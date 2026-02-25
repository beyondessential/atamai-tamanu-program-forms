"""
Atamai - Tamanu Program Form Builder

A conversational assistant that helps implementers build Tamanu program
form XLSX files for import via the program importer.
"""

import streamlit as st
from dotenv import load_dotenv

from baml_client.sync_client import b
from xlsx_generator import generate_xlsx

load_dotenv()

st.set_page_config(
    page_title="Tamanu Program Form Builder",
    page_icon="🏥",
    layout="centered",
)

st.title("Tamanu Program Form Builder")
st.caption("Describe the program form you need and I'll help you build it.")

# ── Session state ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "xlsx_data" not in st.session_state:
    st.session_state.xlsx_data = None

if "program_name" not in st.session_state:
    st.session_state.program_name = "survey"

# ── Chat history ──────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Download section (shown at bottom of conversation once XLSX is ready) ─────

if st.session_state.xlsx_data:
    st.success("Your XLSX is ready to download.")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.download_button(
            label="⬇️  Download survey XLSX",
            data=st.session_state.xlsx_data,
            file_name=f"{st.session_state.program_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col2:
        if st.button("Start new survey", use_container_width=True):
            st.session_state.messages = []
            st.session_state.xlsx_data = None
            st.session_state.program_name = "survey"
            st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────

if user_input := st.chat_input("Describe your survey..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Format conversation history for BAML
    conversation_history = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = b.ProcessMessage(conversation_history)

        st.write(result.message)
        st.session_state.messages.append({"role": "assistant", "content": result.message})

        if result.ready_to_generate:
            try:
                with st.spinner("Generating survey definition..."):
                    program = b.BuildSurveyDefinition(conversation_history)

                with st.spinner("Building XLSX..."):
                    xlsx_bytes = generate_xlsx(program)

                st.session_state.xlsx_data = xlsx_bytes
                st.session_state.program_name = program.program_code.lower()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate XLSX: {e}")
