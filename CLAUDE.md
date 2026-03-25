# Project Rules - dify-customer-support-agent

## What we are building

A **Customer Support Agent** built on Dify's Agent node. The agent answers user
support questions by searching a knowledge base (RAG), calling tools when needed,
and running every answer through a hallucination validator before returning it.

Portfolio goal: demonstrate RAG, tool calling, and hallucination mitigation in one
cohesive project — targeting the Upwork job "LLM Hallucination Mitigation - SaaS
Analytics Platform" ($35-75/hr).

**GitHub**: https://github.com/okalangkenneth/dify-customer-support-agent

---

## Architecture

```
User Question
      ↓
 [Agent Node]
   tools: search_knowledge_base | check_order_status | escalate_to_human
      ↓
 Agent Draft Answer + Retrieved Context
      ↓
 [Hallucination Validator LLM]
   "Does the answer contain claims not in the retrieved docs?"
      ↓
 [Code Node]  ← replaces answer if grounded: false
      ↓
 Final Verified Answer
```

The validator is the key portfolio differentiator: it outputs JSON
`{grounded: bool, unsupported_claims: [], safe_answer: string}`
and the Code node enforces it.

---

## Build Progress (Claude Code: update every session)

### COMPLETED
- Project scaffold created (CLAUDE.md, dirs, .gitignore)
- Knowledge base documents written (faq.md, return-policy.md, product-catalog.md)
- Dify workflow DSL written (customer-support-agent.yml) — 380 lines, 6 nodes
  - Start → KB Search (RAG) → Support Agent LLM → Hallucination Validator LLM
    → Grounding Enforcer (Code) → End
  - Validator outputs JSON: {grounded, confidence, unsupported_claims, safe_answer}
  - Code node enforces: swaps in safe_answer if grounded==false
- docs/setup-guide.md written (step-by-step import + test instructions)
- Phase 3: support_agent.py Flask API route written and mounted via override
- Phase 3: docker-compose.override.yml updated (etsy + support agent combined)
- Phase 3: support-agent-demo.html built and served at localhost/support-agent.html
- Phase 3: Full end-to-end test passed — pipeline live, validator firing correctly

### IN PROGRESS
- [ ] Git init + push to GitHub

### REMAINING
- [ ] Record Loom demo (2 min walkthrough)

### COMPLETED (Phase 4)
- README.md written — architecture diagram, examples, setup guide, stack table
- docs/hallucination-mitigation.md written — Upwork portfolio explainer
- [ ] Upload knowledge base docs to Dify UI
- [ ] Import workflow DSL into Dify
- [ ] Write API route (support_agent.py)
- [ ] Mount API route via docker-compose.override.yml
- [ ] Build demo HTML (support-agent-demo.html)
- [ ] Test end-to-end
- [ ] Write README with architecture diagram
- [ ] Write hallucination-mitigation.md (portfolio explainer)
- [ ] Record Loom demo

---

## Tech Stack

- Backend: Python 3.12 + Flask (Dify API service, same Docker instance as etsy-toolkit)
- Frontend: Vanilla HTML served via nginx
- Container: Reuses C:\Projects\dify-etsy-toolkit\dify\docker (DO NOT start new Docker)
- Workflow: Dify DSL in dify-workflows/
- Knowledge Base: Markdown docs uploaded via Dify UI

---

## Business Rules (NON-NEGOTIABLE)

- Agent MUST cite source document for every factual claim
- Hallucination validator runs on EVERY response — never skip it
- If validator says grounded: false → return safe_answer, never the raw agent answer
- Escalate to human if: confidence < 0.5, question contains "lawsuit"/"legal"/"refund dispute"
- Never fabricate order IDs, prices, or policy details

---

## Session End Prompt

Update the Build Progress section in CLAUDE.md with completed work, then stop.
