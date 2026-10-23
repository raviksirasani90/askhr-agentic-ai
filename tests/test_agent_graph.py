from src import agent_graph


def test_graph_routes_leave_balance_to_hr_tool():
    result = agent_graph.askhr_graph.invoke({
        "question": "What is my leave balance?",
        "employee_id": "EMP001",
    })

    assert result["intent"] == "leave_balance"
    assert "18 days" in result["answer"]


def test_graph_routes_policy_question_to_knowledge(monkeypatch):
    def fake_answer_policy_question(question):
        return {
            "answer": "Test policy answer",
            "sources": ["test_policy.txt"],
        }

    monkeypatch.setattr(
        agent_graph,
        "answer_policy_question",
        fake_answer_policy_question,
    )

    result = agent_graph.askhr_graph.invoke({
        "question": "What is the parental leave policy?",
        "employee_id": "EMP001",
    })

    assert result["intent"] == "knowledge"
    assert result["answer"] == "Test policy answer"
    assert result["sources"] == ["test_policy.txt"]
