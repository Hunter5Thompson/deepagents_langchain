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

# Optional: PostgreSQL Database
DATABASE_URL=postgresql://deepagent:password@localhost:5432/deepagent_db
```

### Database Setup (Optional)

The application supports PostgreSQL for storing research queries and results.

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run database migrations
uv run alembic upgrade head
```

See [Database Documentation](docs/DATABASE.md) for detailed setup and usage instructions.

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
- `database.py`: Database connection and session management
- `models/`: SQLAlchemy ORM models
- `tools/`: Tool definitions (search, etc.)
- `agents/`: Agent factories
- `cli.py`: Command-line interface
- `alembic/`: Database migrations

## Documentation

- [Database Setup and Usage](docs/DATABASE.md) - PostgreSQL integration guide