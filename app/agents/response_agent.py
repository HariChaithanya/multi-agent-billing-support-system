from typing import Any

from pydantic import BaseModel, Field

from app.agents.common import append_error, append_event
from app.lm import get_llm
from app.state import SupportState

SYSTEM_PROMPT = """You are a billing support assistant drafting the final customer response.
Be clear, professional, and grounded only in the provided context.
Do not invent account details, amounts, or policies.
If information is missing, explain what you can confirm and what the customer should do next."""


class ResponseResult(BaseModel):
    final_response: str
    confidence_score: float = Field(ge=0.0, le=1.0)


async def run(state: SupportState) -> dict[str, Any]:
    query = state.get("customer_query", "").strip()
    if not query:
        return {
            "final_response": "We could not process your request because the message was empty.",
            "confidence_score": 0.0,
            "errors": append_error(state, "response_agent: customer_query is required"),
            "agent_events": append_event(
                state,
                agent="response_agent",
                event_type="validation_error",
                details={"reason": "missing customer_query"},
            ),
        }

    llm = get_llm().with_structured_output(ResponseResult)
    result: ResponseResult = await llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                (
                    f"Case id: {state.get('case_id', '')}\n"
                    f"Customer id: {state.get('customer_id', '')}\n"
                    f"Customer query: {query}\n"
                    f"Intent: {state.get('intent', '')}\n"
                    f"Priority: {state.get('priority', '')}\n"
                    f"Customer profile: {state.get('customer_profile', {})}\n"
                    f"Billing analysis: {state.get('billing_analysis', {})}\n"
                    f"Errors so far: {state.get('errors', [])}"
                ),
            ),
        ]
    )

    confidence = result.confidence_score
    if state.get("confidence_score"):
        confidence = max(confidence, float(state["confidence_score"]))

    return {
        "final_response": result.final_response,
        "confidence_score": confidence,
        "agent_events": append_event(
            state,
            agent="response_agent",
            event_type="generated_response",
            details={"confidence_score": confidence},
        ),
    }
