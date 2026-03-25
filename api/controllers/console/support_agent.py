import logging
import os

import requests
from flask import request
from flask_restx import Resource
from pydantic import BaseModel, Field

from controllers.console import console_ns
from controllers.console.wraps import account_initialization_required, setup_required
from libs.login import login_required

logger = logging.getLogger(__name__)

DIFY_API_BASE = os.environ.get("DIFY_INNER_API_URL", "http://api:5001")
SUPPORT_AGENT_KEY = os.environ.get("SUPPORT_AGENT_WORKFLOW_KEY", "")


class SupportAgentPayload(BaseModel):
    user_question: str = Field(..., min_length=3, max_length=1000)


@console_ns.route("/support-agent/ask")
class SupportAgentApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        """Run a customer support question through the RAG + hallucination-validated agent."""
        try:
            payload = SupportAgentPayload.model_validate(request.json or {})
        except Exception as e:
            return {"message": f"Invalid input: {e}"}, 400

        if not SUPPORT_AGENT_KEY:
            logger.error("SUPPORT_AGENT_WORKFLOW_KEY is not set")
            return {"message": "Support Agent is not configured on this server."}, 503

        try:
            resp = requests.post(
                f"{DIFY_API_BASE}/v1/workflows/run",
                headers={
                    "Authorization": f"Bearer {SUPPORT_AGENT_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": {"user_question": payload.user_question},
                    "response_mode": "blocking",
                    "user": "support-agent",
                },
                timeout=90,
            )
            resp.raise_for_status()
        except requests.Timeout:
            logger.error("Support agent workflow timed out")
            return {"message": "The agent timed out. Please try again."}, 504
        except requests.RequestException as e:
            logger.error(f"Support agent workflow request failed: {e}")
            return {"message": "Failed to reach the workflow engine."}, 502

        data = resp.json()
        outputs = data.get("data", {}).get("outputs", {})

        if not outputs:
            logger.error(f"Unexpected workflow response: {data}")
            return {"message": "Workflow returned no output."}, 500

        grounded = outputs.get("grounded", "false").lower() == "true"

        return {
            "answer": outputs.get("final_answer", ""),
            "grounded": grounded,
            "confidence": outputs.get("confidence", "0.0"),
            "unsupported_claims": outputs.get("unsupported_claims", "none"),
        }, 200
