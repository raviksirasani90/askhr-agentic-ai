DEMO_EMPLOYEES = {
    "EMP001": {
        "name": "Alex Morgan",
        "leave_balance": 18,
    },
    "EMP002": {
        "name": "Jamie Taylor",
        "leave_balance": 12,
    },
}


def get_leave_balance(employee_id: str) -> dict:
    """Return a synthetic employee's leave balance."""
    employee = DEMO_EMPLOYEES.get(employee_id)

    if employee is None:
        return {
            "success": False,
            "message": "Employee record not found.",
        }

    return {
        "success": True,
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "leave_balance": employee["leave_balance"],
        "unit": "days",
        "demo": True,
    }


def submit_leave_request(
    employee_id: str,
    days: int,
    reason: str,
    confirmed: bool = False,
) -> dict:
    """Create a demo leave request after explicit confirmation."""
    if employee_id not in DEMO_EMPLOYEES:
        return {"success": False, "message": "Employee record not found."}

    if not isinstance(days, int) or isinstance(days, bool) or days < 1 or days > 30:
        return {
            "success": False,
            "message": "Leave duration must be a whole number between 1 and 30 days.",
        }

    if not reason.strip():
        return {"success": False, "message": "A reason is required."}

    if not confirmed:
        return {
            "success": False,
            "requires_confirmation": True,
            "message": "Explicit employee confirmation is required before submission.",
        }

    balance = DEMO_EMPLOYEES[employee_id]["leave_balance"]

    if days > balance:
        return {
            "success": False,
            "message": f"Insufficient leave balance. Available: {balance} days.",
        }

    # This demo creates no real HR transaction.
    return {
        "success": True,
        "status": "PENDING_MANAGER_APPROVAL",
        "employee_id": employee_id,
        "days_requested": days,
        "message": "Demo request created. Manager approval is still required.",
        "demo": True,
    }
