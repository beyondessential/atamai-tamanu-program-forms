"""
Atamai — Tamanu Assistant

Multi-skill AI assistant for Tamanu implementers. The AI automatically determines
which skill to use from the conversation — no explicit tool switching required.
"""

import base64
from io import BytesIO

import streamlit as st
from baml_py import Image as BamlImage
from dotenv import load_dotenv
from pypdf import PdfReader

from baml_client.sync_client import b
from baml_client.types import Skill
from xlsx_parser import parse_xlsx
from skills import program_builder, lab_builder, questions

load_dotenv()

_ALL_SKILLS = [program_builder, lab_builder, questions]
_SKILL_MAP: dict[str, object] = {s.TITLE: s for s in _ALL_SKILLS}
_BAML_SKILL_MAP: dict[Skill, object] = {
    Skill.ProgramBuilder: program_builder,
    Skill.LabBuilder: lab_builder,
    Skill.Questions: questions,
}

st.set_page_config(
    page_title="Atamai — Tamanu",
    page_icon="🏥",
    layout="centered",
)

# ── Session state ──────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "upload_context" not in st.session_state:
    st.session_state.upload_context = None

if "upload_program_data" not in st.session_state:
    st.session_state.upload_program_data = None

if "uploaded_filenames" not in st.session_state:
    st.session_state.uploaded_filenames = set()

if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

if "active_skill" not in st.session_state:
    st.session_state.active_skill = None

# Initialise all skill states
for _skill in _ALL_SKILLS:
    _skill.init_state()

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Atamai")

    if st.session_state.active_skill:
        active = _SKILL_MAP.get(st.session_state.active_skill)
        if active:
            st.caption(f"Active: {active.ICON} {active.TITLE}")
            st.divider()
            active.render_sidebar()
            st.divider()

    st.subheader("Attach files")
    st.caption(
        "Upload existing program or lab XLSXs to modify, CSV data, PDF specs, "
        "or images of paper forms."
    )

    uploaded_files = st.file_uploader(
        "files",
        type=["xlsx", "csv", "pdf", "png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.file_uploader_key}",
    )

    current_names = {f.name for f in (uploaded_files or [])}
    if current_names != st.session_state.uploaded_filenames:
        contexts = []
        st.session_state.upload_program_data = None

        for uploaded_file in (uploaded_files or []):
            file_bytes = uploaded_file.read()
            ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

            if ext == "xlsx":
                with st.spinner(f"Parsing {uploaded_file.name}..."):
                    summary, program_data, errors = parse_xlsx(file_bytes)
                for err in errors:
                    st.warning(err)
                if summary:
                    contexts.append(summary)
                if program_data and st.session_state.upload_program_data is None:
                    st.session_state.upload_program_data = program_data

            elif ext == "csv":
                text = file_bytes.decode("utf-8", errors="replace")
                contexts.append(f"[CSV FILE: {uploaded_file.name}]\n{text}")

            elif ext == "pdf":
                reader = PdfReader(BytesIO(file_bytes))
                pages_text = []
                for i, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_text.append(f"[Page {i}]\n{text.strip()}")
                if not pages_text:
                    st.warning(
                        f"Could not extract text from {uploaded_file.name}. "
                        "It may be a scanned document — try uploading it as an image instead."
                    )
                else:
                    contexts.append("[PDF DOCUMENT LOADED]\n\n" + "\n\n".join(pages_text))

            else:
                mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
                with st.spinner(f"Interpreting {uploaded_file.name}..."):
                    baml_image = BamlImage.from_base64(
                        mime, base64.b64encode(file_bytes).decode()
                    )
                    description = b.InterpretFormImage(baml_image)
                contexts.append(f"[FORM IMAGE INTERPRETED]\n{description}")

        st.session_state.upload_context = "\n\n".join(contexts) if contexts else None
        st.session_state.uploaded_filenames = current_names
        st.rerun()

    if st.session_state.upload_context:
        for name in sorted(st.session_state.uploaded_filenames):
            st.success(f"Loaded: {name}")
        if st.button("Clear attachments", use_container_width=True):
            st.session_state.upload_context = None
            st.session_state.upload_program_data = None
            st.session_state.uploaded_filenames = set()
            st.session_state.file_uploader_key += 1
            st.rerun()

# ── Main area ──────────────────────────────────────────────────────────────────

st.title("🏥 Atamai — Tamanu")
st.caption("Your Tamanu assistant — describe what you need and I'll figure out how to help.")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Active skill outputs (download buttons, etc.)
if st.session_state.active_skill:
    active = _SKILL_MAP.get(st.session_state.active_skill)
    if active:
        active.render_outputs()

# ── Slash command helpers ──────────────────────────────────────────────────────

_SLASH_COMMANDS: dict[str, str] = {
    "program": program_builder.TITLE,
    "program_builder": program_builder.TITLE,
    "lab": lab_builder.TITLE,
    "lab_builder": lab_builder.TITLE,
    "q": questions.TITLE,
    "question": questions.TITLE,
}


def _parse_slash(text: str) -> tuple[str | None, str]:
    """Return (skill_title, remaining_text) if text is a slash command, else (None, text)."""
    if not text.startswith("/"):
        return None, text
    parts = text[1:].split(None, 1)
    cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    return _SLASH_COMMANDS.get(cmd), rest


def _build_history() -> str:
    history = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
    )
    if st.session_state.upload_context:
        history = st.session_state.upload_context + "\n\n" + history
    return history


# ── Chat input ─────────────────────────────────────────────────────────────────

_skill_cmds = "  ·  ".join(f"`/{cmd}`" for cmd in ["program", "lab", "q"])
st.caption(f"Tip: use {_skill_cmds} to switch tools directly.")

if user_input := st.chat_input("Ask me anything about Tamanu..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    slash_title, remaining = _parse_slash(user_input)

    if slash_title is not None:
        # ── Explicit skill switch via slash command ─────────────────────────────
        skill = _SKILL_MAP.get(slash_title)
        if skill is None:
            available = ", ".join(f"`/{c}`" for c in _SLASH_COMMANDS)
            msg = f"Unknown command. Available: {available}"
            with st.chat_message("assistant"):
                st.write(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})
        else:
            st.session_state.active_skill = skill.TITLE
            if remaining:
                skill.handle_message(remaining, _build_history())
            else:
                confirm = f"Switched to {skill.ICON} **{skill.TITLE}**. How can I help?"
                with st.chat_message("assistant"):
                    st.write(confirm)
                st.session_state.messages.append({"role": "assistant", "content": confirm})
                st.rerun()

    else:
        # ── Auto-route via AI (only when no skill is active yet) ───────────────
        if st.session_state.active_skill:
            skill = _SKILL_MAP[st.session_state.active_skill]
        else:
            try:
                with st.spinner("Thinking..."):
                    route = b.RouteMessage(user_input)
            except Exception:
                msg = "Sorry, I'm having trouble connecting right now. Please try again in a moment."
                with st.chat_message("assistant"):
                    st.write(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.stop()

            if route.skill == Skill.OffTopic:
                available = ", ".join(f"`/{c}`" for c in ["program", "lab", "q"])
                refusal = (
                    "I can only help with Tamanu-related tasks — "
                    "building program forms, lab reference data, or answering Tamanu questions. "
                    f"Is there something Tamanu-related I can help with? "
                    f"(You can also switch tools directly with {available}.)"
                )
                with st.chat_message("assistant"):
                    st.write(refusal)
                st.session_state.messages.append({"role": "assistant", "content": refusal})
                skill = None

            else:
                skill = _BAML_SKILL_MAP[route.skill]
                st.session_state.active_skill = skill.TITLE

        if skill is not None:
            skill.handle_message(user_input, _build_history())
