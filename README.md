# Customer Support Agent

> A production-grade customer support agent built on [Dify](https://github.com/langgenius/dify) (90k ⭐)
> featuring **RAG (Retrieval-Augmented Generation)**, **tool calling**, and a
> **hallucination validation pipeline** that verifies every answer against source
> documents before returning it to the user.

<img width="749" height="920" alt="image" src="https://github.com/user-attachments/assets/24e877c8-b3a4-4c1f-b0cc-5665f04eca33" />



## Live Demo

[Demo](https://www.loom.com/share/54d272fd6e8e485ca1edea5d0200e397) 


Ask a question → the agent searches a knowledge base, drafts an answer, validates it
for hallucinations, and returns a verified response with a grounding score.

**Example — clean grounded response:**
```
Q: How do I reset my password?

A: Go to app.supportdeskpro.com/login → click "Forgot password" → enter your email.
   A reset link is sent within 2 minutes. Links expire after 24 hours.

grounded: true  |  confidence: 95%  |  unsupported_claims: none
```

**Example — hallucination caught and corrected:**
```
Q: Can I get a refund after 60 days?

[Support Agent draft]: Makes up a "60-day grace period" not in any document
[Hallucination Validator]: grounded: false — "60-day grace period" not in context
[Grounding Enforcer]: Replaces draft with safe_answer from validator

A: Our standard refund window is 14 days. Annual plans have a 30-day window.
   For situations outside these windows, contact support@supportdeskpro.com.

grounded: false  |  confidence: 12%  |  unsupported_claims: "60-day grace period"
```

**Example, automatic escalation:**
```
Q: I want to sue you for losing my data

A: This requires human review. Please email support@supportdeskpro.com.
```

---

## Why I built this

LLM hallucination is the #1 blocker for enterprise AI adoption. Most demos skip the
hard part: *what happens when the model makes something up?*

This project shows a concrete, production-ready answer:

1. **Ground answers in documents** (RAG, not just vibes)
2. **Validate every response** before it reaches the user (post-hoc grounding check)
3. **Fail safe**, if validation fails, return a conservative verified answer, never the hallucinated one

The validator runs as a second LLM call at `temperature=0`, forced to output structured
JSON: `{grounded, confidence, unsupported_claims, safe_answer}`. A Python code node
then enforces the decision — no way for a hallucination to slip through.

---

## Architecture

```
User Question
      │
      ▼
┌─────────────────────┐
│   Search Knowledge  │  ← RAG: semantic search across 3 support docs
│       Base          │    Top-5 chunks retrieved per query
└──────────┬──────────┘
           │ retrieved context
           ▼
┌─────────────────────┐
│   Support Agent     │  ← Claude Haiku, temp=0.3
│       LLM           │    Grounded in context, escalation rules baked in
└──────────┬──────────┘
           │ draft answer
           ▼
┌─────────────────────┐
│  Hallucination      │  ← Claude Haiku, temp=0  ← KEY COMPONENT
│    Validator LLM    │    Outputs JSON:
└──────────┬──────────┘    {grounded, confidence,
           │                unsupported_claims, safe_answer}
           ▼
┌─────────────────────┐
│  Grounding Enforcer │  ← Python code node
│    (Code Node)      │    if grounded==false → use safe_answer
└──────────┬──────────┘    else → use original draft
           │
           ▼
    Verified Answer
   {answer, grounded,
    confidence, claims}
```

### Stack

| Layer | Technology |
|-------|-----------|
| Workflow engine | [Dify](https://github.com/langgenius/dify) 1.13.2 |
| LLM | Claude Haiku (via Anthropic plugin) |
| Vector search | Weaviate (bundled with Dify Docker) |
| API layer | Python 3.12 + Flask (Dify internal) |
| Frontend demo | Vanilla HTML + nginx |
| Infrastructure | Docker Compose (11 containers) |

---

## Knowledge Base

Three documents covering a fictional SaaS product (SupportDesk Pro):

| Document | Content |
|----------|---------|
| `faq.md` | Account, billing, features, security Q&A |
| `return-policy.md` | Refund windows, eligibility, process |
| `product-catalog.md` | Plans, pricing, feature comparison table |

These docs are uploaded to Dify's Knowledge Base and indexed with Weaviate.
The retrieval uses semantic search — not keyword matching.

---

## Hallucination Mitigation.  How It Works

The validator prompt is the heart of the project:

```
You are a hallucination detection system. Verify whether an AI-generated
answer is fully supported by retrieved source documents.

Respond ONLY with valid JSON:
{
  "grounded": true or false,
  "confidence": 0.0 to 1.0,
  "unsupported_claims": ["each claim not found in context"],
  "safe_answer": "verbatim draft if grounded; conservative rewrite if not"
}

Rules:
- grounded is true ONLY when every factual claim is explicitly in the context
- Prices, dates, limits, and policy details are high-risk — require explicit support
- safe_answer must never introduce facts not in the retrieved context
```

The Python **Grounding Enforcer** node then makes the final decision:

```python
if grounded:
    final = draft_answer          # validator approved it
else:
    final = safe_answer           # validator's conservative rewrite
    # fallback if safe_answer is too short:
    final = "I don't have enough verified information..."
```

This means the validator doesn't just *flag* hallucinations  it also *fixes* them
by writing a grounded alternative. The user always gets a useful response.

---

## Project Structure

```
dify-customer-support-agent/
  README.md
  CLAUDE.md                         # build log + rules
  .gitignore
  knowledge-base/
    faq.md                          # uploaded to Dify Knowledge Base
    return-policy.md
    product-catalog.md
  dify-workflows/
    customer-support-agent.yml      # full workflow DSL (import into Dify)
  api/controllers/console/
    support_agent.py                # Flask API route
    __init__.py                     # updated with support_agent import
  demo/
    support-agent-demo.html         # standalone UI (served via nginx)
  docs/
    setup-guide.md                  # step-by-step setup instructions
    hallucination-mitigation.md     # technical explainer
```

---

## Setup

### Prerequisites
- Docker Desktop (green engine, 8GB RAM allocated)
- Dify running at `http://localhost` (see [dify-etsy-toolkit](https://github.com/okalangkenneth/dify-etsy-toolkit) for Docker setup)
- Anthropic plugin installed in Dify

### 1. Upload the Knowledge Base
Open `http://localhost` → **Knowledge** → **Create Knowledge**
- Name: `SupportDesk Pro Docs`
- Upload `knowledge-base/faq.md`, `return-policy.md`, `product-catalog.md`
- Indexing: High Quality, Automatic segmentation

### 2. Import the Workflow
**Studio** → **Create App** → **Import DSL file** → select `dify-workflows/customer-support-agent.yml`

Then click the **Search Knowledge Base** node → **Add** → select `SupportDesk Pro Docs` → Save.

Click **Publish**.

### 3. Mount the API Route

Add to `dify/docker/docker-compose.override.yml` under `services.api.volumes`:
```yaml
- /path/to/dify-customer-support-agent/api/controllers/console/support_agent.py:/app/api/controllers/console/support_agent.py:ro
- /path/to/dify-customer-support-agent/api/controllers/console/__init__.py:/app/api/controllers/console/__init__.py:ro
```

Add to `dify/docker/.env`:
```
SUPPORT_AGENT_WORKFLOW_KEY=app-your-key-here
```

Get the key from: Dify Studio → Customer Support Agent → **API Access**.

Then recreate the API container:
```bash
cd dify/docker
docker compose up -d --no-deps --force-recreate api
```

### 4. Serve the Demo UI
```bash
docker cp demo/support-agent-demo.html docker-nginx-1:/usr/share/nginx/html/support-agent.html
```

Add nginx location block (inside the container):
```bash
docker exec docker-nginx-1 sed -i 's|location / {|location /support-agent.html {\n      root /usr/share/nginx/html;\n    }\n\n    location / {|' /etc/nginx/conf.d/default.conf
docker exec docker-nginx-1 nginx -s reload
```

Open `http://localhost/support-agent.html`.

---

## Related Projects

- **[dify-etsy-toolkit](https://github.com/okalangkenneth/dify-etsy-toolkit)** — Dify workflow that generates SEO-optimized Etsy listings. The Docker setup this project runs on.

---

## Author

Kenneth Okalang — [GitHub](https://github.com/okalangkenneth)
