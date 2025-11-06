from __future__ import annotations
from deepagents import create_deep_agent
from tools import internet_search

RESEARCH_INSTRUCTIONS = """You are an expert researcher.
Use `internet_search` to gather up-to-date information, plan with todos,
and write a concise, well-structured report with sources.
If a tool fails, explain what you tried and suggest next steps."""

def build_agent():
    # Hooks: add subagents/tools later, e.g., write_file/read_file for long contexts.
    agent = create_deep_agent(
        tools=[internet_search],
        system_prompt=RESEARCH_INSTRUCTIONS,
    )
    return agent
