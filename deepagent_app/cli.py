# deepagent_app/cli.py
from __future__ import annotations
import argparse, json, os
from loguru import logger

from deepagent_app.settings import settings  # noqa: F401  (env validation on import)
from deepagent_app.agent import build_agent

def main() -> int:
    parser = argparse.ArgumentParser(description="DeepAgents Research CLI")
    parser.add_argument("query", help="Research prompt")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--topic", choices=["general", "news", "finance"], default="general")
    args = parser.parse_args()

    logger.remove()
    logger.add(lambda m: print(m, end=""), level=os.getenv("LOG_LEVEL", "INFO"))

    agent = build_agent()
    payload = {"messages": [{"role": "user",
                             "content": f"{args.query} (limit to {args.max_results} results, topic={args.topic})"}]}
    result = agent.invoke(payload)
    msg = result["messages"][-1].content
    try:
        print(json.dumps(json.loads(msg), indent=2, ensure_ascii=False))
    except Exception:
        print(msg)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
