"""
Research Agent Factory
Creates configured research agents with internet search capabilities.
"""

from typing import Callable

from deepagents import create_deep_agent


DEFAULT_RESEARCH_PROMPT = """You are an expert researcher.

Your process:
1. Plan your research approach briefly
2. Search precisely for relevant information
3. Synthesize findings into a clear, structured answer
4. Cite sources (URLs) at the end

Be concise but thorough. If a tool fails, explain what you tried and suggest next steps.

## Available Tool: internet_search

Use this to search the web. Parameters:
- query: Search terms
- max_results: Number of results (default: 5)
- topic: 'general' | 'news' | 'finance' (default: 'general')
- include_raw_content: Include full page text (default: False)
"""


def create_research_agent(
    search_tool: Callable,
    system_prompt: str = DEFAULT_RESEARCH_PROMPT
):
    """
    Create a research agent with internet search capability.
    
    Args:
        search_tool: Configured search tool function
        system_prompt: Custom system prompt (optional)
        
    Returns:
        Configured DeepAgent instance
        
    Note:
        The agent will automatically use Anthropic's Claude
        and respect TLS environment variables.
    """
    return create_deep_agent(
        tools=[search_tool],
        system_prompt=system_prompt,
    )
