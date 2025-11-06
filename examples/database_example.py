"""
Database Usage Example
Demonstrates how to use the PostgreSQL database with the DeepAgent application.
"""

from loguru import logger

from deepagent_app.config import load_config
from deepagent_app.database import initialize_database
from deepagent_app.models import ResearchQuery, ResearchResult


def main():
    """Demonstrate database usage."""

    # Load configuration
    logger.info("Loading configuration...")
    config = load_config()

    # Check if database is configured
    if not config.has_database:
        logger.warning("Database not configured. Set DATABASE_URL in .env file.")
        logger.info("Example: DATABASE_URL=postgresql://user:pass@localhost:5432/dbname")
        return

    # Initialize database
    logger.info("Initializing database...")
    db_manager = initialize_database(config)

    # Perform health check
    logger.info("Checking database health...")
    if not db_manager.health_check():
        logger.error("Database health check failed!")
        return

    logger.success("Database is healthy!")

    # Example 1: Create a research query
    logger.info("\n--- Example 1: Creating a research query ---")
    with db_manager.session() as session:
        query = ResearchQuery(
            query="What is LangGraph and how does it work?",
            status="pending",
        )
        session.add(query)
        session.flush()  # Get the ID without committing
        query_id = query.id
        logger.success(f"Created research query with ID: {query_id}")

    # Example 2: Add research results
    logger.info("\n--- Example 2: Adding research results ---")
    with db_manager.session() as session:
        results = [
            ResearchResult(
                query_id=query_id,
                title="LangGraph Documentation",
                content="LangGraph is a library for building stateful, multi-actor applications...",
                source_url="https://langchain-ai.github.io/langgraph/",
                relevance_score=0.95,
            ),
            ResearchResult(
                query_id=query_id,
                title="LangGraph Tutorial",
                content="Learn how to build agents with LangGraph step by step...",
                source_url="https://python.langchain.com/docs/langgraph",
                relevance_score=0.88,
            ),
        ]
        session.add_all(results)
        logger.success(f"Added {len(results)} research results")

    # Example 3: Update query status
    logger.info("\n--- Example 3: Updating query status ---")
    with db_manager.session() as session:
        query = session.get(ResearchQuery, query_id)
        if query:
            query.status = "completed"
            logger.success(f"Updated query status to: {query.status}")

    # Example 4: Query results
    logger.info("\n--- Example 4: Querying results ---")
    with db_manager.session() as session:
        # Get all completed queries
        completed_queries = (
            session.query(ResearchQuery).filter_by(status="completed").all()
        )
        logger.info(f"Found {len(completed_queries)} completed queries")

        for query in completed_queries:
            logger.info(f"\nQuery ID: {query.id}")
            logger.info(f"Query: {query.query}")
            logger.info(f"Status: {query.status}")
            logger.info(f"Results: {len(query.results)}")

            # Show top results sorted by relevance
            top_results = sorted(
                query.results,
                key=lambda r: r.relevance_score or 0,
                reverse=True,
            )[:3]

            for i, result in enumerate(top_results, 1):
                logger.info(f"\n  Result {i}:")
                logger.info(f"    Title: {result.title}")
                logger.info(f"    Score: {result.relevance_score}")
                logger.info(f"    URL: {result.source_url}")

    # Example 5: Clean up (optional)
    logger.info("\n--- Example 5: Cleanup (commented out) ---")
    logger.info("To delete the test data, uncomment the code below:")
    # with db_manager.session() as session:
    #     query = session.get(ResearchQuery, query_id)
    #     if query:
    #         session.delete(query)  # This will also delete related results (cascade)
    #         logger.success(f"Deleted query and all related results")

    logger.success("\n✅ All examples completed successfully!")


if __name__ == "__main__":
    main()
