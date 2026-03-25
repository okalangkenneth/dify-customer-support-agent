# LLM Hallucination Mitigation — Technical Approach

*This document explains the hallucination mitigation pattern used in this project,
written for a technical audience. Suitable for use in proposals or portfolio discussions.*

---

## The Problem

Large language models generate fluent, confident text — even when they're wrong.
In customer support, this is a high-stakes failure:

- A model invents a refund policy that doesn't exist → customer expects it → dispute
- A model misremembers a pricing tier → customer purchases the wrong plan
- A model conflates two similar products → incorrect technical guidance

Standard RAG (Retrieval-Augmented Generation) helps by grounding the model in
retrieved documents. But RAG alone doesn't prevent hallucination — a model can
retrieve the right document and still fabricate a detail when generating its answer.

---

## The Solution: Post-Hoc Grounding Validation

Instead of only controlling the *input* (what context the model sees), this project
also validates the *output* (whether the answer actually uses that context).

The pipeline has two LLM calls:

### Call 1 — Support Agent (draft)
```
System: Answer based only on the retrieved context. Cite sources.
Context: [top-5 knowledge base chunks]
User: [customer question]

→ Output: draft answer (may contain hallucinations)
```

### Call 2 — Hallucination Validator (verify)
```
System: You are a hallucination detection system.
        Does the draft answer contain claims NOT in the retrieved context?
        Respond ONLY with JSON.

Input:  RETRIEVED CONTEXT: [same chunks]
        DRAFT ANSWER: [output from Call 1]

→ Output: {
    "grounded": true/false,
    "confidence": 0.0–1.0,
    "unsupported_claims": ["list of fabricated claims"],
    "safe_answer": "grounded rewrite if hallucination detected"
  }
```

### Enforcement (code node — no LLM)
```python
if grounded:
    return draft_answer      # validator approved it
else:
    return safe_answer        # validator's conservative rewrite
```

---

## Why a Second LLM Call Works

The validator runs at **temperature=0** with a narrow, structured task.
It cannot invent claims — it can only compare two pieces of text and report differences.
This asymmetry is key: generation is hard to constrain, but comparison is easy.

Using the same model family (Claude Haiku for both) keeps costs low.
The total latency overhead is ~1–2 seconds per query.

---

## Tradeoffs and Limitations

| Tradeoff | Notes |
|----------|-------|
| False positives | Validator occasionally flags correct answers as ungrounded (seen in testing). The safe_answer fallback still returns correct information, so the user is never harmed — just routed through the fallback path. |
| Cost | Two LLM calls per query instead of one. At Haiku pricing (~$0.25/1M input tokens) this is negligible for support volumes. |
| Latency | +1–2s per query for the validation call. Acceptable for support; not for real-time chat. |
| KB quality | Validation is only as good as the retrieved context. If the KB doesn't contain the answer, the validator will correctly output grounded=false and route to a "contact support" response. |

---

## Production Extensions

This pattern scales to production with these additions:

- **Confidence threshold routing**: if `confidence < 0.5`, auto-escalate to human
- **Claim logging**: store `unsupported_claims` per query → feed back to KB team as coverage gaps
- **A/B testing**: run validator on a sample (e.g., 20%) and compare hallucination rates
- **Streaming**: run validator async while streaming the draft → replace if needed before user reads it
- **Fine-tuning signal**: false positives from the validator → training data for a smaller dedicated classifier

---

## Summary

The pattern demonstrated here — **generate, then verify** — is a practical,
low-overhead solution to LLM hallucination that requires no model fine-tuning,
no custom infrastructure, and no changes to the underlying LLM.

It works today, with off-the-shelf models, and it fails safe:
if something goes wrong at any step, the user gets a conservative answer
or a handoff to a human — never a confident fabrication.
