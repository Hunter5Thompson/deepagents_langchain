"""
DeepAgent App - Corporate Edition
Research agents with corporate proxy support.
"""

__version__ = "0.1.0"

from deepagent_app.agents import create_research_agent
from deepagent_app.config import Config, load_config
from deepagent_app.tools import create_search_tool

__all__ = [
    "Config",
    "load_config",
    "create_search_tool",
    "create_research_agent",
]