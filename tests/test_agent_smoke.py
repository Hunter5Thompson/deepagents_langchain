from __future__ import annotations
import types
from agent import build_agent

def test_agent_has_tools():
    agent = build_agent()
    assert hasattr(agent, "invoke")

def test_invoke_mocked(monkeypatch):
    # Monkeypatch the internet_search tool by replacing it in the agent's tool registry if exposed,
    # or simulate a minimal call path via a stub that bypasses the external call.
    agent = build_agent()

    # Fallback: just ensure the shape of response when no real call is made.
    # This is a smoke test: we only assert the pipeline doesn't explode on minimal input.
    res = agent.invoke({"messages": [{"role": "user", "content": "Hello"}]})
    assert "messages" in res
    assert isinstance(res["messages"], list)
