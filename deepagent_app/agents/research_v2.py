"""
Research Agent Factory V2 - Long-Term Memory Edition
====================================================

Advanced research agents with persistent memory across threads and conversations.

Author: GISA R&D
Created: 2025-11-06
Version: 2.1.0 - Fixed API (CompositeBackend)
"""

from pathlib import Path
from typing import Callable, Optional

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# ==============================================================================
# SYSTEM PROMPTS - Token-Optimized
# ==============================================================================

MEMORY_RESEARCH_PROMPT_MINIMAL = """Expert researcher with persistent memory.

BEFORE research: Check `/memories/research/` for existing files
DURING: Save WIP to `/memories/research/{topic}_wip.json`
AFTER: Save final to `/memories/research/{topic}.json` + `/{topic}_report.md`

Files in `/memories/` = permanent, others = temporary

Tool: `internet_search(query, max_results=5, topic='general'|'news'|'finance')`

Build knowledge incrementally."""

MEMORY_RESEARCH_PROMPT = """Expert researcher with PERSISTENT MEMORY across sessions.

## Memory Protocol
BEFORE: Check `/memories/research/`, read existing data
DURING: Save progress `/memories/research/{topic}_wip.json`
AFTER: Save `/memories/research/{topic}.json` (structured) + `/{topic}_report.md` (human)

## File Rules
`/memories/*` = PERMANENT | `/*` = TEMPORARY

## Strategy
1. Check memory → 2. Fill gaps → 3. Synthesize → 4. Save JSON+MD

Tool: `internet_search(query, max_results=5, topic='general'|'news'|'finance')`

Every session makes you smarter about that topic."""

MEMORY_RESEARCH_PROMPT_DETAILED = """You are an expert researcher with PERSISTENT MEMORY across sessions.

## 🧠 Memory Protocol

**BEFORE research:**
1. Check `/memories/research/` for existing files
2. If topic researched before: READ existing data first
3. Identify what's outdated or missing

**DURING research:**
- Save progress: `/memories/research/{topic}_wip.json`
- Prevents data loss if interrupted

**AFTER research:**
- Save final: `/memories/research/{topic}.json`
- JSON format: {"topic", "timestamp", "summary", "findings", "sources", "confidence"}
- Also create human-readable: `/{topic}_report.md` (temporary)

## 📁 File Rules
- `/memories/*` = PERMANENT (survives restarts)
- `/*` = TEMPORARY (deleted after thread)

## 🎯 Research Strategy
1. Check memory → 2. Fill gaps → 3. Synthesize → 4. Save both JSON + MD

## 🔧 Tools
- `internet_search(query, max_results=5, topic='general'|'news'|'finance')`

Build knowledge incrementally. Every session makes you smarter about that topic.
"""

SIMPLE_RESEARCH_PROMPT = """Expert researcher.

Process: Plan → Search → Synthesize → Cite sources

Tool: `internet_search(query, max_results=5, topic='general'|'news'|'finance')`"""


# ==============================================================================
# BACKEND FACTORIES - Correct API
# ==============================================================================

def create_memory_backend(runtime):
    """
    Create CompositeBackend that routes /memories/ to persistent storage.
    
    Args:
        runtime: Runtime passed by deepagents
        
    Returns:
        CompositeBackend with /memories/ routed to StoreBackend
    """
    return CompositeBackend(
        default=StateBackend(runtime),  # Ephemeral storage
        routes={
            "/memories/": StoreBackend(runtime)  # Persistent storage
        }
    )


# ==============================================================================
# STORE FACTORIES
# ==============================================================================

def create_file_store(base_path: Path = Path(".deepagent_store")) -> InMemoryStore:
    """
    Create file-backed store for persistence.
    
    Args:
        base_path: Directory for storage files
        
    Returns:
        Store instance with file persistence
        
    Note:
        Currently returns InMemoryStore. For production, implement
        proper file serialization or use PostgresStore.
    """
    base_path.mkdir(parents=True, exist_ok=True)
    store = InMemoryStore()
    print(f"⚠️  File store not implemented, using InMemoryStore")
    print(f"   Store path would be: {base_path}")
    return store


def create_shared_store() -> InMemoryStore:
    """
    Create a shared InMemoryStore for multiple agents.
    
    Returns:
        Fresh InMemoryStore instance
        
    Warning:
        Data lost on restart. Use PostgresStore for persistence.
    """
    return InMemoryStore()


# ==============================================================================
# AGENT FACTORIES - Fixed API
# ==============================================================================

def create_memory_research_agent(
    search_tool: Callable,
    system_prompt: str = MEMORY_RESEARCH_PROMPT,
    store: Optional[InMemoryStore] = None,
    verbose: bool = False,
) -> object:
    """
    Create research agent with long-term memory.
    
    Features:
    ✅ Persistent memory across sessions
    ✅ Builds on previous research
    ✅ Incremental progress saving
    ✅ Organized knowledge in /memories/
    
    Args:
        search_tool: Configured search tool (from tools.search)
        system_prompt: Custom prompt (default: MEMORY_RESEARCH_PROMPT)
                      Options: MEMORY_RESEARCH_PROMPT_MINIMAL (fastest)
                               MEMORY_RESEARCH_PROMPT (balanced)
                               MEMORY_RESEARCH_PROMPT_DETAILED (verbose)
        store: LangGraph Store instance (creates InMemoryStore if None)
        verbose: Print debug info
        
    Returns:
        DeepAgent with long-term memory
        
    Example:
        >>> from deepagent_app.tools import create_search_tool
        >>> from deepagent_app.agents.research_v2 import create_memory_research_agent
        >>> 
        >>> search_tool = create_search_tool(tavily_key)
        >>> agent = create_memory_research_agent(search_tool)
        >>> 
        >>> # Thread-based memory (REQUIRED!)
        >>> config = {"configurable": {"thread_id": "research-session-1"}}
        >>> result = agent.invoke({"messages": [...]}, config=config)
        
    Critical:
        - MUST provide thread_id in config for memory to work!
        - Without thread_id, each call starts fresh
        - MUST provide store parameter for persistence
        
    Token Optimization:
        - MINIMAL: ~120 tokens (fastest, basic guidance)
        - BALANCED: ~180 tokens (default, good balance)
        - DETAILED: ~250 tokens (complex cases, max guidance)
    """
    if store is None:
        store = InMemoryStore()
        if verbose:
            print("⚠️  No store provided, using InMemoryStore (non-persistent)")
    
    return create_deep_agent(
        tools=[search_tool],
        system_prompt=system_prompt,
        store=store,  # Required for StoreBackend
        backend=create_memory_backend,  # Routes /memories/ to persistent storage
    )


def create_research_agent(
    search_tool: Callable,
    system_prompt: str = SIMPLE_RESEARCH_PROMPT
) -> object:
    """
    Create simple research agent WITHOUT memory.
    
    Original V1 agent - backward compatible.
    Each call starts fresh with no context.
    
    Args:
        search_tool: Configured search tool
        system_prompt: Custom prompt (optional, default: ~50 tokens)
        
    Returns:
        DeepAgent (no memory)
        
    Use when:
    ✅ One-off queries
    ✅ Quick fact-checking
    ✅ No persistent storage needed
    
    Don't use when:
    ❌ Multi-session research
    ❌ Iterative work
    → Use create_memory_research_agent() instead
    """
    return create_deep_agent(
        tools=[search_tool],
        system_prompt=system_prompt,
    )


# ==============================================================================
# TOKEN OPTIMIZATION UTILITIES
# ==============================================================================

def get_prompt_token_count(prompt: str, accurate: bool = False) -> int:
    """
    Get token count for prompt.
    
    Args:
        prompt: System prompt string
        accurate: Use tiktoken if available (slower but precise)
        
    Returns:
        Token count
    """
    if accurate and TIKTOKEN_AVAILABLE:
        # Anthropic uses similar tokenizer to GPT-4
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(prompt))
    else:
        # Fast approximation: ~1 token per 4 characters
        return len(prompt) // 4


def compare_prompt_costs(
    queries_per_day: int = 100,
    input_token_price: float = 3.0,  # $ per 1M input tokens
    output_token_estimate: int = 500,  # Average output tokens per query
    output_token_price: float = 15.0,  # $ per 1M output tokens
    accurate_counting: bool = False,
) -> None:
    """
    Compare token costs for different prompt versions.
    
    Args:
        queries_per_day: Expected daily query volume
        input_token_price: Price per 1M input tokens (Claude Sonnet: $3)
        output_token_estimate: Average output tokens per response
        output_token_price: Price per 1M output tokens (Claude Sonnet: $15)
        accurate_counting: Use tiktoken for precise counts (requires tiktoken package)
    """
    prompts = {
        "MINIMAL": MEMORY_RESEARCH_PROMPT_MINIMAL,
        "BALANCED": MEMORY_RESEARCH_PROMPT,
        "DETAILED": MEMORY_RESEARCH_PROMPT_DETAILED,
        "SIMPLE": SIMPLE_RESEARCH_PROMPT,
    }
    
    print("📊 Token Cost Comparison")
    print("=" * 80)
    print(f"Volume: {queries_per_day:,} queries/day")
    print(f"Pricing: ${input_token_price}/1M input, ${output_token_price}/1M output")
    print(f"Avg output: {output_token_estimate} tokens/query")
    if accurate_counting and not TIKTOKEN_AVAILABLE:
        print("⚠️  tiktoken not available, using approximation")
    print()
    
    for name, prompt in prompts.items():
        # Input tokens (system prompt)
        input_tokens = get_prompt_token_count(prompt, accurate=accurate_counting)
        
        # Total tokens per query
        total_input_tokens = input_tokens
        total_output_tokens = output_token_estimate
        total_tokens = total_input_tokens + total_output_tokens
        
        # Calculate costs
        daily_input_tokens = total_input_tokens * queries_per_day
        daily_output_tokens = total_output_tokens * queries_per_day
        
        monthly_input_tokens = daily_input_tokens * 30
        monthly_output_tokens = daily_output_tokens * 30
        
        # Cost calculation
        monthly_input_cost = (monthly_input_tokens / 1_000_000) * input_token_price
        monthly_output_cost = (monthly_output_tokens / 1_000_000) * output_token_price
        monthly_total_cost = monthly_input_cost + monthly_output_cost
        
        print(f"{name:12}")
        print(f"  Input:  {input_tokens:5} tokens | Monthly: ${monthly_input_cost:7.2f}")
        print(f"  Output: {output_token_estimate:5} tokens | Monthly: ${monthly_output_cost:7.2f}")
        print(f"  TOTAL:  {total_tokens:5} tokens | Monthly: ${monthly_total_cost:7.2f}")
        print()
    
    print("=" * 80)


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Factories
    "create_memory_research_agent",
    "create_research_agent",
    "create_shared_store",
    "create_file_store",
    "create_memory_backend",
    # Prompts (for custom usage)
    "MEMORY_RESEARCH_PROMPT_MINIMAL",
    "MEMORY_RESEARCH_PROMPT",
    "MEMORY_RESEARCH_PROMPT_DETAILED",
    "SIMPLE_RESEARCH_PROMPT",
    # Utils
    "get_prompt_token_count",
    "compare_prompt_costs",
]
