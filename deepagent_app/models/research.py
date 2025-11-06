"""
Research Models
Database models for storing research queries and results.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from deepagent_app.models.base import Base, IDMixin, TimestampMixin


class ResearchQuery(Base, IDMixin, TimestampMixin):
    """
    Stores research queries submitted by users.

    Attributes:
        id: Primary key
        query: The research query text
        status: Query status (pending, processing, completed, failed)
        created_at: Timestamp when query was created
        updated_at: Timestamp when query was last updated
        results: Related research results
    """

    __tablename__ = "research_queries"

    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    # Relationship to results
    results: Mapped[list["ResearchResult"]] = relationship(
        "ResearchResult",
        back_populates="query",
        cascade="all, delete-orphan",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_research_queries_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ResearchQuery(id={self.id}, query='{self.query[:50]}...', status='{self.status}')>"


class ResearchResult(Base, IDMixin, TimestampMixin):
    """
    Stores individual research results from a query.

    Attributes:
        id: Primary key
        query_id: Foreign key to research_queries
        title: Result title
        content: Full result content
        source_url: URL of the source
        relevance_score: Relevance score (0.0 to 1.0)
        created_at: Timestamp when result was created
        updated_at: Timestamp when result was last updated
        query: Related research query
    """

    __tablename__ = "research_results"

    query_id: Mapped[int] = mapped_column(
        ForeignKey("research_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Relationship to query
    query: Mapped["ResearchQuery"] = relationship(
        "ResearchQuery",
        back_populates="results",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_research_results_query_relevance", "query_id", "relevance_score"),
    )

    def __repr__(self) -> str:
        return f"<ResearchResult(id={self.id}, title='{self.title[:50]}...', query_id={self.query_id})>"
