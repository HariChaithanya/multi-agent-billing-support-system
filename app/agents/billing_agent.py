from typing import Any

from pydantic import BaseModel, Field

from app.agents.common import append_error, append_event
from app.database import async_session_factory
from app.lm import get_llm
from app.state import SupportState
from app.tools.billing_tool import fetch_billing_analysis

BILLING_INTENTS = {
    "billing_inquiry",
    "payment_issue",
    "refund_request",
}


class BillingAnalysisResult(BaseModel):
    summary: str
    key_findings: list[str]
    recommended_action: str
    confidence_score: float = Field(ge=0.0, le=1.0)


SYSTEM_PROMPT = """You are a billing analyst for a customer support system.
Use the customer query, intent, profile, and billing data to produce a concise analysis.
If billing data is missing, say so clearly and keep recommendations conservative."""


async def run(state: SupportState) -> dict[str, Any]:
    customer_id = state.get("customer_id", "").strip()
    intent = state.get("intent", "general_support")

    async with async_session_factory() as session:
        billing_data = await fetch_billing_analysis(session, customer_id)

    if intent not in BILLING_INTENTS:
        analysis = {
            "skipped_llm": True,
            "reason": "intent does not require detailed billing analysis",
            "intent": intent,
            "billing_data": billing_data,
        }
        return {
            "billing_analysis": analysis,
            "agent_events": append_event(
                state,
                agent="billing_agent",
                event_type="skipped_analysis",
                details={"intent": intent},
            ),
        }

    if not billing_data.get("found"):
        return {
            "billing_analysis": {
                "skipped_llm": True,
                "reason": "no billing records found",
                "billing_data": billing_data,
            },
            "errors": append_error(
                state, f"billing_agent: no billing data for customer {customer_id}"
            ),
            "agent_events": append_event(
                state,
                agent="billing_agent",
                event_type="missing_billing_data",
                details={"customer_id": customer_id},
            ),
        }

    llm = get_llm().with_structured_output(BillingAnalysisResult)
    result: BillingAnalysisResult = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                (
                    f"Customer query: {state.get('customer_query', '')}\n"
                    f"Intent: {intent}\n"
                    f"Customer profile: {state.get('customer_profile', {})}\n"
                    f"Billing data: {billing_data}"
                ),
            ),
        ]
    )

    analysis = {
        "summary": result.summary,
        "key_findings": result.key_findings,
        "recommended_action": result.recommended_action,
        "confidence_score": result.confidence_score,
        "billing_data": billing_data,
    }

    return {
        "billing_analysis": analysis,
        "confidence_score": result.confidence_score,
        "agent_events": append_event(
            state,
            agent="billing_agent",
            event_type="completed_analysis",
            details={
                "recommended_action": result.recommended_action,
                "confidence_score": result.confidence_score,
            },
        ),
    }
