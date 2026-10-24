
import streamlit as st

from src.agent_graph import askhr_graph
from src.hr_tools import (
    AUTHORIZED_MANAGERS,
    get_leave_requests,
    decide_leave_request,
    get_audit_log,
    get_leave_balance,
    get_leave_request,
    submit_leave_request,
)

st.set_page_config(
    page_title="AskHR | Employee Assistant",
    page_icon="💬",
    layout="centered",
)

st.title("💬 AskHR")
st.caption("Agentic AI employee assistant — demonstration prototype")

DEMO_EMPLOYEE_ID = "EMP001"

with st.sidebar:
    st.subheader("About AskHR")
    st.write("Ask questions about sample HR policies and demo employee data.")
    st.info(
        "Fictional demo policies and synthetic employee data only. "
        "Not connected to Vodafone HR systems."
    )
    st.caption(f"Demo employee: {DEMO_EMPLOYEE_ID}")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

chat_tab, employee_tab, manager_tab, audit_tab = st.tabs(
    ["AskHR Chat", "Employee Leave", "Manager Review", "Audit Log"]
)

with chat_tab:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.write(f"• {source}")

    question = st.chat_input(
        "Ask about HR policies or your demo leave balance..."
    )

    if question:
        st.session_state.messages.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                result = askhr_graph.invoke({
                    "question": question,
                    "employee_id": DEMO_EMPLOYEE_ID,
                })

                answer = result.get(
                    "answer",
                    "I couldn't produce an answer. Please try again.",
                )
                sources = result.get("sources", [])

                st.markdown(answer)

                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.write(f"• {source}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })

            except Exception:
                st.error(
                    "AskHR couldn't process this request. "
                    "Check the application logs and try again."
                )

with employee_tab:
    st.subheader("Submit a leave request")
    st.caption(f"Demo employee: {DEMO_EMPLOYEE_ID}")

    balance_result = get_leave_balance(DEMO_EMPLOYEE_ID)
    if balance_result["success"]:
        st.metric(
            "Demo leave balance",
            f'{balance_result["leave_balance"]} days',
        )

    with st.form("leave_request_form"):
        days_requested = st.number_input(
            "Number of leave days",
            min_value=1,
            max_value=30,
            value=1,
            step=1,
        )
        reason = st.text_area(
            "Reason for leave",
            placeholder="Enter a reason for your request",
        )
        confirmed = st.checkbox(
            "I confirm that I want to submit this demo leave request."
        )
        submitted = st.form_submit_button("Submit leave request")

    if submitted:
        result = submit_leave_request(
            employee_id=DEMO_EMPLOYEE_ID,
            days=int(days_requested),
            reason=reason,
            confirmed=confirmed,
        )

        if result["success"]:
            st.success(
                f'Request {result["request_id"]} submitted. '
                f'Status: {result["status"]}'
            )
        else:
            st.error(result["message"])

    st.divider()
    st.subheader("My demo requests")

    employee_requests = [
        request
        for request in get_leave_requests()
        if request["employee_id"] == DEMO_EMPLOYEE_ID
    ]

    if not employee_requests:
        st.info("No leave requests submitted in this app session.")
    else:
        for request in reversed(employee_requests):
            with st.expander(
                f'{request["request_id"]} — {request["status"]}'
            ):
                st.write(f'Days: {request["days_requested"]}')
                st.write(f'Reason: {request["reason"]}')
                if request["manager_comments"]:
                    st.write(
                        f'Manager comments: {request["manager_comments"]}'
                    )

with manager_tab:
    st.subheader("Manager review")
    st.warning(
        "Demo only: this panel is not protected by real authentication. "
        "The manager ID is checked against a hard-coded demo allowlist."
    )

    manager_id = st.text_input(
        "Demo manager ID",
        value="MGR001",
        key="manager_id",
    )

    pending_requests = [
        request
        for request in get_leave_requests()
        if request["status"] == "PENDING_MANAGER_APPROVAL"
    ]

    if not pending_requests:
        st.info("No pending requests in this app session.")

    for request in pending_requests:
        with st.container(border=True):
            st.markdown(f'**Request: {request["request_id"]}**')
            st.write(f'Employee: {request["employee_id"]}')
            st.write(f'Days: {request["days_requested"]}')
            st.write(f'Reason: {request["reason"]}')

            with st.form(f'review_{request["request_id"]}'):
                comments = st.text_input(
                    "Manager comments",
                    key=f'comments_{request["request_id"]}',
                )
                decision = st.radio(
                    "Decision",
                    ["Approve", "Reject"],
                    horizontal=True,
                    key=f'decision_{request["request_id"]}',
                )
                decide = st.form_submit_button("Record decision")

            if decide:
                result = decide_leave_request(
                    request_id=request["request_id"],
                    manager_id=manager_id.strip(),
                    approved=(decision == "Approve"),
                    comments=comments,
                )

                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

with audit_tab:
    st.subheader("Demo audit log")
    audit_events = get_audit_log()

    if not audit_events:
        st.info("No audit events recorded in this app session.")
    else:
        st.caption(
            "Events are held in memory and are lost when the app process "
            "restarts. This is not a durable production audit system."
        )
        st.dataframe(audit_events, use_container_width=True)
