"""Research Agent Factories V3 - Subagent Coordinators.

This module introduces coordinator agents that orchestrate subagents using
shared memory backends. Two execution patterns are provided:

1. Simple + Sequential + Shared
   - One specialized researcher subagent.
   - Sequential baton-style execution (each task builds on the last).
   - Ideal for incremental reports where a single specialist iterates.

2. Specialized + Parallel + Shared
   - Three focused subagents (technology, market, competition).
   - Designed for parallel delegation via the ``task()`` tool.
   - Coordinator merges outputs into a unified report.

Both coordinator variants route ``/memories/research/`` into the persistent
store so that all subagents share the same long-term memory namespace.
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Mapping, MutableMapping, Optional

from deepagents import create_deep_agent

from langgraph.store.memory import InMemoryStore

from deepagent_app.agents.research_v2 import create_memory_backend


# ==============================================================================
# Shared system prompt fragments
# ==============================================================================

MEMORY_HYGIENE_INSTRUCTIONS = """\
Memory Hygiene
--------------
* Persist artifacts that should survive agent runs to `/memories/research/`.
* Use JSON for structured data and Markdown for human-readable summaries.
* Never overwrite existing files blindly—merge or append updated insights.
* Summaries returned to the coordinator must stay under 400 words.
"""


# ==============================================================================
# Simple + Sequential + Shared configuration
# ==============================================================================

SIMPLE_SEQUENTIAL_COORDINATOR_PROMPT = f"""\
You are the coordinator for a sequential research workflow.

Execution Pattern: Sequential baton pass — delegate one task at a time to the
`focus-researcher` subagent using the `task()` tool. Each delegated task must
build on the previous result. Always review the latest memory artifacts before
deciding the next step.

Delegation Rules:
1. Break the assignment into small checkpoints.
2. Call `task(name="focus-researcher", task=...)` for each checkpoint.
3. Wait for the result before planning the next step.
4. Summarize the combined findings and highlight open questions.

Shared Memory Protocol:
* All agents read/write `/memories/research/`.
* Encourage the subagent to store interim JSON under
  `/memories/research/{slug}_wip.json`.
* Consolidate a final JSON + Markdown deliverable when work concludes.

{MEMORY_HYGIENE_INSTRUCTIONS}
"""

SIMPLE_SEQUENTIAL_SUBAGENT_PROMPT = f"""\
You are `focus-researcher`, a methodical analyst.

Workflow Guidance:
1. Inspect `/memories/research/` for context relevant to the assigned topic.
2. Perform deep web research using the provided search tool.
3. Save incremental findings to `/memories/research/` (JSON for data,
   Markdown notes when helpful).
4. Return a concise update (<250 words) to the coordinator with:
   - Progress summary
   - New insights
   - Recommended next action

{MEMORY_HYGIENE_INSTRUCTIONS}
"""


def create_simple_sequential_research_agent(
    search_tool: Callable,
    *,
    system_prompt: str = SIMPLE_SEQUENTIAL_COORDINATOR_PROMPT,
    subagent_prompt: str = SIMPLE_SEQUENTIAL_SUBAGENT_PROMPT,
    store: Optional[object] = None,
    extra_tools: Optional[Iterable[Callable]] = None,
    metadata: Optional[Mapping[str, str]] = None,
) -> object:
    """Create a coordinator that executes a single sequential subagent.

    Args:
        search_tool: Configured internet search callable.
        system_prompt: Coordinator prompt (override for customization).
        subagent_prompt: Prompt used by the `focus-researcher` subagent.
        store: Shared LangGraph store. Defaults to an in-memory store if ``None``.
        extra_tools: Optional additional tools for the coordinator.
        metadata: Optional metadata dictionary forwarded to ``create_deep_agent``.

    Returns:
        DeepAgent instance with sequential delegation semantics.
    """

    subagent_tools: List[Callable] = [search_tool]
    if extra_tools:
        for tool in extra_tools:
            if tool not in subagent_tools:
                subagent_tools.append(tool)

    subagents = [
        {
            "name": "focus-researcher",
            "description": (
                "Sequential specialist that deep dives on a single strand of the "
                "research plan while persisting progress in shared memory."
            ),
            "system_prompt": subagent_prompt,
            "tools": subagent_tools,
        }
    ]

    coordinator_tools: List[Callable] = [search_tool]
    if extra_tools:
        for tool in extra_tools:
            if tool not in coordinator_tools:
                coordinator_tools.append(tool)

    agent_kwargs: MutableMapping[str, object] = {}
    if metadata:
        agent_kwargs["metadata"] = dict(metadata)

    if store is None:
        store = InMemoryStore()

    return create_deep_agent(
        tools=coordinator_tools,
        system_prompt=system_prompt,
        subagents=subagents,
        store=store,
        backend=create_memory_backend,
        **agent_kwargs,
    )


# ==============================================================================
# Specialized + Parallel + Shared configuration
# ==============================================================================

PARALLEL_COORDINATOR_PROMPT = f"""\
You orchestrate a multi-threaded research team. Dispatch specialized subagents
in parallel using the `task()` tool. Issue one task per subagent without
waiting, then gather results as they complete.

Workflow Checklist:
1. Plan the investigation (technology, market, competition).
2. Launch tasks concurrently:
   - `task(name="tech-analyst", task=...)`
   - `task(name="market-analyst", task=...)`
   - `task(name="competition-analyst", task=...)`
3. Monitor responses and synthesize a final deliverable that reconciles all
   perspectives, clearly attributing insights to each discipline.

Shared Memory Expectations:
* Require every subagent to persist structured output to
  `/memories/research/parallel/` using deterministic filenames.
* Merge overlapping discoveries instead of duplicating files.
* Use the shared store to cross-reference insights (e.g. market findings can
  inform competition analysis).

{MEMORY_HYGIENE_INSTRUCTIONS}
"""

TECH_SUBAGENT_PROMPT = f"""\
You are `tech-analyst`, responsible for technology landscape research.

Focus Areas:
* Core technologies, protocols, and innovations.
* Roadmaps, standards, and technical differentiators.

Deliverables:
1. A JSON document saved to `/memories/research/parallel/tech.json` with keys
   `highlights`, `risks`, `opportunities`, `notable_sources`.
2. A short summary (<200 words) returned to the coordinator.

{MEMORY_HYGIENE_INSTRUCTIONS}
"""

MARKET_SUBAGENT_PROMPT = f"""\
You are `market-analyst`, covering adoption, TAM, and macro forces.

Deliverables:
1. Persist `/memories/research/parallel/market.json` with
   `size`, `growth`, `drivers`, `headwinds`, `sources`.
2. Return a summary (<200 words) emphasising demand signals and GTM insights.

{MEMORY_HYGIENE_INSTRUCTIONS}
"""

COMPETITION_SUBAGENT_PROMPT = f"""\
You are `competition-analyst`, profiling competitors and substitutes.

Deliverables:
1. Store `/memories/research/parallel/competition.json` capturing
   `leaders`, `challengers`, `differentiators`, `threats`, `sources`.
2. Provide the coordinator with a concise digest (<200 words) spotlighting
   differentiation angles.

{MEMORY_HYGIENE_INSTRUCTIONS}
"""


def create_parallel_shared_research_agent(
    search_tool: Callable,
    *,
    system_prompt: str = PARALLEL_COORDINATOR_PROMPT,
    store: Optional[object] = None,
    tech_prompt: str = TECH_SUBAGENT_PROMPT,
    market_prompt: str = MARKET_SUBAGENT_PROMPT,
    competition_prompt: str = COMPETITION_SUBAGENT_PROMPT,
    extra_tools: Optional[Iterable[Callable]] = None,
    metadata: Optional[Mapping[str, str]] = None,
) -> object:
    """Create a coordinator with specialized parallel subagents.

    Args:
        search_tool: Configured internet search callable.
        system_prompt: Coordinator prompt instructing parallel delegation.
        store: Shared LangGraph store (defaults to in-memory when ``None``).
        tech_prompt: Prompt for the technology subagent.
        market_prompt: Prompt for the market subagent.
        competition_prompt: Prompt for the competition subagent.
        extra_tools: Optional additional tools for the coordinator and subagents.
        metadata: Optional metadata dictionary forwarded to ``create_deep_agent``.

    Returns:
        DeepAgent instance configured for parallel specialized delegation.
    """

    shared_tools: List[Callable] = [search_tool]
    if extra_tools:
        for tool in extra_tools:
            if tool not in shared_tools:
                shared_tools.append(tool)

    subagents = [
        {
            "name": "tech-analyst",
            "description": (
                "Technology scout delivering architecture trends and innovation "
                "signals while persisting structured findings."
            ),
            "system_prompt": tech_prompt,
            "tools": list(shared_tools),
        },
        {
            "name": "market-analyst",
            "description": (
                "Market strategist covering adoption metrics, TAM, and demand "
                "drivers with shared memory hand-offs."
            ),
            "system_prompt": market_prompt,
            "tools": list(shared_tools),
        },
        {
            "name": "competition-analyst",
            "description": (
                "Competitive intelligence lead mapping rivals, substitutes, and "
                "defensible advantages."
            ),
            "system_prompt": competition_prompt,
            "tools": list(shared_tools),
        },
    ]

    agent_kwargs: MutableMapping[str, object] = {}
    if metadata:
        agent_kwargs["metadata"] = dict(metadata)

    if store is None:
        store = InMemoryStore()

    return create_deep_agent(
        tools=list(shared_tools),
        system_prompt=system_prompt,
        subagents=subagents,
        store=store,
        backend=create_memory_backend,
        **agent_kwargs,
    )


__all__ = [
    "create_simple_sequential_research_agent",
    "create_parallel_shared_research_agent",
    "SIMPLE_SEQUENTIAL_COORDINATOR_PROMPT",
    "SIMPLE_SEQUENTIAL_SUBAGENT_PROMPT",
    "PARALLEL_COORDINATOR_PROMPT",
]

