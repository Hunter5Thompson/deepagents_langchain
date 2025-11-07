"""Coordinator-style research agents with subagent orchestration.

This module provides two coordinator agent factories based on the
requirements captured during the discovery session:

* Simple + Sequential + Shared memory coordinator
* Specialized + Parallel + Shared memory coordinator

Both coordinators rely on the DeepAgents runtime and leverage the
built-in middleware stack that exposes filesystem and subagent
capabilities. A composite backend is configured so that the regular
state backend handles ephemeral conversation artifacts while the
``/memories/research/`` prefix is persisted via a store backend. For the
current development workflow we rely on ``InMemoryStore`` which survives
for the lifetime of the Python process. Migrating to a persistent store
(e.g. PostgresStore) is a two-line change: swap the store class and pass
its instance to the agent factory.
"""

from __future__ import annotations

from typing import Callable, Sequence

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.middleware.subagents import SubAgent
from deepagents.middleware.types import AgentMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.types import Checkpointer

ToolLike = Callable[..., object]


# Shared filesystem routing -------------------------------------------------

def _create_shared_memory_backend() -> Callable[[object], CompositeBackend]:
    """Create a backend factory that exposes a shared memory prefix."""

    def backend_factory(runtime: object) -> CompositeBackend:  # pragma: no cover - simple wrapper
        return CompositeBackend(
            default=StateBackend(runtime),
            routes={"/memories/research/": StoreBackend(runtime)},
        )

    return backend_factory


def _resolve_store(store: BaseStore | None) -> BaseStore:
    """Return the provided store or fall back to the in-memory variant."""

    return store or InMemoryStore()


def _resolve_checkpointer(checkpointer: Checkpointer | None) -> Checkpointer:
    """Return the provided checkpointer or a simple in-memory saver."""

    return checkpointer or MemorySaver()


# Common prompt fragments ---------------------------------------------------

SHARED_MEMORY_REMINDER = """All agents share the /memories/research/ namespace.
Use ls/read_file/write_file/edit_file tools to collaborate safely.
Keep filenames descriptive (e.g. /memories/research/<topic>-notes.md)
and avoid deleting other agents' artefacts.
"""

SUBAGENT_OUTPUT_GUIDELINES = """When returning results:
- Provide a concise summary (max 250 words) with clear bullet points.
- Cite sources inline with URLs for every major claim.
- Do not paste raw tool outputs. Store long content in shared files instead.
"""


def _build_simple_subagents(search_tool: ToolLike) -> Sequence[SubAgent]:
    """Create the single subagent used by the sequential coordinator."""

    simple_executor_prompt = f"""You are the Research Executor working on a focused subtask.

Your responsibilities:
1. Plan the investigation briefly and execute precise internet_search calls.
2. Capture structured notes (bullets, short quotes with source URLs) in a
   new or existing Markdown file under /memories/research/ (for example
   `/memories/research/stage-notes.md`).
3. Summarise the findings in your final reply so the coordinator can
   reference them immediately.

If you gather large datasets, save them to the filesystem first and only
return distilled insights.

{SHARED_MEMORY_REMINDER}
{SUBAGENT_OUTPUT_GUIDELINES}
"""

    return (
        {
            "name": "research-executor",
            "description": "Executes a focused research task and saves notes to shared memory.",
            "system_prompt": simple_executor_prompt,
            "tools": [search_tool],
        },
    )


def _build_specialised_subagents(search_tool: ToolLike) -> Sequence[SubAgent]:
    """Create domain-specific subagents for the parallel coordinator."""

    tech_prompt = f"""You are the Technical Research Specialist.
Focus on architecture, product capabilities, roadmaps, and key
technology differentiators. Perform targeted internet_search calls and
store your notes under `/memories/research/tech-*.md`.

{SHARED_MEMORY_REMINDER}
{SUBAGENT_OUTPUT_GUIDELINES}
"""

    market_prompt = f"""You are the Market Analyst.
Investigate TAM/SAM/SOM figures, pricing models, customer segments, and
macro trends. Use precise internet_search queries and save findings to
`/memories/research/market-*.md`.

{SHARED_MEMORY_REMINDER}
{SUBAGENT_OUTPUT_GUIDELINES}
"""

    competition_prompt = f"""You are the Competitive Intelligence Specialist.
Compare main competitors, positioning, strengths/weaknesses, and recent
moves. Collect sourced evidence with internet_search and write to
`/memories/research/competition-*.md`.

{SHARED_MEMORY_REMINDER}
{SUBAGENT_OUTPUT_GUIDELINES}
"""

    return (
        {
            "name": "tech-specialist",
            "description": "Deep technical product research and architectural analysis.",
            "system_prompt": tech_prompt,
            "tools": [search_tool],
        },
        {
            "name": "market-analyst",
            "description": "Market sizing, pricing, and customer landscape research.",
            "system_prompt": market_prompt,
            "tools": [search_tool],
        },
        {
            "name": "competition-analyst",
            "description": "Competitive landscape comparisons and differentiation insights.",
            "system_prompt": competition_prompt,
            "tools": [search_tool],
        },
    )


# Public factories ----------------------------------------------------------

def create_simple_sequential_shared_agent(
    search_tool: ToolLike,
    *,
    system_prompt: str | None = None,
    middleware: Sequence[AgentMiddleware] | None = None,
    store: BaseStore | None = None,
    checkpointer: Checkpointer | None = None,
) -> object:
    """Create the simple sequential coordinator with shared memory."""

    base_prompt = """You are the Research Flow Coordinator.
Run a *sequential* workflow:
1. Identify the next concrete subtask and launch the `research-executor`
   via the task tool with explicit instructions.
2. Wait for the subagent result, inspect the files it created under
   /memories/research/, and update/append summaries if needed.
3. Communicate the final answer to the user referencing key artefacts.

Never launch multiple task agents at the same time. Finish one before
starting the next. Optimise for clarity and reuse of the shared notes.
Always cite sources and keep your replies concise.
"""

    resolved_prompt = f"{base_prompt}\n\n{SHARED_MEMORY_REMINDER}" if system_prompt is None else system_prompt
    backend_factory = _create_shared_memory_backend()
    resolved_store = _resolve_store(store)
    resolved_checkpointer = _resolve_checkpointer(checkpointer)
    subagents = list(_build_simple_subagents(search_tool))
    middleware_list = list(middleware or [])

    return create_deep_agent(
        tools=[search_tool],
        system_prompt=resolved_prompt,
        backend=backend_factory,
        store=resolved_store,
        checkpointer=resolved_checkpointer,
        subagents=subagents,
        middleware=middleware_list,
        name="research-coordinator-simple",
    )


def create_specialized_parallel_shared_agent(
    search_tool: ToolLike,
    *,
    system_prompt: str | None = None,
    middleware: Sequence[AgentMiddleware] | None = None,
    store: BaseStore | None = None,
    checkpointer: Checkpointer | None = None,
) -> object:
    """Create the specialised coordinator that favours parallel execution."""

    base_prompt = """You are the Multi-Disciplinary Research Lead.
Break down complex questions into parallel workstreams handled by the
specialised task agents (tech-specialist, market-analyst,
competition-analyst).

Best practices:
- Launch the relevant specialists *in parallel* whenever their work can
  progress independently. Use a single response with multiple task tool
  calls so they run concurrently.
- Coordinate through the shared memory files each specialist maintains.
- After receiving the results, reconcile overlaps, highlight conflicts,
  and deliver a coherent synthesis to the user.
- Ensure the final deliverable includes cited sources and highlights
  where supporting documents live in /memories/research/.
"""

    resolved_prompt = f"{base_prompt}\n\n{SHARED_MEMORY_REMINDER}" if system_prompt is None else system_prompt
    backend_factory = _create_shared_memory_backend()
    resolved_store = _resolve_store(store)
    resolved_checkpointer = _resolve_checkpointer(checkpointer)
    subagents = list(_build_specialised_subagents(search_tool))
    middleware_list = list(middleware or [])

    return create_deep_agent(
        tools=[search_tool],
        system_prompt=resolved_prompt,
        backend=backend_factory,
        store=resolved_store,
        checkpointer=resolved_checkpointer,
        subagents=subagents,
        middleware=middleware_list,
        name="research-coordinator-specialised",
    )


__all__ = [
    "create_simple_sequential_shared_agent",
    "create_specialized_parallel_shared_agent",
]
