# DeepAgent Research App

Research agent with corporate proxy and SSL certificate support.

## Quick Start
```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run research
uv run python main.py "What is LangGraph?"

# Or use the installed script
uv run research "Analyze OODA loop applications"
```

## Configuration

Create a `.env` file:
```ini
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
COMPANY_CERT_PATH=C:\path\to\company_cert.cer
```

## Development
```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Run tests
uv run pytest
```

## Architecture

- `config.py`: Environment and configuration management
- `http_client.py`: HTTP client factory with cert support
- `tools/`: Tool definitions (search, etc.)
- `agents/`: Agent factories
- `cli.py`: Command-line interface