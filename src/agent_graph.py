from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END

from src.hr_tools import get_leave_balance
from src.knowledge import answer_policy_question


class AskHRState(TypedDict, total=False):
    question: str
    employee_id: str
    intent: str
    answer: str
    sources: list[str]


def route_intent(state: AskHRState) -> dict:
    """Route recognized leave-balance requests to the HR tool."""
    question = state["question"].lower()

    balance_terms = (
        "leave balance",
        "balance of my leave",
        "how much leave",
        "remaining leave",
        "available leave balance",
    )

    if any(term in question for term in balance_terms):
        return {"intent": "leave_balance"}

    return {"intent": "knowledge"}


def leave_balance_node(state: AskHRState) -> dict:
    """Read synthetic demo data for the configured employee."""
    result = get_leave_balance(state.get("employee_id", "EMP001"))

    if not result["success"]:
        return {
            "answer": result["message"],
            "sources": [],
        }

    return {
        "answer": (
            f"Demo employee: {result['employee_name']} "
            f"({result['employee_id']}). "
            f"Available leave balance: {result['leave_balance']} days. "
            "This is synthetic demo data, not a live HR record."
        ),
        "sources": ["Synthetic demo employee record"],
    }


def knowledge_node(state: AskHRState) -> dict:
    """Run the existing retrieval-augmented generation pipeline."""
    result = answer_policy_question(state["question"])
    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }


def select_node(
    state: AskHRState,
) -> Literal["leave_balance", "knowledge"]:
    if state.get("intent") == "leave_balance":
        return "leave_balance"
    return "knowledge"


def build_graph():
    graph = StateGraph(AskHRState)

    graph.add_node("router", route_intent)
    graph.add_node("leave_balance", leave_balance_node)
    graph.add_node("knowledge", knowledge_node)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        select_node,
        {
            "leave_balance": "leave_balance",
            "knowledge": "knowledge",
        },
    )
    graph.add_edge("leave_balance", END)
    graph.add_edge("knowledge", END)

    return graph.compile()


askhr_graph = build_graph()
