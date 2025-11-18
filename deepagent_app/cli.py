"""
CLI Interface V2 - With Memory Support
Command-line interface for research agents with optional long-term memory.
"""

import argparse
import json
import time
from pathlib import Path
from typing import NoReturn, Optional

import httpx

from deepagent_app.agents.research_v2 import (
    create_file_store,
    create_memory_research_agent,
    create_research_agent,
    create_shared_store,
)
from deepagent_app.agents.research_v3 import (
    create_parallel_shared_research_agent,
    create_simple_sequential_research_agent,
)
from deepagent_app.config import (
    Config,
    ConfigurationError,
    configure_tls_environment,
    load_config,
)
from deepagent_app.formatters import MarkdownFormatter
from deepagent_app.http_client import create_http_client
from deepagent_app.telemetry import create_langfuse_callbacks
from deepagent_app.tools import create_search_tool

try:  # Anthropic SDK exposes transient overload/rate limit errors here
    from anthropic._exceptions import OverloadedError as AnthropicOverloadedError
except Exception:  # pragma: no cover - defensive import for optional dependency
    AnthropicOverloadedError = None

try:
    from anthropic._exceptions import RateLimitError as AnthropicRateLimitError
except Exception:  # pragma: no cover - defensive import for optional dependency
    AnthropicRateLimitError = None


def _extract_retry_after_seconds(error: Exception) -> Optional[int]:
    """Best-effort extraction of a retry delay from Anthropic errors."""

    response = getattr(error, "response", None)
    if response is None:
        return None

    headers = getattr(response, "headers", None)
    if headers is None:
        return None

    retry_after = headers.get("retry-after") or headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        return int(float(retry_after))
    except (TypeError, ValueError):
        return None


def _invoke_with_retries(
    agent,
    payload,
    *,
    config,
    callbacks = None,
    max_attempts: int = 3,
) -> object:
    """Invoke an agent with retries for transient Anthropic overloads or rate limits."""

    retryable = tuple(
        error
        for error in (AnthropicOverloadedError, AnthropicRateLimitError)
        if error is not None
    )
    attempt = 0
    while True:
        attempt += 1
        try:
            return agent.invoke(payload, config=config, callbacks=callbacks)
        except Exception as exc:  # pragma: no cover - depends on Anthropic runtime
            if not retryable or not isinstance(exc, retryable):
                raise

            if attempt >= max_attempts:
                raise

            delay = 2 ** (attempt - 1)
            reason = "Anthropic transient error"

            if AnthropicOverloadedError and isinstance(exc, AnthropicOverloadedError):
                reason = "Anthropic overloaded"

            if AnthropicRateLimitError and isinstance(exc, AnthropicRateLimitError):
                reason = "Anthropic rate limit hit"
                retry_after = _extract_retry_after_seconds(exc)
                if retry_after:
                    delay = max(delay, retry_after)

            print(
                "⚠️  "
                f"{reason}. Retrying in {delay}s (attempt {attempt + 1}/{max_attempts})"
            )
            time.sleep(delay)


def _build_agent(
    agent_type: str,
    search_tool,
    *,
    use_memory: bool,
):
    """Create agent instance and return tuple (agent, memory_enabled, label)."""

    if agent_type == "v2":
        if use_memory:
            store = create_shared_store()
            agent = create_memory_research_agent(search_tool, store=store)
            return agent, True, "🧠 Memory-enabled (v2)"

        agent = create_research_agent(search_tool)
        return agent, False, "📝 One-shot mode (v2)"

    store = create_shared_store()
    if agent_type == "simple-sequential":
        agent = create_simple_sequential_research_agent(
            search_tool,
            store=store,
        )
        return agent, True, "🧠 Simple sequential workflow (v3)"

    if agent_type == "parallel-shared":
        agent = create_parallel_shared_research_agent(
            search_tool,
            store=store,
        )
        return agent, True, "🧠 Parallel shared workflow (v3)"

    raise ValueError(f"Unknown agent type: {agent_type}")


def run_research(
    query: str,
    config: Config,
    *,
    thread_id: Optional[str] = None,
    use_memory: bool = False,
    save_markdown: bool = True,
    output_dir: Path = Path("outputs/research"),
    agent_type: str = "v2",
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
    memory_required = use_memory
    if agent_type != "v2":
        memory_required = True

    if memory_required and not thread_id:
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
        agent, memory_enabled, label = _build_agent(
            agent_type,
            search_tool,
            use_memory=use_memory,
        )

        if memory_enabled:
            print(f"{label} (thread: {thread_id})")
        else:
            print(label)

        # Prepare config with thread_id
        agent_config = {}
        if thread_id:
            agent_config = {"configurable": {"thread_id": thread_id}}

        callbacks = create_langfuse_callbacks(
            config,
            agent_type=agent_type,
            thread_id=thread_id,
            query=query,
        )
        if callbacks:
            print("📡 Langfuse tracing enabled for this run")
        
        # Execute research
        print(f"🔍 Research: {query}\n")
        payload = {"messages": [{"role": "user", "content": query}]}
        result = _invoke_with_retries(
            agent,
            payload,
            config=agent_config,
            callbacks=callbacks or None,
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
        description="DeepAgents Research - With Memory & Subagent Workflows",
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

  # V3 sequential coordinator (memory required)
  %(prog)s "Was sind 3D Gaussian Splatting?" --workflow simple-sequential --thread 3dgs-research

  # V3 parallel coordinator (memory required)
  %(prog)s "Analyse AI chip market" --workflow parallel-shared --thread ai-chips
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

    parser.add_argument(
        "--workflow",
        choices=("v2", "simple-sequential", "parallel-shared"),
        default="v2",
        help=(
            "Select agent workflow: 'v2' (default), 'simple-sequential' for the "
            "V3 baton-pass coordinator, or 'parallel-shared' for the V3 "
            "multi-specialist team."
        ),
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
            output_dir=args.output_dir,
            agent_type=args.workflow,
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