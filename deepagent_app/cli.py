from __future__ import annotations
import argparse
import json
import os
from loguru import logger
from settings import settings  # noqa: F401 (ensures env validation on import)
from agent import build_agent

def main() -> int:
    parser = argparse.ArgumentParser(description="DeepAgents Research CLI")
    parser.add_argument("query", help="Research prompt, e.g. 'What is LangGraph?'")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--topic", choices=["general", "news", "finance"], default="general")
    args = parser.parse_args()

    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=os.getenv("LOG_LEVEL", "INFO"))

    agent = build_agent()
    payload = {
        "messages": [
            {"role": "user", "content": f"{args.query} (limit to {args.max_results} results, topic={args.topic})"}
        ]
    }

    logger.info("Invoking agent…")
    result = agent.invoke(payload)
    message = result["messages"][-1].content
    # Try to pretty-print JSON if the agent emitted structured output
    try:
        parsed = json.loads(message)  # some agents return JSON
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except Exception:
        print(message)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
