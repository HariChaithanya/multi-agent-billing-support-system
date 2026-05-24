"""
LangGraph workflow:

    START
      ↓
    IntentAgent
      ↓
    CustomerAgent
      ↓
    BillingAgent
      ↓
    ResponseAgent
      ↓
    END
"""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.billing_agent import run as billing_agent
from app.agents.customer_agent import run as customer_agent
from app.agents.intent_agent import run as intent_agent
from app.agents.response_agent import run as response_agent
from app.state import SupportState

INTENT_AGENT = "IntentAgent"
CUSTOMER_AGENT = "CustomerAgent"
BILLING_AGENT = "BillingAgent"
RESPONSE_AGENT = "ResponseAgent"


def build_graph():
    workflow = StateGraph(SupportState)

    workflow.add_node(INTENT_AGENT, intent_agent)
    workflow.add_node(CUSTOMER_AGENT, customer_agent)
    workflow.add_node(BILLING_AGENT, billing_agent)
    workflow.add_node(RESPONSE_AGENT, response_agent)

    workflow.add_edge(START, INTENT_AGENT)
    workflow.add_edge(INTENT_AGENT, CUSTOMER_AGENT)
    workflow.add_edge(CUSTOMER_AGENT, BILLING_AGENT)
    workflow.add_edge(BILLING_AGENT, RESPONSE_AGENT)
    workflow.add_edge(RESPONSE_AGENT, END)

    return workflow.compile()


support_graph = build_graph()


def create_initial_state(
    *,
    case_id: str,
    customer_id: str,
    customer_query: str,
) -> SupportState:
    return SupportState(
        case_id=case_id,
        customer_id=customer_id,
        customer_query=customer_query,
        intent="",
        customer_profile={},
        billing_analysis={},
        transaction_analysis={},
        policy_decision={},
        fraud_analysis={},
        escalation_decision={},
        final_response="",
        confidence_score=0.0,
        priority="medium",
        retry_count=0,
        agent_events=[],
        errors=[],
    )


async def run_workflow(
    *,
    case_id: str,
    customer_id: str,
    customer_query: str,
) -> dict[str, Any]:
    initial_state = create_initial_state(
        case_id=case_id,
        customer_id=customer_id,
        customer_query=customer_query,
    )
    return await support_graph.ainvoke(initial_state)
