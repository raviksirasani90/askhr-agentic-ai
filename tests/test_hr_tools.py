
import pytest

from src.hr_tools import (
    AUDIT_LOG,
    LEAVE_REQUESTS,
    decide_leave_request,
    get_audit_log,
    get_leave_balance,
    get_leave_request,
    submit_leave_request,
)


@pytest.fixture(autouse=True)
def reset_demo_state():
    """Keep tests isolated from each other's in-memory records."""
    LEAVE_REQUESTS.clear()
    AUDIT_LOG.clear()


def test_get_leave_balance_for_demo_employee():
    result = get_leave_balance("EMP001")

    assert result["success"] is True
    assert result["leave_balance"] == 18
    assert result["demo"] is True


def test_unknown_employee_is_rejected():
    result = get_leave_balance("UNKNOWN")

    assert result["success"] is False


def test_leave_request_requires_confirmation():
    result = submit_leave_request("EMP001", 3, "Personal leave")

    assert result["success"] is False
    assert result["requires_confirmation"] is True


def test_confirmed_leave_request_requires_manager_approval():
    result = submit_leave_request(
        "EMP001", 3, "Personal leave", confirmed=True
    )

    assert result["success"] is True
    assert result["status"] == "PENDING_MANAGER_APPROVAL"
    assert result["demo"] is True
    assert result["request_id"].startswith("LR-")


def test_leave_request_rejects_excessive_days():
    result = submit_leave_request(
        "EMP001", 31, "Personal leave", confirmed=True
    )

    assert result["success"] is False


def test_manager_can_approve_pending_request():
    submitted = submit_leave_request(
        "EMP001", 3, "Personal leave", confirmed=True
    )

    result = decide_leave_request(
        submitted["request_id"],
        manager_id="MGR001",
        approved=True,
        comments="Approved for the requested dates.",
    )

    assert result["success"] is True
    assert result["request"]["status"] == "APPROVED"
    assert result["request"]["manager_id"] == "MGR001"


def test_manager_can_reject_pending_request():
    submitted = submit_leave_request(
        "EMP001", 2, "Personal leave", confirmed=True
    )

    result = decide_leave_request(
        submitted["request_id"],
        manager_id="MGR001",
        approved=False,
        comments="Insufficient team coverage.",
    )

    assert result["success"] is True
    assert result["request"]["status"] == "REJECTED"


def test_unauthorized_manager_cannot_decide_request():
    submitted = submit_leave_request(
        "EMP001", 2, "Personal leave", confirmed=True
    )

    result = decide_leave_request(
        submitted["request_id"],
        manager_id="MGR999",
        approved=True,
    )

    assert result["success"] is False
    assert get_leave_request(submitted["request_id"])["request"]["status"] == (
        "PENDING_MANAGER_APPROVAL"
    )


def test_request_cannot_be_decided_twice():
    submitted = submit_leave_request(
        "EMP001", 2, "Personal leave", confirmed=True
    )

    first = decide_leave_request(
        submitted["request_id"], "MGR001", True
    )
    second = decide_leave_request(
        submitted["request_id"], "MGR001", False
    )

    assert first["success"] is True
    assert second["success"] is False


def test_submission_and_decision_are_audited():
    submitted = submit_leave_request(
        "EMP001", 2, "Personal leave", confirmed=True
    )

    decide_leave_request(
        submitted["request_id"], "MGR001", True
    )

    events = get_audit_log()

    assert [event["event_type"] for event in events] == [
        "LEAVE_REQUEST_SUBMITTED",
        "LEAVE_REQUEST_DECIDED",
    ]
    assert all(event["timestamp"] for event in events)


def test_unknown_request_cannot_be_decided():
    result = decide_leave_request(
        "LR-DOESNOTEXIST", "MGR001", True
    )

    assert result["success"] is False


def test_invalid_decision_type_is_rejected():
    submitted = submit_leave_request(
        "EMP001", 2, "Personal leave", confirmed=True
    )

    result = decide_leave_request(
        submitted["request_id"], "MGR001", "yes"
    )

    assert result["success"] is False
    assert get_leave_request(submitted["request_id"])["request"]["status"] == (
        "PENDING_MANAGER_APPROVAL"
    )
