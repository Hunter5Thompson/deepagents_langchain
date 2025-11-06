from __future__ import annotations
import os
from typing import Literal
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tavily import TavilyClient

class ToolError(RuntimeError):
    """Wrap external tool failures with a clear error type."""

def _mk_tavily() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ToolError("TAVILY_API_KEY not set")
    return TavilyClient(api_key=api_key)

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=8),
    retry=retry_if_exception_type(Exception),
)
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search via Tavily with basic retries."""
    try:
        client = _mk_tavily()
        return client.search(
            query=query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
    except Exception as exc:
        # sanitize & rethrow for the agent
        raise ToolError(f"Search failed: {exc}") from exc
