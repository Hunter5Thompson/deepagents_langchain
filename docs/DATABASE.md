# PostgreSQL Database Integration

Diese Anleitung beschreibt, wie Sie die PostgreSQL-Datenbank für die DeepAgent-Anwendung einrichten und verwenden.

## Übersicht

Die Anwendung verwendet:
- **PostgreSQL** als Datenbank
- **SQLAlchemy 2.0** als ORM
- **Alembic** für Datenbankmigrationen
- **psycopg2-binary** als PostgreSQL-Adapter

## Schnellstart

### 1. Datenbank mit Docker starten

```bash
# PostgreSQL starten
docker-compose up -d postgres

# PostgreSQL mit pgAdmin starten (optional, für Development)
docker-compose --profile dev up -d
```

Die Datenbank läuft dann auf:
- **Host**: localhost
- **Port**: 5432
- **Database**: deepagent_db
- **User**: deepagent
- **Password**: password

pgAdmin (optional) ist verfügbar unter:
- **URL**: http://localhost:5050
- **Email**: admin@deepagent.local
- **Password**: admin

### 2. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env` Datei:

```bash
cp .env.example .env
```

Setzen Sie die `DATABASE_URL`:

```ini
DATABASE_URL=postgresql://deepagent:password@localhost:5432/deepagent_db
```

### 3. Abhängigkeiten installieren

```bash
uv sync
```

### 4. Datenbank-Migrationen ausführen

```bash
# Erste Migration erstellen
uv run alembic revision --autogenerate -m "Initial tables"

# Migration ausführen
uv run alembic upgrade head
```

## Datenbankmodelle

### ResearchQuery

Speichert Research-Anfragen:

```python
from deepagent_app.models import ResearchQuery

query = ResearchQuery(
    query="What is LangGraph?",
    status="pending"
)
```

**Felder:**
- `id`: Primary Key
- `query`: Der Suchtext
- `status`: Status (pending, processing, completed, failed)
- `created_at`: Erstellungszeitpunkt
- `updated_at`: Aktualisierungszeitpunkt

### ResearchResult

Speichert einzelne Suchergebnisse:

```python
from deepagent_app.models import ResearchResult

result = ResearchResult(
    query_id=1,
    title="LangGraph Documentation",
    content="LangGraph is...",
    source_url="https://example.com",
    relevance_score=0.95
)
```

**Felder:**
- `id`: Primary Key
- `query_id`: Foreign Key zu ResearchQuery
- `title`: Titel des Ergebnisses
- `content`: Vollständiger Inhalt
- `source_url`: URL der Quelle
- `relevance_score`: Relevanz-Score (0.0 bis 1.0)

## Verwendung im Code

### Database Manager initialisieren

```python
from deepagent_app.config import load_config
from deepagent_app.database import initialize_database

# Konfiguration laden
config = load_config()

# Datenbank initialisieren (wenn konfiguriert)
if config.has_database:
    db_manager = initialize_database(config)
```

### Session verwenden

```python
from deepagent_app.database import get_database_manager
from deepagent_app.models import ResearchQuery

db_manager = get_database_manager()

# Mit Context Manager (empfohlen)
with db_manager.session() as session:
    query = ResearchQuery(query="Test query", status="pending")
    session.add(query)
    # Commit erfolgt automatisch bei Verlassen des Context Managers

# Query ausführen
with db_manager.session() as session:
    queries = session.query(ResearchQuery).filter_by(status="completed").all()
    for query in queries:
        print(f"{query.id}: {query.query}")
```

### Health Check

```python
from deepagent_app.database import get_database_manager

db_manager = get_database_manager()
if db_manager.health_check():
    print("✅ Database is healthy")
else:
    print("❌ Database connection failed")
```

## Alembic-Migrationen

### Neue Migration erstellen

```bash
# Automatische Migration basierend auf Model-Änderungen
uv run alembic revision --autogenerate -m "Add new field to research_query"

# Manuelle Migration
uv run alembic revision -m "Add custom index"
```

### Migration ausführen

```bash
# Zur neuesten Version upgraden
uv run alembic upgrade head

# Zu einer bestimmten Revision upgraden
uv run alembic upgrade <revision_id>

# Um eine Version zurück
uv run alembic downgrade -1

# Zur Basis zurück
uv run alembic downgrade base
```

### Migration-Historie anzeigen

```bash
# Alle Migrationen anzeigen
uv run alembic history

# Aktuelle Revision anzeigen
uv run alembic current
```

## Best Practices

### 1. Verwenden Sie Context Manager

Immer den `session()` Context Manager verwenden für automatisches Cleanup:

```python
with db_manager.session() as session:
    # Ihre Datenbankoperationen
    pass
```

### 2. Error Handling

```python
from deepagent_app.database import get_database_manager
from sqlalchemy.exc import SQLAlchemyError

db_manager = get_database_manager()

try:
    with db_manager.session() as session:
        # Datenbankoperationen
        pass
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    # Fehlerbehandlung
```

### 3. Connection Pooling

Der DatabaseManager verwendet Connection Pooling:
- **Pool Size**: 5 Verbindungen
- **Max Overflow**: 10 zusätzliche Verbindungen
- **Pool Pre-Ping**: Überprüft Verbindungen vor Verwendung
- **Pool Recycle**: Recycelt Verbindungen nach 1 Stunde

### 4. Transaktionen

Explizite Transaktionen wenn nötig:

```python
with db_manager.session() as session:
    try:
        session.begin()
        # Multiple Operationen
        query = ResearchQuery(query="Test")
        session.add(query)
        # Weitere Operationen
        session.commit()
    except Exception:
        session.rollback()
        raise
```

## Produktions-Setup

### 1. Sichere Credentials

Verwenden Sie niemals hardcodierte Passwörter in Produktion:

```bash
# Verwenden Sie starke Passwörter
DATABASE_URL=postgresql://user:secure_password@db-host:5432/dbname
```

### 2. SSL-Verbindungen

Für Produktionsumgebungen SSL aktivieren:

```python
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 3. Connection Limits

Passen Sie Pool-Größe an Ihre Anforderungen an in `database.py`:

```python
self._engine = create_engine(
    self.database_url,
    pool_size=20,           # Erhöhen für High-Traffic
    max_overflow=40,
    pool_recycle=3600,
)
```

### 4. Monitoring

Implementieren Sie Monitoring für:
- Connection Pool Status
- Query Performance
- Error Rates
- Health Checks

## Troubleshooting

### Verbindungsfehler

```bash
# PostgreSQL-Status prüfen
docker-compose ps postgres

# Logs anzeigen
docker-compose logs postgres

# In PostgreSQL-Container verbinden
docker exec -it deepagent_postgres psql -U deepagent -d deepagent_db
```

### Migration-Fehler

```bash
# Aktuelle Revision prüfen
uv run alembic current

# Zu bekannter guter Revision zurück
uv run alembic downgrade <revision_id>

# Migration neu ausführen
uv run alembic upgrade head
```

### Datenbank zurücksetzen (Development)

```bash
# WARNUNG: Löscht alle Daten!
docker-compose down -v
docker-compose up -d postgres
uv run alembic upgrade head
```

## Weitere Ressourcen

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
