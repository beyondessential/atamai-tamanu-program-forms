"""
Atamai - Tamanu Program & Registry Builder

A conversational assistant that helps implementers build Tamanu program
form and registry XLSX files for import via the program importer.
"""

import base64
from io import BytesIO

import streamlit as st
from baml_py import Image as BamlImage
from dotenv import load_dotenv
from pypdf import PdfReader

from baml_client.sync_client import b
from xlsx_generator import generate_xlsx
from xlsx_parser import parse_xlsx

load_dotenv()

st.set_page_config(
    page_title="Tamanu Program & Registry Builder",
    page_icon="🏥",
    layout="centered",
)

st.title("Tamanu Program & Registry Builder")
st.caption("Describe the program form you need and I'll help you build it.")

# ── Session state ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "xlsx_data" not in st.session_state:
    st.session_state.xlsx_data = None

if "program_name" not in st.session_state:
    st.session_state.program_name = "survey"

if "upload_context" not in st.session_state:
    st.session_state.upload_context = None

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

# ── Sidebar — file upload ──────────────────────────────────────────────────────

with st.sidebar:
    st.subheader("Attach a file")
    st.caption("Upload an existing program XLSX to modify, or an image of a paper form to base your form on.")

    uploaded_file = st.file_uploader(
        "file",
        type=["xlsx", "pdf", "png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_file and uploaded_file.name != st.session_state.uploaded_filename:
        file_bytes = uploaded_file.read()
        ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

        if ext == "xlsx":
            with st.spinner("Parsing XLSX..."):
                summary, errors = parse_xlsx(file_bytes)
            for err in errors:
                st.warning(err)
            if summary:
                st.session_state.upload_context = summary
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.messages = []
                st.rerun()
        elif ext == "pdf":
            reader = PdfReader(BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f"[Page {i}]\n{text.strip()}")
            if not pages_text:
                st.warning("Could not extract text from this PDF. It may be a scanned document — try uploading it as an image instead.")
            else:
                st.session_state.upload_context = "[PDF DOCUMENT LOADED]\n\n" + "\n\n".join(pages_text)
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.messages = []
                st.rerun()
        else:
            mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
            with st.spinner("Interpreting image..."):
                baml_image = BamlImage.from_base64(mime, base64.b64encode(file_bytes).decode())
                description = b.InterpretFormImage(baml_image)
            st.session_state.upload_context = f"[FORM IMAGE INTERPRETED]\n{description}"
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.messages = []
            st.rerun()

    if st.session_state.upload_context:
        st.success(f"Loaded: {st.session_state.uploaded_filename}")
        if st.button("Clear attachment", use_container_width=True):
            st.session_state.upload_context = None
            st.session_state.uploaded_filename = None
            st.rerun()

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
            st.session_state.upload_context = None
            st.session_state.uploaded_filename = None
            st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────

if user_input := st.chat_input("Describe your program, surveys, or registry..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Format conversation history for BAML, prepending any upload context
    conversation_history = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
    )
    if st.session_state.upload_context:
        conversation_history = st.session_state.upload_context + "\n\n" + conversation_history

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
