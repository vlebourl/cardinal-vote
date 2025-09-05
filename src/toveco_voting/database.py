"""Database operations for the ToVéCo voting platform."""

import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, desc, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from .models import Base, DatabaseError, VoteRecord

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for the voting platform."""

    def __init__(self, database_path: str = "votes.db"):
        """Initialize database manager with SQLite database."""
        self.database_path = Path(database_path)
        self.database_url = f"sqlite:///{self.database_path}"

        # Create engine with proper SQLite settings
        self.engine = create_engine(
            self.database_url,
            echo=False,  # Set to True for SQL logging
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )

        # Create sessionmaker
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize database
        self.init_db()

    def init_db(self) -> None:
        """Initialize the database with required tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database initialized at {self.database_path}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}") from e

    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def save_vote(self, voter_first_name: str, voter_last_name: str, ratings: dict[str, int]) -> int:
        """Save a vote to the database."""
        try:
            with self.get_session() as session:
                full_name = f"{voter_first_name} {voter_last_name}"
                vote_record = VoteRecord(
                    voter_first_name=voter_first_name,
                    voter_last_name=voter_last_name,
                    voter_name=full_name,  # Keep for backward compatibility
                    ratings=json.dumps(ratings, sort_keys=True)
                )
                session.add(vote_record)
                session.flush()  # Get the ID before commit
                vote_id = vote_record.id
                logger.info(f"Vote saved for {full_name} with ID {vote_id}")
                return vote_id
        except SQLAlchemyError as e:
            logger.error(f"Failed to save vote: {e}")
            raise DatabaseError(f"Failed to save vote: {e}") from e

    def get_all_votes(self) -> list[dict[str, Any]]:
        """Retrieve all votes from the database."""
        try:
            with self.get_session() as session:
                votes = session.query(VoteRecord).order_by(desc(VoteRecord.timestamp)).all()

                result = []
                for vote in votes:
                    # Handle both new format (first/last name) and legacy format (single name)
                    if hasattr(vote, 'voter_first_name') and vote.voter_first_name:
                        voter_name = f"{vote.voter_first_name} {vote.voter_last_name}"
                        first_name = vote.voter_first_name
                        last_name = vote.voter_last_name
                    else:
                        voter_name = vote.voter_name or "Unknown"
                        # Try to split legacy name for backward compatibility
                        name_parts = voter_name.split(" ", 1)
                        first_name = name_parts[0] if len(name_parts) > 0 else voter_name
                        last_name = name_parts[1] if len(name_parts) > 1 else ""

                    result.append({
                        "id": vote.id,
                        "voter_name": voter_name,
                        "voter_first_name": first_name,
                        "voter_last_name": last_name,
                        "timestamp": vote.timestamp.isoformat(),
                        "ratings": json.loads(vote.ratings)
                    })

                logger.info(f"Retrieved {len(result)} votes from database")
                return result
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve votes: {e}")
            raise DatabaseError(f"Failed to retrieve votes: {e}") from e

    def get_vote_count(self) -> int:
        """Get the total number of votes."""
        try:
            with self.get_session() as session:
                count = session.query(VoteRecord).count()
                return count
        except SQLAlchemyError as e:
            logger.error(f"Failed to get vote count: {e}")
            raise DatabaseError(f"Failed to get vote count: {e}") from e

    def calculate_results(self) -> dict[str, Any]:
        """Calculate voting results with rankings."""
        votes = self.get_all_votes()

        if not votes:
            return {
                "summary": {},
                "total_voters": 0
            }

        # Aggregate ratings per logo
        logo_totals: dict[str, int] = {}
        logo_counts: dict[str, int] = {}

        for vote in votes:
            ratings = vote["ratings"]
            for logo, rating in ratings.items():
                if logo not in logo_totals:
                    logo_totals[logo] = 0
                    logo_counts[logo] = 0
                logo_totals[logo] += rating
                logo_counts[logo] += 1

        # Calculate averages and create summary
        summary = {}
        for logo in logo_totals:
            average = logo_totals[logo] / logo_counts[logo]
            summary[logo] = {
                "average": round(average, 2),
                "total_votes": logo_counts[logo],
                "total_score": logo_totals[logo]
            }

        # Sort by total score (descending) and add rankings
        sorted_logos = sorted(summary.items(), key=lambda x: x[1]['total_score'], reverse=True)
        for rank, (_logo, stats) in enumerate(sorted_logos, 1):
            stats["ranking"] = rank

        # Convert back to dict maintaining order
        ranked_summary = dict(sorted_logos)

        return {
            "summary": ranked_summary,
            "total_voters": len(votes),
            "votes": votes  # Include individual votes for admin view
        }

    def delete_vote_by_id(self, vote_id: int) -> bool:
        """Delete a specific vote by its ID."""
        try:
            with self.get_session() as session:
                vote = session.query(VoteRecord).filter_by(id=vote_id).first()
                if vote:
                    session.delete(vote)
                    session.commit()
                    logger.info(f"Deleted vote with ID: {vote_id}")
                    return True
                else:
                    logger.warning(f"Vote with ID {vote_id} not found")
                    return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete vote {vote_id}: {e}")
            raise DatabaseError(f"Failed to delete vote: {e}") from e

    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

