"""Telemetry helpers for Langfuse call tracing."""

from __future__ import annotations

import inspect
import uuid
from typing import Dict, List, Optional

from deepagent_app.config import Config

try:  # pragma: no cover - optional dependency
    from langfuse import Langfuse
    from langfuse.callback import CallbackHandler as LangfuseCallbackHandler
except Exception:  # pragma: no cover - optional dependency
    Langfuse = None  # type: ignore[assignment]
    LangfuseCallbackHandler = None  # type: ignore[assignment]

_MISSING_LANGFUSE_WARNING_EMITTED = False


def _filter_kwargs(target, values: Dict[str, object]) -> Dict[str, object]:
    """Return only keyword arguments accepted by the callable."""

    try:
        parameters = inspect.signature(target).parameters
    except (TypeError, ValueError):  # pragma: no cover - very defensive
        return {}

    return {key: value for key, value in values.items() if key in parameters}


def _emit_missing_dependency_warning() -> None:
    """Emit a single warning when langfuse package is unavailable."""

    global _MISSING_LANGFUSE_WARNING_EMITTED
    if _MISSING_LANGFUSE_WARNING_EMITTED:
        return
    print("⚠️  Langfuse dependency not installed. Skipping call tracing.")
    _MISSING_LANGFUSE_WARNING_EMITTED = True


def create_langfuse_callbacks(
    config: Config,
    *,
    agent_type: str,
    thread_id: Optional[str],
    query: str,
) -> List[object]:
    """Return LangChain callbacks for Langfuse tracing, if enabled."""

    if not config.langfuse_active:
        return []

    if Langfuse is None or LangfuseCallbackHandler is None:
        _emit_missing_dependency_warning()
        return []

    client_kwargs = {
        "public_key": config.langfuse_public_key,
        "secret_key": config.langfuse_secret_key,
    }
    if config.langfuse_host:
        client_kwargs["host"] = config.langfuse_host

    client_kwargs = _filter_kwargs(Langfuse.__init__, client_kwargs)

    try:
        client = Langfuse(**client_kwargs)
    except Exception as exc:  # pragma: no cover - runtime safeguard
        print(f"⚠️  Failed to initialize Langfuse client: {exc}")
        return []

    handler_kwargs = {
        "session_id": thread_id or f"cli-session-{uuid.uuid4().hex[:8]}",
        "user_id": thread_id or "research-cli",
        "tags": ["research-cli", agent_type],
        "metadata": {
            "query": query,
            "agent_type": agent_type,
            "thread_id": thread_id,
        },
        "trace_name": f"research::{agent_type}",
    }
    if config.langfuse_release:
        handler_kwargs["release"] = config.langfuse_release

    handler_params = inspect.signature(LangfuseCallbackHandler.__init__).parameters
    if "langfuse_client" in handler_params:
        handler_kwargs["langfuse_client"] = client
    else:
        handler_kwargs.update(
            _filter_kwargs(
                LangfuseCallbackHandler.__init__,
                {
                    "public_key": config.langfuse_public_key,
                    "secret_key": config.langfuse_secret_key,
                    "host": config.langfuse_host,
                },
            )
        )

    handler_kwargs = _filter_kwargs(LangfuseCallbackHandler.__init__, handler_kwargs)

    try:
        handler = LangfuseCallbackHandler(**handler_kwargs)
    except Exception as exc:  # pragma: no cover - runtime safeguard
        print(f"⚠️  Failed to initialize Langfuse callback: {exc}")
        return []

    return [handler]
