"""
Database Loader
Handles loading transformed data into PostgreSQL database.
"""

import time
from datetime import date
from typing import Any, Dict, List

from logging_config import setup_logging
from sqlalchemy import (
    DECIMAL,
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from ..config import get_settings
from ..models.jikan import AnimeSnapshot

# Only import ETL metrics if we're running in ETL context (not backend)
try:
    from ..metrics_server import etl_metrics

    ETL_METRICS_AVAILABLE = True
except ImportError:
    ETL_METRICS_AVAILABLE = False

logger = setup_logging("etl-loaders-database")


class DatabaseLoader:
    """
    Loads anime snapshots into PostgreSQL database.
    Handles bulk inserts, deduplication, and error recovery.
    """

    def __init__(self):
        self.settings = get_settings()
        self.engine = create_engine(self.settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.metadata = MetaData()

        # Define table structure (matches our SQL schema)
        self.anime_snapshots_table = Table(
            "anime_snapshots",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("mal_id", Integer, nullable=False),
            Column("url", String(500)),
            Column("title", String(500), nullable=False),
            Column("title_english", String(500)),
            Column("title_japanese", String(500)),
            Column("title_synonyms", JSON),
            Column("titles", JSON),
            Column("type", String(50)),
            Column("source", String(100)),
            Column("episodes", Integer),
            Column("status", String(100)),
            Column("airing", Boolean),
            Column("duration", String(100)),
            Column("rating", String(100)),
            Column("score", DECIMAL(4, 2)),
            Column("scored_by", Integer),
            Column("rank", Integer),
            Column("popularity", Integer),
            Column("members", Integer),
            Column("favorites", Integer),
            Column("approved", Boolean),
            Column("season", String(50)),
            Column("year", Integer),
            Column("aired", JSON),
            Column("synopsis", String),
            Column("background", String),
            Column("images", JSON),
            Column("trailer", JSON),
            Column("genres", JSON),
            Column("explicit_genres", JSON),
            Column("themes", JSON),
            Column("demographics", JSON),
            Column("studios", JSON),
            Column("producers", JSON),
            Column("licensors", JSON),
            Column("broadcast", JSON),
            Column("snapshot_type", String(50), nullable=False),
            Column("snapshot_date", Date, nullable=False),
            Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
            Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
        )

    def test_connection(self) -> bool:
        """Test database connection"""
        start_time = time.time()
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                duration = time.time() - start_time
                if ETL_METRICS_AVAILABLE:
                    etl_metrics.record_database_operation("connection_test_success", duration)
                return result.fetchone()[0] == 1
        except Exception as e:
            duration = time.time() - start_time
            if ETL_METRICS_AVAILABLE:
                etl_metrics.record_database_operation("connection_test_error", duration)
            logger.error("Database connection test failed", error=str(e))
            return False

    def load_snapshots(
        self, snapshots: List[AnimeSnapshot], batch_size: int = 100, upsert: bool = True
    ) -> Dict[str, Any]:
        """
        Load anime snapshots into database.

        Args:
            snapshots: List of AnimeSnapshot objects to insert
            batch_size: Number of records to insert per batch
            upsert: Whether to update existing records or skip duplicates

        Returns:
            Dictionary with loading statistics
        """
        start_time = time.time()
        operation_type = "upsert" if upsert else "insert_only"

        stats: Dict[str, Any] = {
            "total_snapshots": len(snapshots),
            "successful_inserts": 0,
            "successful_updates": 0,
            "duplicate_skips": 0,
            "errors": 0,
            "error_details": [],
        }

        if not snapshots:
            logger.info("No snapshots to load")
            # Record empty operation
            duration = time.time() - start_time
            if ETL_METRICS_AVAILABLE:
                etl_metrics.record_database_operation(f"load_snapshots_{operation_type}_empty", duration)
            return stats

        logger.info(
            "Starting database load",
            total_snapshots=len(snapshots),
            batch_size=batch_size,
        )

        try:
            # Process in batches
            for i in range(0, len(snapshots), batch_size):
                batch = snapshots[i : i + batch_size]
                batch_stats = self._load_batch(batch, upsert)

                # Aggregate statistics
                stats["successful_inserts"] += batch_stats["successful_inserts"]
                stats["successful_updates"] += batch_stats["successful_updates"]
                stats["duplicate_skips"] += batch_stats["duplicate_skips"]
                stats["errors"] += batch_stats["errors"]
                stats["error_details"].extend(batch_stats["error_details"])

                logger.info(
                    "Batch processed",
                    batch_number=i // batch_size + 1,  # 1-indexed
                    batch_size=len(batch),
                    successful=batch_stats["successful_inserts"],
                    errors=batch_stats["errors"],
                    skips=batch_stats["duplicate_skips"],
                )

            # Record successful operation metrics
            duration = time.time() - start_time
            if ETL_METRICS_AVAILABLE:
                etl_metrics.record_database_operation(f"load_snapshots_{operation_type}_success", duration)

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            if ETL_METRICS_AVAILABLE:
                etl_metrics.record_database_operation(f"load_snapshots_{operation_type}_error", duration)
            logger.error("Database load failed", error=str(e))
            raise

        logger.info("Database load completed", **stats)
        return stats

    def _load_batch(self, batch: List[AnimeSnapshot], upsert: bool) -> Dict[str, Any]:
        """Load a single batch of snapshots"""
        batch_stats: Dict[str, Any] = {
            "successful_inserts": 0,
            "successful_updates": 0,
            "duplicate_skips": 0,
            "errors": 0,
            "error_details": [],
        }

        session = self.SessionLocal()
        try:
            for snapshot in batch:
                try:
                    existing = session.execute(
                        text(
                            """
                            SELECT id FROM anime_snapshots
                            WHERE mal_id = :mal_id
                            AND snapshot_type = :snapshot_type
                            AND snapshot_date = :snapshot_date
                        """
                        ),
                        {
                            "mal_id": snapshot.mal_id,
                            "snapshot_type": snapshot.snapshot_type,
                            "snapshot_date": snapshot.snapshot_date,
                        },
                    ).fetchone()

                    # Check for existing record (prevent duplicates)
                    if not upsert:
                        if existing:
                            batch_stats["duplicate_skips"] += 1
                            continue  # Skip duplicate

                    # Convert snapshot to dictionary
                    snapshot_dict = self._snapshot_to_dict(snapshot)

                    # Try to insert or update
                    if upsert:
                        # Use PostgreSQL UPSERT (ON CONFLICT)
                        upsert_start_time = time.time()
                        insert_stmt = text(
                            """
                            INSERT INTO anime_snapshots (
                                mal_id, url, title, title_english, title_japanese, title_synonyms, titles,
                                type, source, episodes, status, airing, duration, rating, score, scored_by,
                                rank, popularity, members, favorites, approved, season, year, aired,
                                synopsis, background, images, trailer, genres, explicit_genres, themes,
                                demographics, studios, producers, licensors, broadcast,
                                snapshot_type, snapshot_date
                            ) VALUES (
                                :mal_id, :url, :title, :title_english, :title_japanese, :title_synonyms, :titles,
                                :type, :source, :episodes, :status, :airing, :duration, :rating, :score, :scored_by,
                                :rank, :popularity, :members, :favorites, :approved, :season, :year, :aired,
                                :synopsis, :background, :images, :trailer, :genres, :explicit_genres, :themes,
                                :demographics, :studios, :producers, :licensors, :broadcast,
                                :snapshot_type, :snapshot_date
                            )
                            ON CONFLICT (mal_id, snapshot_type, snapshot_date)
                            DO UPDATE SET
                                title = EXCLUDED.title,
                                score = EXCLUDED.score,
                                rank = EXCLUDED.rank,
                                popularity = EXCLUDED.popularity,
                                members = EXCLUDED.members,
                                favorites = EXCLUDED.favorites,
                                updated_at = CURRENT_TIMESTAMP
                        """
                        )

                        session.execute(insert_stmt, snapshot_dict)
                        upsert_duration = time.time() - upsert_start_time

                        if existing:
                            batch_stats["successful_updates"] += 1
                            if ETL_METRICS_AVAILABLE:
                                etl_metrics.record_database_operation("snapshot_update", upsert_duration)
                        else:
                            batch_stats["successful_inserts"] += 1
                            if ETL_METRICS_AVAILABLE:
                                etl_metrics.record_database_operation("snapshot_insert", upsert_duration)

                    # Just insert without checking for duplicates
                    else:
                        # Simple insert
                        insert_start_time = time.time()
                        insert_stmt = text(
                            """
                            INSERT INTO anime_snapshots (
                                mal_id, url, title, title_english, title_japanese, title_synonyms, titles,
                                type, source, episodes, status, airing, duration, rating, score, scored_by,
                                rank, popularity, members, favorites, approved, season, year, aired,
                                synopsis, background, images, trailer, genres, explicit_genres, themes,
                                demographics, studios, producers, licensors, broadcast,
                                snapshot_type, snapshot_date
                            ) VALUES (
                                :mal_id, :url, :title, :title_english, :title_japanese, :title_synonyms, :titles,
                                :type, :source, :episodes, :status, :airing, :duration, :rating, :score, :scored_by,
                                :rank, :popularity, :members, :favorites, :approved, :season, :year, :aired,
                                :synopsis, :background, :images, :trailer, :genres, :explicit_genres, :themes,
                                :demographics, :studios, :producers, :licensors, :broadcast,
                                :snapshot_type, :snapshot_date
                            )
                        """
                        )
                        session.execute(insert_stmt, snapshot_dict)
                        insert_duration = time.time() - insert_start_time
                        batch_stats["successful_inserts"] += 1
                        if ETL_METRICS_AVAILABLE:
                            etl_metrics.record_database_operation("snapshot_insert_only", insert_duration)

                except SQLAlchemyError as e:  # DB-related issues
                    batch_stats["errors"] += 1
                    error_detail = {
                        "mal_id": snapshot.mal_id,
                        "title": snapshot.title,
                        "error": str(e),
                    }
                    batch_stats["error_details"].append(error_detail)
                    logger.warning("Database insert error", **error_detail)

                except Exception as e:  # Bad data / logic issues
                    batch_stats["errors"] += 1
                    error_detail = {
                        "mal_id": snapshot.mal_id,
                        "title": snapshot.title,
                        "error": f"Unexpected error: {str(e)}",
                    }
                    batch_stats["error_details"].append(error_detail)
                    logger.error("Unexpected insert error", **error_detail)

            # Commit the batch
            session.commit()

        # If DB connection dies at any point, cancel the whole batch
        except Exception as e:
            session.rollback()
            logger.error("Batch processing failed", error=str(e))
            batch_stats["errors"] = len(batch)

        # Successfully processed batch, close session
        finally:
            session.close()

        return batch_stats

    def _snapshot_to_dict(self, snapshot: AnimeSnapshot) -> Dict[str, Any]:
        """Convert AnimeSnapshot to dictionary for database insertion"""
        import json

        def json_serialize(obj):
            """Convert dict/list to JSON string, leave other types as-is"""
            if obj is None:
                return None
            elif isinstance(obj, (dict, list)):
                return json.dumps(obj)
            else:
                return obj

        return {
            "mal_id": snapshot.mal_id,
            "url": snapshot.url,
            "title": snapshot.title,
            "title_english": snapshot.title_english,
            "title_japanese": snapshot.title_japanese,
            "title_synonyms": json_serialize(snapshot.title_synonyms),
            "titles": json_serialize(snapshot.titles),
            "type": snapshot.type,
            "source": snapshot.source,
            "episodes": snapshot.episodes,
            "status": snapshot.status,
            "airing": snapshot.airing,
            "duration": snapshot.duration,
            "rating": snapshot.rating,
            "score": float(snapshot.score) if snapshot.score else None,
            "scored_by": snapshot.scored_by,
            "rank": snapshot.rank,
            "popularity": snapshot.popularity,
            "members": snapshot.members,
            "favorites": snapshot.favorites,
            "approved": snapshot.approved,
            "season": snapshot.season,
            "year": snapshot.year,
            "aired": json_serialize(snapshot.aired),
            "synopsis": snapshot.synopsis,
            "background": snapshot.background,
            "images": json_serialize(snapshot.images),
            "trailer": json_serialize(snapshot.trailer),
            "genres": json_serialize(snapshot.genres),
            "explicit_genres": json_serialize(snapshot.explicit_genres),
            "themes": json_serialize(snapshot.themes),
            "demographics": json_serialize(snapshot.demographics),
            "studios": json_serialize(snapshot.studios),
            "producers": json_serialize(snapshot.producers),
            "licensors": json_serialize(snapshot.licensors),
            "broadcast": json_serialize(snapshot.broadcast),
            "snapshot_type": snapshot.snapshot_type,
            "snapshot_date": snapshot.snapshot_date,
        }

    def get_latest_snapshot_date(self, snapshot_type: str) -> date:
        """Get the date of the latest snapshot for a given type"""
        session = self.SessionLocal()
        try:
            result = session.execute(
                text("SELECT MAX(snapshot_date) FROM anime_snapshots WHERE snapshot_type = :type"),
                {"type": snapshot_type},
            ).fetchone()

            return result[0] if result[0] else date.today()

        finally:
            session.close()

    def cleanup_old_snapshots(self, snapshot_type: str, keep_days: int = 30) -> int:
        """Remove old snapshots to prevent database bloat"""
        session = self.SessionLocal()
        try:
            result = session.execute(
                text(
                    """
                    DELETE FROM anime_snapshots
                    WHERE snapshot_type = :type
                    AND snapshot_date < CURRENT_DATE - INTERVAL ':days days'
                """
                ),
                {"type": snapshot_type, "days": keep_days},
            )

            deleted_count = result.rowcount
            session.commit()

            logger.info(
                "Cleaned up old snapshots",
                snapshot_type=snapshot_type,
                deleted_count=deleted_count,
            )

            return deleted_count

        except Exception as e:
            session.rollback()
            logger.error("Failed to cleanup old snapshots", error=str(e))
            return 0

        finally:
            session.close()


def create_loader() -> DatabaseLoader:
    """Create a new DatabaseLoader instance"""
    return DatabaseLoader()
