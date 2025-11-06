"""
CLI Interface
Command-line interface for the research agent.
"""

import argparse
import json
from typing import NoReturn

import httpx

from deepagent_app.agents import create_research_agent
from deepagent_app.config import (
    Config,
    ConfigurationError,
    configure_tls_environment,
    load_config,
)
from deepagent_app.http_client import create_http_client
from deepagent_app.tools import create_search_tool


def run_research(query: str, config: Config) -> None:
    """
    Execute a research query.
    
    Args:
        query: Research question
        config: Application configuration
        
    Raises:
        Various exceptions for network/API errors
    """
    # Configure TLS environment
    configure_tls_environment(config.cert_path)
    
    # Create HTTP client (for future use, if needed)
    http_client = create_http_client(config.cert_path)
    
    try:
        # Create tools and agent
        search_tool = create_search_tool(config.tavily_api_key)
        agent = create_research_agent(search_tool)
        
        # Execute research
        print(f"🔍 Research: {query}\n")
        result = agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        # Display results
        content = result["messages"][-1].content
        
        # Try to pretty-print if JSON
        try:
            parsed = json.loads(content)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except (json.JSONDecodeError, TypeError):
            print(content)
            
    except httpx.ConnectError as exc:
        print(f"❌ Connection Error: {exc}")
        print("   → Check proxy settings and network connection")
        raise
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:200] if hasattr(exc.response, 'text') else ''
        print(f"❌ HTTP Error: {exc.response.status_code}")
        print(f"   → Response: {body}")
        raise
    except Exception as exc:
        print(f"❌ Unexpected Error: {exc.__class__.__name__}: {exc}")
        raise
    finally:
        http_client.close()


def main() -> NoReturn:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DeepAgents Research Agent - Corporate Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is LangGraph?"
  %(prog)s "Analyze OODA loop in modern warfare"
  %(prog)s "Compare microservices vs monolithic architectures"
        """
    )
    parser.add_argument(
        "query",
        help="Research question or prompt"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        config = load_config()
        run_research(args.query, config)
    except ConfigurationError as exc:
        print(f"❌ Configuration Error: {exc}")
        parser.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        parser.exit(130)
    except Exception:
        # Let the exception propagate for full traceback
        raise


if __name__ == "__main__":
    main()