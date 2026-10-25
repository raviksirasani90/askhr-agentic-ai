
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from src.database import (
    add_audit_event,
    decide_leave_request_transaction,
    get_leave_request_record,
    initialize_database,
    list_audit_events,
    list_leave_requests,
    save_leave_request,
)


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

# Demo-only manager allowlist; not production authentication.
AUTHORIZED_MANAGERS = {"MGR001"}

# Initialize tables when the HR module is loaded.
initialize_database()


def _record_audit_event(event_type: str, details: dict) -> None:
    """Persist a timestamped audit event."""
    event = {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **deepcopy(details),
    }
    add_audit_event(event)


def get_audit_log() -> list:
    """Return persisted audit events."""
    return list_audit_events()


def get_leave_request(request_id: str) -> dict:
    """Retrieve a leave request from SQLite."""
    request = get_leave_request_record(request_id)

    if request is None:
        return {
            "success": False,
            "message": "Leave request not found.",
        }

    request["demo"] = bool(request["demo"])
    return {
        "success": True,
        "request": deepcopy(request),
    }


def get_leave_requests(employee_id: str | None = None) -> list:
    """List persisted requests, optionally for one employee."""
    requests = list_leave_requests(employee_id)
    for request in requests:
        request["demo"] = bool(request["demo"])
    return requests


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
    """Create a persistent demo request after employee confirmation."""
    if employee_id not in DEMO_EMPLOYEES:
        return {
            "success": False,
            "message": "Employee record not found.",
        }

    if (
        not isinstance(days, int)
        or isinstance(days, bool)
        or days < 1
        or days > 30
    ):
        return {
            "success": False,
            "message": (
                "Leave duration must be a whole number "
                "between 1 and 30 days."
            ),
        }

    if not isinstance(reason, str) or not reason.strip():
        return {
            "success": False,
            "message": "A valid reason is required.",
        }

    if confirmed is not True:
        return {
            "success": False,
            "requires_confirmation": True,
            "message": (
                "Explicit employee confirmation is required "
                "before submission."
            ),
        }

    balance = DEMO_EMPLOYEES[employee_id]["leave_balance"]

    if days > balance:
        return {
            "success": False,
            "message": f"Insufficient leave balance. Available: {balance} days.",
        }

    request = {
        "request_id": f"LR-{uuid4().hex[:10].upper()}",
        "employee_id": employee_id,
        "days_requested": days,
        "reason": reason.strip(),
        "status": "PENDING_MANAGER_APPROVAL",
        "manager_id": None,
        "manager_comments": None,
        "demo": True,
    }

    save_leave_request(request)

    _record_audit_event(
        "LEAVE_REQUEST_SUBMITTED",
        {
            "request_id": request["request_id"],
            "employee_id": employee_id,
            "days_requested": days,
            "status": request["status"],
        },
    )

    return {
        "success": True,
        **deepcopy(request),
        "message": "Demo request created. Manager approval is still required.",
    }



def decide_leave_request(
    request_id: str,
    manager_id: str,
    approved: bool,
    comments: str = "",
) -> dict:
    """Decide a pending request and persist its audit event atomically."""
    if manager_id not in AUTHORIZED_MANAGERS:
        _record_audit_event(
            "UNAUTHORIZED_MANAGER_ATTEMPT",
            {
                "request_id": request_id,
                "manager_id": manager_id,
            },
        )
        return {
            "success": False,
            "message": "Manager is not authorized to decide leave requests.",
        }

    if not isinstance(approved, bool):
        return {
            "success": False,
            "message": "Decision must be explicitly True or False.",
        }

    if not isinstance(comments, str):
        return {
            "success": False,
            "message": "Manager comments must be text.",
        }

    new_status = "APPROVED" if approved else "REJECTED"
    clean_comments = comments.strip()

    audit_event = {
        "event_id": str(uuid4()),
        "event_type": "LEAVE_REQUEST_DECIDED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "manager_id": manager_id,
        "decision": new_status,
        "comments": clean_comments,
    }

    result = decide_leave_request_transaction(
        request_id=request_id,
        manager_id=manager_id,
        new_status=new_status,
        comments=clean_comments,
        audit_event=audit_event,
    )

    if not result["success"]:
        return result

    request = result["request"]
    request["demo"] = bool(request["demo"])

    return {
        "success": True,
        "request": deepcopy(request),
        "message": f"Leave request {new_status.lower()}.",
        "demo": True,
    }
