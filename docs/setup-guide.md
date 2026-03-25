# Setup Guide — Customer Support Agent

## Prerequisites

- Docker Desktop running (green engine)
- Dify at `http://localhost` (reusing `C:\Projects\dify-etsy-toolkit\dify\docker`)
- Anthropic plugin installed in Dify

---

## Step 1 — Upload the Knowledge Base

1. Open `http://localhost` → **Knowledge** (left sidebar) → **Create Knowledge**
2. Name it: `SupportDesk Pro Docs`
3. Upload these three files (one at a time):
   - `knowledge-base/faq.md`
   - `knowledge-base/return-policy.md`
   - `knowledge-base/product-catalog.md`
4. Indexing settings: **High Quality**, **Automatic** segmentation
5. Wait for indexing to complete (green checkmark on each doc)

---

## Step 2 — Import the Workflow

1. Open `http://localhost` → **Studio** → **Create App** → **Import DSL file**
2. Upload `dify-workflows/customer-support-agent.yml`
3. The workflow opens with 6 nodes visible

---

## Step 3 — Connect the Knowledge Base to the Workflow

This step cannot be done in the DSL file — it must be done in the UI:

1. Click the **Search Knowledge Base** node
2. In the right panel, click **Add** under "Knowledge Base"
3. Select **SupportDesk Pro Docs**
4. Set: Top K = 5, Score threshold = OFF
5. Click **Save**

---

## Step 4 — Publish and Test

1. Click **Publish** (top right)
2. Click **Run** to open the test panel
3. Try these test questions:

**Should return grounded answer:**
> "How do I reset my password?"

**Should trigger safe fallback (hallucination test):**
> "Can I get a refund after 60 days if I'm unhappy?" 
> _(policy only covers 14 days — watch grounded=false fire)_

**Should escalate:**
> "I want to sue you for losing my data"

4. Check the outputs panel — you should see:
   - `final_answer` — the safe, verified response
   - `grounded` — `true` or `false`
   - `unsupported_claims` — any claims the validator rejected
   - `confidence` — validator confidence score

---

## Step 5 — Note the Workflow API Key

1. In Studio, click **API Access** on the published workflow
2. Copy the API key
3. Add it to `dify-etsy-toolkit/dify/docker/.env`:
   ```
   SUPPORT_AGENT_WORKFLOW_KEY=app-xxxxxxxxxxxxxxxx
   ```

This key is used by the Flask API route in Phase 3.
