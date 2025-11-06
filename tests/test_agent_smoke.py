from __future__ import annotations

from unittest.mock import MagicMock

from deepagent_app.agents import build_agent


def test_agent_has_tools(monkeypatch):
    # Set a dummy API key to allow the agent to be initialized
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    agent = build_agent()
    assert hasattr(agent, "invoke")


def test_invoke_mocked(monkeypatch):
    # Set a dummy API key to allow the agent to be initialized
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

    # Mock the specific method that makes the API call
    mock_create = MagicMock(
        return_value=MagicMock(
            content=[MagicMock(text='{"messages": ["mocked response"]}')]
        )
    )
    monkeypatch.setattr(
        "anthropic.resources.messages.Messages.create", mock_create
    )

    agent = build_agent()

    res = agent.invoke({"messages": [{"role": "user", "content": "Hello"}]})
    assert "messages" in res
    assert isinstance(res["messages"], list)
