from src.hr_tools import get_leave_balance, submit_leave_request


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


def test_leave_request_rejects_excessive_days():
    result = submit_leave_request(
        "EMP001", 31, "Personal leave", confirmed=True
    )

    assert result["success"] is False
