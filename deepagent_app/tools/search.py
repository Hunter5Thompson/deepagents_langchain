"""
Internet Search Tool
Tavily-based web search for research agents.
"""

from typing import Callable, Literal

from tavily import TavilyClient


class SearchError(Exception):
    """Raised when search operation fails."""
    pass


def create_search_tool(tavily_api_key: str) -> Callable:
    """
    Factory for internet search tool.
    
    Args:
        tavily_api_key: Tavily API key
        
    Returns:
        Configured search function
    """
    client = TavilyClient(api_key=tavily_api_key)
    
    def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False,
    ) -> dict:
        """
        Search the internet for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-20)
            topic: Search category
            include_raw_content: Include full page content
            
        Returns:
            Search results dictionary
            
        Raises:
            SearchError: If search fails
        """
        try:
            return client.search(
                query=query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic,
            )
        except Exception as exc:
            raise SearchError(f"Search failed for query '{query}': {exc}") from exc
    
    return internet_search