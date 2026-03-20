"""Questions skill — answers questions about Tamanu via the github-repo-rag MCP server.

Two modes:
  HTTP (shared server): Set RAG_MCP_URL and GOOGLE_SERVICE_ACCOUNT_FILE in .env.
                        The app authenticates as the service account.
  stdio (local):        Leave RAG_MCP_URL unset. The MCP server is spawned as a
                        subprocess — no auth required.
"""

import asyncio
import os
import shutil
import sys
from pathlib import Path

import anthropic
import streamlit as st

TITLE = "Questions"
ICON = "💬"
DESCRIPTION = "Ask questions about Tamanu — how it works, configuration, and troubleshooting."

_SYSTEM = (
    "You are a helpful assistant. Use the retrieved context below to answer questions accurately. "
    "Your audience is non-technical — explain concepts in plain language, avoid jargon, and focus on what things do rather than how they are implemented. "
    "If the user asks for technical details, you may include file paths, package names, and implementation specifics. "
    "If the retrieved context doesn't fully answer the question, say what you know and be honest about gaps."
)

_MODEL = "claude-sonnet-4-6"
_RAG_DIR = str(Path(__file__).parent.parent.parent / "github-repo-rag")
_NAMESPACE = "tamanu"


def _is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _get_service_token() -> str:
    """Get a Google OAuth access token from the service account credentials."""
    import google.auth.transport.requests
    from google.oauth2 import service_account

    scopes = ["https://www.googleapis.com/auth/userinfo.email"]

    key_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if key_file:
        creds = service_account.Credentials.from_service_account_file(key_file, scopes=scopes)
    else:
        import json
        creds = service_account.Credentials.from_service_account_info(
            json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]),
            scopes=scopes,
        )

    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


async def _mcp_search_http(question: str, mcp_url: str) -> str:
    """Call search_codebase on the shared MCP server via HTTP with service account auth."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    token = _get_service_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await asyncio.wait_for(
                session.call_tool("search_codebase", {"question": question, "namespace": _NAMESPACE}),
                timeout=60,
            )
    return result.content[0].text


async def _mcp_search_stdio(question: str) -> str:
    """Spawn the MCP server as a local subprocess (no auth required)."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    uv = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv.exe")
    params = StdioServerParameters(
        command=uv,
        args=["run", "--directory", _RAG_DIR, "github-repo-rag-mcp"],
        env=dict(os.environ),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await asyncio.wait_for(
                session.call_tool("search_codebase", {"question": question, "namespace": _NAMESPACE}),
                timeout=60,
            )
    return result.content[0].text


def _search_codebase(question: str) -> str:
    mcp_url = os.environ.get("RAG_MCP_URL")
    coro = _mcp_search_http(question, mcp_url) if mcp_url else _mcp_search_stdio(question)

    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def init_state() -> None:
    pass


def reset_state() -> None:
    pass


def render_sidebar() -> None:
    if not _is_configured():
        st.warning("Set `ANTHROPIC_API_KEY` in `.env` to enable Q&A.")


def render_outputs() -> None:
    pass


def handle_message(user_input: str, conversation_history: str) -> None:
    if not _is_configured():
        msg = "The Questions skill requires `ANTHROPIC_API_KEY` to be set in `.env`."
        with st.chat_message("assistant"):
            st.write(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})
        return

    response_text = ""
    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching Tamanu codebase..."):
                context = _search_codebase(user_input)

            with st.spinner("Generating answer..."):
                system = f"{_SYSTEM}\n\n## Retrieved context\n\n{context}"
                history = st.session_state.messages[:-1]
                messages = [{"role": m["role"], "content": m["content"]} for m in history]
                messages.append({"role": "user", "content": user_input})

                client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
                response = client.messages.create(
                    model=_MODEL,
                    max_tokens=2048,
                    system=system,
                    messages=messages,
                )
                response_text = response.content[0].text

            st.write(response_text)
        except Exception as exc:
            actual = exc.exceptions[0] if hasattr(exc, "exceptions") else exc
            if isinstance(actual, (FileNotFoundError, asyncio.TimeoutError, ConnectionRefusedError, ConnectionError, OSError)):
                response_text = "The Questions skill is currently unavailable — the search service could not be reached. Please try again later."
            else:
                response_text = f"Sorry, something went wrong: {type(actual).__name__}: {actual}"
            st.error(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
