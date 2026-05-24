from typing import TypedDict


class SupportState(TypedDict):
    case_id: str
    customer_id: str
    customer_query: str

    intent: str

    customer_profile: dict

    billing_analysis: dict

    transaction_analysis: dict

    policy_decision: dict

    fraud_analysis: dict

    escalation_decision: dict

    final_response: str

    confidence_score: float

    priority: str

    retry_count: int

    agent_events: list

    errors: list
