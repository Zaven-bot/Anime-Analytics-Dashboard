"""
Analytics Service
Backend analytics service with direct database access
"""

import json
import time
from typing import Any, Dict, List, Optional, cast

import redis.asyncio as redis
import structlog
from logging_config import setup_logging
logger = setup_logging("backend-services-analytics")
from ..database import database_engine, get_database_session
from ..metrics import metrics

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """
    Analytics service with direct database access for backend API.
    Uses dependency injection for Redis client.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.engine = database_engine
        self.redis_client = redis_client

        # Cache TTL settings (in seconds) - domain-specific
        self.cache_ttl = {
            "database_stats": 300,  # 5 minutes
            "top_rated": 600,  # 10 minutes
            "genre_distribution": 1800,  # 30 minutes (expensive query)
            "seasonal_trends": 900,  # 15 minutes
        }

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate consistent cache keys"""
        key_parts = [f"anime:{prefix}"]
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        return ":".join(key_parts)

    async def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get data from cache - returns Any type since different methods cache different structures"""
        if not self.redis_client:
            logger.debug("Redis client not available, skipping cache")
            metrics.record_cache_operation("miss", "no_client")
            return None

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.info("Cache hit", cache_key=cache_key)
                # Determine cache key type for metrics
                cache_type = cache_key.split(":")[1] if ":" in cache_key else "unknown"
                metrics.record_cache_operation("hit", cache_type)
                return json.loads(cached_data)
            else:
                logger.info("Cache miss", cache_key=cache_key)
                cache_type = cache_key.split(":")[1] if ":" in cache_key else "unknown"
                metrics.record_cache_operation("miss", cache_type)
                return None
        except Exception as e:
            logger.warning("Cache read failed", cache_key=cache_key, error=str(e))
            cache_type = cache_key.split(":")[1] if ":" in cache_key else "unknown"
            metrics.record_cache_operation("error", cache_type)
            return None

    async def _set_cached_data(self, cache_key: str, data: Any, ttl: int):
        """Set data in cache with TTL - accepts Any data type for flexible caching"""
        if not self.redis_client:
            logger.debug("Redis client not available, skipping cache write")
            return

        try:
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data, default=str),  # default=str handles dates
            )
            logger.info("Data cached", cache_key=cache_key, ttl=ttl)
        except Exception as e:
            logger.warning("Cache write failed", cache_key=cache_key, error=str(e))

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics (with caching)"""
        cache_key = self._get_cache_key("database_stats")

        # Try cache first
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Cache miss - query database
        start_time = time.time()
        session = get_database_session()
        try:
            # Total snapshots
            total_query = text("SELECT COUNT(*) FROM anime_snapshots")
            total_snapshots = session.execute(total_query).scalar()

            # Snapshots by type
            type_query = text(
                """
                SELECT snapshot_type, COUNT(*) as count, MAX(snapshot_date) as latest_date
                FROM anime_snapshots
                GROUP BY snapshot_type
                ORDER BY count DESC
            """
            )
            snapshot_types = []
            for row in session.execute(type_query):
                snapshot_types.append(
                    {
                        "type": row.snapshot_type,
                        "count": row.count,
                        "latest_date": (row.latest_date.isoformat() if row.latest_date else None),
                    }
                )

            # Latest snapshot date overall
            latest_query = text("SELECT MAX(snapshot_date) FROM anime_snapshots")
            latest_date = session.execute(latest_query).scalar()

            result = {
                "total_snapshots": total_snapshots,
                "snapshot_types": snapshot_types,
                "latest_snapshot_date": (latest_date.isoformat() if latest_date else None),
                "unique_anime": self._get_unique_anime_count(session),
            }

            # Record metrics for query execution
            query_duration = time.time() - start_time
            metrics.record_database_query("database_stats", query_duration)

            # Cache the result
            await self._set_cached_data(cache_key, result, self.cache_ttl["database_stats"])
            return result

        except Exception as e:
            logger.error("Failed to get database stats", error=str(e))
            # Record error in metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("database_stats_error", query_duration)
            raise
        finally:
            session.close()

    async def get_top_rated_anime(self, limit: int = 10, snapshot_type: str = "top") -> List[Dict[str, Any]]:
        """Get top-rated anime from latest snapshots"""
        cache_key = self._get_cache_key("top_rated", snapshot_type=snapshot_type, limit=limit)

        # Try cache first
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Cache miss - query database
        start_time = time.time()
        session = get_database_session()
        try:
            # Get latest snapshot date for the type
            latest_date_query = text(
                """
                SELECT MAX(snapshot_date)
                FROM anime_snapshots
                WHERE snapshot_type = :snapshot_type
            """
            )
            latest_date = session.execute(latest_date_query, {"snapshot_type": snapshot_type}).scalar()

            if not latest_date:
                query_duration = time.time() - start_time
                metrics.record_database_query("top_rated_no_data", query_duration)
                return []

            # Get top anime from latest snapshot
            query = text(
                """
                SELECT mal_id, title, score, rank, popularity, genres, studios
                FROM anime_snapshots
                WHERE snapshot_type = :snapshot_type
                  AND snapshot_date = :snapshot_date
                  AND score IS NOT NULL
                ORDER BY score DESC, rank ASC
                LIMIT :limit
            """
            )

            results = []
            for row in session.execute(
                query,
                {
                    "snapshot_type": snapshot_type,
                    "snapshot_date": latest_date,
                    "limit": limit,
                },
            ):
                # Parse JSON fields safely
                genres = self._parse_json_field(row.genres)
                studios = self._parse_json_field(row.studios)

                results.append(
                    {
                        "mal_id": row.mal_id,
                        "title": row.title,
                        "score": float(row.score) if row.score else None,
                        "rank": row.rank,
                        "popularity": row.popularity,
                        "genres": [g.get("name", "") for g in genres if isinstance(g, dict) and "name" in g],
                        "studios": [s.get("name", "") for s in studios if isinstance(s, dict) and "name" in s],
                    }
                )

            # Record successful query metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("top_rated", query_duration)

            # Cache the result
            await self._set_cached_data(cache_key, results, self.cache_ttl["top_rated"])
            return results

        except Exception as e:
            logger.error("Failed to get top rated anime", error=str(e))
            # Record error in metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("top_rated_error", query_duration)
            raise
        finally:
            session.close()

    async def get_genre_distribution(self, snapshot_type: str = "top") -> Dict[str, Any]:
        """Get genre distribution with both coverage and frequency percentages"""
        cache_key = self._get_cache_key("genre_distribution", snapshot_type=snapshot_type)
        # Try cache first
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Cache miss - run expensive query
        start_time = time.time()
        session = get_database_session()
        try:
            # Get latest snapshot date
            latest_date_query = text(
                """
                SELECT MAX(snapshot_date)
                FROM anime_snapshots
                WHERE snapshot_type = :snapshot_type
            """
            )
            latest_date = session.execute(latest_date_query, {"snapshot_type": snapshot_type}).scalar()

            if not latest_date:
                query_duration = time.time() - start_time
                metrics.record_database_query("genre_distribution_no_data", query_duration)
                return {
                    "genres": [],
                    "total_anime": 0,
                    "total_genre_mentions": 0,
                    "snapshot_date": None,
                }

            # Get all anime with genres from latest snapshot
            query = text(
                """
                SELECT genres, mal_id
                FROM anime_snapshots
                WHERE snapshot_type = :snapshot_type
                  AND snapshot_date = :snapshot_date
                  AND genres IS NOT NULL
            """
            )

            # Two different counting approaches:
            # 1. anime_count: How many unique anime have this genre (for coverage percentage)
            # 2. mention_count: How many times this genre appears total (for frequency percentage)
            genre_anime_sets: Dict[str, set] = {}  # Track unique anime per genre
            genre_mention_counts: Dict[str, int] = {}  # Count total mentions per genre
            total_anime = 0
            total_genre_mentions = 0

            for row in session.execute(query, {"snapshot_type": snapshot_type, "snapshot_date": latest_date}):
                total_anime += 1
                genres = self._parse_json_field(row.genres)

                # Track genres for this anime
                anime_genres = set()
                for genre_obj in genres:
                    if isinstance(genre_obj, dict) and "name" in genre_obj:
                        genre_name = genre_obj["name"]
                        anime_genres.add(genre_name)

                        # Count total mentions
                        genre_mention_counts[genre_name] = genre_mention_counts.get(genre_name, 0) + 1
                        total_genre_mentions += 1

                # Track unique anime per genre
                for genre_name in anime_genres:
                    if genre_name not in genre_anime_sets:
                        genre_anime_sets[genre_name] = set()
                    genre_anime_sets[genre_name].add(row.mal_id)

            # Convert to list with both percentage types
            genre_list = []
            for genre_name in set(genre_anime_sets.keys()) | set(genre_mention_counts.keys()):
                anime_count = len(genre_anime_sets.get(genre_name, set()))
                mention_count = genre_mention_counts.get(genre_name, 0)

                # Calculate both percentage types
                anime_percentage = (anime_count / total_anime * 100) if total_anime > 0 else 0
                mention_percentage = (mention_count / total_genre_mentions * 100) if total_genre_mentions > 0 else 0

                genre_list.append(
                    {
                        "genre": genre_name,
                        "anime_count": anime_count,
                        "mention_count": mention_count,
                        "anime_percentage": round(anime_percentage, 2),
                        "mention_percentage": round(mention_percentage, 2),
                    }
                )

            # Sort by anime count (coverage) by default
            genre_list.sort(key=lambda x: cast(int, x.get("anime_count", 0)), reverse=True)

            result = {
                "genres": genre_list,
                "total_anime": total_anime,
                "total_genre_mentions": total_genre_mentions,
                "snapshot_date": latest_date.isoformat(),
            }

            # Record successful query metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("genre_distribution", query_duration)

            # Cache the expensive result with longer TTL
            await self._set_cached_data(cache_key, result, self.cache_ttl["genre_distribution"])
            return result

        except Exception as e:
            logger.error("Failed to get genre distribution", error=str(e))
            # Record error in metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("genre_distribution_error", query_duration)
            raise
        finally:
            session.close()

    async def get_seasonal_trends(self) -> Dict[str, Any]:
        """Get seasonal anime trends by actual seasons and years with comprehensive metrics"""
        cache_key = self._get_cache_key("seasonal_trends")

        # Try cache first
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        start_time = time.time()
        session = get_database_session()
        try:
            query = text(
                """
                WITH resolved_snapshots AS (
                    SELECT
                        CASE
                            WHEN snapshot_type = 'seasonal_current' THEN
                                CASE
                                    WHEN EXTRACT(MONTH FROM snapshot_date) BETWEEN 1 AND 3 THEN 'winter'
                                    WHEN EXTRACT(MONTH FROM snapshot_date) BETWEEN 4 AND 6 THEN 'spring'
                                    WHEN EXTRACT(MONTH FROM snapshot_date) BETWEEN 7 AND 9 THEN 'summer'
                                    WHEN EXTRACT(MONTH FROM snapshot_date) BETWEEN 10 AND 12 THEN 'fall'
                                END
                            ELSE season
                        END AS season,

                        CASE
                            WHEN snapshot_type = 'seasonal_current' THEN EXTRACT(YEAR FROM snapshot_date)::int
                            ELSE year
                        END AS year,

                        score,
                        scored_by,
                        rank,
                        popularity,
                        members,
                        favorites,
                        snapshot_date
                    FROM anime_snapshots
                    WHERE season IS NOT NULL
                        AND year IS NOT NULL
                        AND season IN ('winter', 'spring', 'summer', 'fall')
                        AND snapshot_type IN ('seasonal_current', 'upcoming')
                )

                SELECT
                    season,
                    year,
                    COUNT(*) AS anime_count,

                    -- Averages
                    AVG(score) AS avg_score,
                    AVG(scored_by) AS avg_scored_by,
                    AVG(rank) AS avg_rank,
                    AVG(popularity) AS avg_popularity,
                    AVG(members) AS avg_members,
                    AVG(favorites) AS avg_favorites,

                    -- Sums
                    SUM(COALESCE(scored_by, 0)) AS total_scored_by,
                    SUM(COALESCE(members, 0)) AS total_members,
                    SUM(COALESCE(favorites, 0)) AS total_favorites,

                    MAX(snapshot_date) AS latest_snapshot_date

                FROM resolved_snapshots
                GROUP BY season, year
                HAVING COUNT(*) > 0
                ORDER BY year,
                    CASE season
                        WHEN 'winter' THEN 1
                        WHEN 'spring' THEN 2
                        WHEN 'summer' THEN 3
                        WHEN 'fall' THEN 4
                    END
            """
            )

            trends = []
            for row in session.execute(query):
                trends.append(
                    {
                        "season": row.season,
                        "year": row.year,
                        "anime_count": row.anime_count,
                        # Averages - SQL AVG() already excludes NULLs, so these are clean
                        "avg_score": (round(float(row.avg_score), 2) if row.avg_score is not None else None),
                        "avg_scored_by": (
                            round(float(row.avg_scored_by), 0) if row.avg_scored_by is not None else None
                        ),
                        "avg_rank": (round(float(row.avg_rank), 0) if row.avg_rank is not None else None),
                        "avg_popularity": (
                            round(float(row.avg_popularity), 0) if row.avg_popularity is not None else None
                        ),
                        "avg_members": (round(float(row.avg_members), 0) if row.avg_members is not None else None),
                        "avg_favorites": (
                            round(float(row.avg_favorites), 0) if row.avg_favorites is not None else None
                        ),
                        # Totals - COALESCE in SQL ensures these are never NULL
                        "total_scored_by": int(row.total_scored_by),  # No null check needed
                        "total_members": int(row.total_members),  # No null check needed
                        "total_favorites": int(row.total_favorites),  # No null check needed
                        "latest_snapshot_date": (
                            row.latest_snapshot_date.isoformat() if row.latest_snapshot_date else None
                        ),
                    }
                )

            result = {"trends": trends, "total_periods": len(trends)}

            # Record successful query metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("seasonal_trends", query_duration)

            await self._set_cached_data(cache_key, result, self.cache_ttl["seasonal_trends"])
            return result

        except Exception as e:
            logger.error("Failed to get seasonal trends", error=str(e))
            # Record error in metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("seasonal_trends_error", query_duration)
            raise
        finally:
            session.close()

    def _get_unique_anime_count(self, session) -> int:
        """Get count of unique anime (distinct mal_id)"""
        start_time = time.time()
        try:
            query = text("SELECT COUNT(DISTINCT mal_id) FROM anime_snapshots")
            result = session.execute(query).scalar()

            # Record successful query metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("unique_anime_count", query_duration)
            return result

        except Exception as e:
            # Record error in metrics
            query_duration = time.time() - start_time
            metrics.record_database_query("unique_anime_count_error", query_duration)
            logger.error("Failed to get unique anime count", error=str(e))
            raise

    def _parse_json_field(self, json_field) -> List[Dict]:
        """Safely parse JSON field from database"""
        if json_field is None:
            return []

        if isinstance(json_field, str):
            try:
                return json.loads(json_field)
            except (json.JSONDecodeError, TypeError):
                return []

        if isinstance(json_field, list):
            return json_field

        return []
