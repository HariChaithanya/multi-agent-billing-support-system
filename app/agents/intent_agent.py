from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agents.common import append_error, append_event
from app.lm import get_llm
from app.state import SupportState

IntentLabel = Literal[
    "billing_inquiry",
    "payment_issue",
    "refund_request",
    "account_question",
    "general_support",
]


class IntentResult(BaseModel):
    intent: IntentLabel
    confidence_score: float = Field(ge=0.0, le=1.0)
    priority: Literal["low", "medium", "high", "urgent"]
    reasoning: str


SYSTEM_PROMPT = """You classify customer billing support messages.
Return the best intent, a confidence score between 0 and 1, a priority, and brief reasoning."""


async def run(state: SupportState) -> dict[str, Any]:
    query = state.get("customer_query", "").strip()
    if not query:
        return {
            "intent": "general_support",
            "confidence_score": 0.0,
            "priority": "low",
            "errors": append_error(state, "intent_agent: customer_query is required"),
            "agent_events": append_event(
                state,
                agent="intent_agent",
                event_type="validation_error",
                details={"reason": "missing customer_query"},
            ),
        }

    llm = get_llm().with_structured_output(IntentResult)
    result: IntentResult = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                f"Customer query:\n{query}\n\nCustomer id: {state.get('customer_id', '')}",
            ),
        ]
    )

    return {
        "intent": result.intent,
        "confidence_score": result.confidence_score,
        "priority": result.priority,
        "agent_events": append_event(
            state,
            agent="intent_agent",
            event_type="classified_intent",
            details={
                "intent": result.intent,
                "confidence_score": result.confidence_score,
                "priority": result.priority,
                "reasoning": result.reasoning,
            },
        ),
    }
