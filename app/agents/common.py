from typing import Any

from app.state import SupportState


def append_event(
    state: SupportState,
    *,
    agent: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    events = list(state.get("agent_events") or [])
    events.append(
        {
            "agent": agent,
            "event_type": event_type,
            "details": details or {},
        }
    )
    return events


def append_error(state: SupportState, message: str) -> list[str]:
    errors = list(state.get("errors") or [])
    errors.append(message)
    return errors
