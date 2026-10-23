import streamlit as st

from src.agent_graph import askhr_graph

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
