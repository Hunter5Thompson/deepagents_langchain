# deepagent_app/agent.py
from __future__ import annotations
from deepagents import create_deep_agent
from deepagent_app.tools import internet_search   # <— paket-qualifiziert

RESEARCH_INSTRUCTIONS = """You are an expert researcher.
Use `internet_search` to gather up-to-date info and write a concise report with sources.
If a tool fails, explain what you tried and next steps."""

def build_agent():
    return create_deep_agent(
        tools=[internet_search],
        system_prompt=RESEARCH_INSTRUCTIONS,
    )
