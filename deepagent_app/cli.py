"""
CLI Interface V2 - With Memory Support
Command-line interface for research agents with optional long-term memory.
"""

import argparse
import json
from pathlib import Path
from typing import NoReturn, Optional

import httpx

from deepagent_app.agents.research_v2 import (
    create_file_store,
    create_memory_research_agent,
    create_research_agent,
    create_shared_store,
)
from deepagent_app.config import (
    Config,
    ConfigurationError,
    configure_tls_environment,
    load_config,
)
from deepagent_app.formatters import MarkdownFormatter
from deepagent_app.http_client import create_http_client
from deepagent_app.tools import create_search_tool


def run_research(
    query: str,
    config: Config,
    thread_id: Optional[str] = None,
    use_memory: bool = False,
    save_markdown: bool = True,
    output_dir: Path = Path("outputs/research")
) -> None:
    """
    Execute research query with optional memory.
    
    Args:
        query: Research question
        config: Application configuration
        thread_id: Thread ID for conversation continuity (required if use_memory=True)
        use_memory: Enable long-term memory
        save_markdown: Save results as Markdown
        output_dir: Output directory
        
    Raises:
        ValueError: If use_memory=True but thread_id=None
    """
    if use_memory and not thread_id:
        raise ValueError(
            "thread_id required when use_memory=True\n"
            "Use --thread to specify a session ID"
        )
    
    # Configure environment
    configure_tls_environment(config.cert_path)
    http_client = create_http_client(config.cert_path)
    
    # Initialize formatter
    formatter = MarkdownFormatter(output_dir) if save_markdown else None
    
    try:
        # Create search tool
        search_tool = create_search_tool(config.tavily_api_key)
        
        # Create agent (with or without memory)
        if use_memory:
            store = create_shared_store()  # Or create_file_store() for persistence
            agent = create_memory_research_agent(search_tool, store=store)
            print(f"🧠 Memory enabled (thread: {thread_id})")
        else:
            agent = create_research_agent(search_tool)
            print("📝 One-shot mode (no memory)")
        
        # Prepare config with thread_id
        agent_config = {}
        if thread_id:
            agent_config = {"configurable": {"thread_id": thread_id}}
        
        # Execute research
        print(f"🔍 Research: {query}\n")
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=agent_config
        )
        
        # Extract content
        content = result["messages"][-1].content
        
        # Display in CLI
        print("=" * 80)
        print("📝 RESEARCH RESULTS")
        print("=" * 80)
        
        try:
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            print(formatted)
        except (json.JSONDecodeError, TypeError):
            print(content)
        
        print("=" * 80)
        
        # Save as Markdown (using our formatter, not agent's)
        if formatter:
            metadata = {
                "agent_type": "memory_research" if use_memory else "research",
                "thread_id": thread_id or "none",
                "model": "claude-3-5-sonnet",
            }
            
            filepath = formatter.save_research_report(
                query=query,
                content=content,
                metadata=metadata
            )
            print(f"\n💾 Report saved: {filepath}")
            
    except httpx.ConnectError as exc:
        print(f"❌ Connection Error: {exc}")
        print("   → Check proxy/network")
        raise
    except Exception as exc:
        print(f"❌ Error: {exc.__class__.__name__}: {exc}")
        raise
    finally:
        http_client.close()


def main() -> NoReturn:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DeepAgents Research - With Memory Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # One-shot research (no memory)
  %(prog)s "What is LangGraph?"
  
  # Research with memory (session 1)
  %(prog)s "Research Bitcoin" --memory --thread btc-study
  
  # Continue previous session
  %(prog)s "Bitcoin updates 2024?" --memory --thread btc-study
  
  # New topic, same thread (builds context)
  %(prog)s "Ethereum comparison" --memory --thread btc-study
        """
    )
    
    parser.add_argument(
        "query",
        help="Research question"
    )
    
    # Memory options
    memory_group = parser.add_argument_group("Memory Options")
    memory_group.add_argument(
        "--memory", "-m",
        action="store_true",
        help="Enable long-term memory (requires --thread)"
    )
    memory_group.add_argument(
        "--thread", "-t",
        type=str,
        help="Thread ID for conversation continuity"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save Markdown output"
    )
    output_group.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("outputs/research"),
        help="Output directory (default: outputs/research)"
    )
    
    # Debug
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        config = load_config()
        run_research(
            query=args.query,
            config=config,
            thread_id=args.thread,
            use_memory=args.memory,
            save_markdown=not args.no_save,
            output_dir=args.output_dir
        )
    except ConfigurationError as exc:
        print(f"❌ Configuration Error: {exc}")
        parser.exit(1)
    except ValueError as exc:
        print(f"❌ {exc}")
        parser.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        parser.exit(130)
    except Exception:
        raise


if __name__ == "__main__":
    main()