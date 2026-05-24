from typing import Any

from app.agents.common import append_error, append_event
from app.database import async_session_factory
from app.state import SupportState
from app.tools.customer_tool import fetch_customer_profile


async def run(state: SupportState) -> dict[str, Any]:
    customer_id = state.get("customer_id", "").strip()
    if not customer_id:
        return {
            "customer_profile": {"found": False},
            "errors": append_error(state, "customer_agent: customer_id is required"),
            "agent_events": append_event(
                state,
                agent="customer_agent",
                event_type="validation_error",
                details={"reason": "missing customer_id"},
            ),
        }

    async with async_session_factory() as session:
        profile = await fetch_customer_profile(session, customer_id)

    updates: dict[str, Any] = {
        "customer_profile": profile,
        "agent_events": append_event(
            state,
            agent="customer_agent",
            event_type="loaded_profile",
            details={"found": profile.get("found", False)},
        ),
    }

    if not profile.get("found"):
        updates["errors"] = append_error(
            state, f"customer_agent: customer not found for id {customer_id}"
        )

    return updates
