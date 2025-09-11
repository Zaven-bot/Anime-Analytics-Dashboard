"""
Analytics Service
Extends DatabaseLoader with analytics-specific queries for the API
"""

import sys
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import json
import structlog
import redis

# Add ETL source to Python path
etl_path = Path(__file__).parent.parent.parent.parent / "etl"
sys.path.append(str(etl_path))

from src.loaders.database import DatabaseLoader
from src.models.jikan import AnimeSnapshot
from sqlalchemy import text, func, desc, and_

logger = structlog.get_logger(__name__)

class AnalyticsService:
    """
    Analytics service that extends DatabaseLoader with read-only analytics queries.
    Reuses existing database connection and patterns from ETL.
    """
    
    def __init__(self):
        self.db_loader = DatabaseLoader()
        self.engine = self.db_loader.engine
        self.SessionLocal = self.db_loader.SessionLocal
        
        # Initialize Redis client
        settings = self.db_loader.settings
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        
        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            "database_stats": 300,      # 5 minutes
            "top_rated": 600,           # 10 minutes 
            "genre_distribution": 1800,  # 30 minutes (expensive query)
            "seasonal_trends": 900       # 15 minutes
        }
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate consistent cache keys"""
        key_parts = [prefix]
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        return ":".join(key_parts)
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning("Cache read failed", cache_key=cache_key, error=str(e))
        return None
    
    def _set_cached_data(self, cache_key: str, data: Dict[str, Any], ttl: int):
        """Set data in cache with TTL"""
        try:
            self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(data, default=str)  # default=str handles dates
            )
        except Exception as e:
            logger.warning("Cache write failed", cache_key=cache_key, error=str(e))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics (cached)"""
        cache_key = self._get_cache_key("db_stats")
        
        # Try cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info("Cache hit for database stats")
            return cached_data
        
        # Cache miss - query database
        logger.info("Cache miss for database stats - querying database")
        session = self.SessionLocal()
        try:
            # Total snapshots
            total_query = text("SELECT COUNT(*) FROM anime_snapshots")
            total_snapshots = session.execute(total_query).scalar()
            
            # Snapshots by type
            type_query = text("""
                SELECT snapshot_type, COUNT(*) as count, MAX(snapshot_date) as latest_date
                FROM anime_snapshots 
                GROUP BY snapshot_type
                ORDER BY count DESC
            """)
            snapshot_types = []
            for row in session.execute(type_query):
                snapshot_types.append({
                    "type": row.snapshot_type,
                    "count": row.count,
                    "latest_date": row.latest_date.isoformat() if row.latest_date else None
                })
            
            # Latest snapshot date overall
            latest_query = text("SELECT MAX(snapshot_date) FROM anime_snapshots")
            latest_date = session.execute(latest_query).scalar()
            
            result = {
                "total_snapshots": total_snapshots,
                "snapshot_types": snapshot_types,
                "latest_snapshot_date": latest_date.isoformat() if latest_date else None,
                "unique_anime": self._get_unique_anime_count(session)
            }
            
            # After getting results, cache them
            self._set_cached_data(cache_key, result, self.cache_ttl["database_stats"])
            return result
            
        except Exception as e:
            logger.error("Failed to get database stats", error=str(e))
            raise
        finally:
            session.close()
    
    def get_top_rated_anime(self, limit: int = 10, snapshot_type: str = "top") -> List[Dict[str, Any]]:
        """Get top-rated anime from latest snapshots"""
        session = self.SessionLocal()
        try:
            # Get latest snapshot date for the type
            latest_date_query = text("""
                SELECT MAX(snapshot_date) 
                FROM anime_snapshots 
                WHERE snapshot_type = :snapshot_type
            """)
            latest_date = session.execute(latest_date_query, {"snapshot_type": snapshot_type}).scalar()
            
            if not latest_date:
                return []
            
            # Get top anime from latest snapshot
            query = text("""
                SELECT mal_id, title, score, rank, popularity, genres, studios
                FROM anime_snapshots 
                WHERE snapshot_type = :snapshot_type 
                  AND snapshot_date = :snapshot_date 
                  AND score IS NOT NULL
                ORDER BY score DESC, rank ASC
                LIMIT :limit
            """)
            
            results = []
            for row in session.execute(query, {
                "snapshot_type": snapshot_type,
                "snapshot_date": latest_date,
                "limit": limit
            }):
                # Parse JSON fields safely
                genres = self._parse_json_field(row.genres)
                studios = self._parse_json_field(row.studios)
                
                results.append({
                    "mal_id": row.mal_id,
                    "title": row.title,
                    "score": float(row.score) if row.score else None,
                    "rank": row.rank,
                    "popularity": row.popularity,
                    "genres": [g.get("name", "") for g in genres if isinstance(g, dict) and "name" in g],
                    "studios": [s.get("name", "") for s in studios if isinstance(s, dict) and "name" in s]
                })
            
            return results
            
        except Exception as e:
            logger.error("Failed to get top rated anime", error=str(e))
            raise
        finally:
            session.close()
    
    def get_genre_distribution(self, snapshot_type: str = "top") -> Dict[str, Any]:
        """Get genre distribution from latest snapshots (cached - this is expensive!)"""
        cache_key = self._get_cache_key("genre_dist", snapshot_type=snapshot_type)
        
        # Try cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info("Cache hit for genre distribution", snapshot_type=snapshot_type)
            return cached_data
        
        # Cache miss - run expensive query
        logger.info("Cache miss for genre distribution - running expensive query", snapshot_type=snapshot_type)
        session = self.SessionLocal()
        try:
            # Get latest snapshot date
            latest_date_query = text("""
                SELECT MAX(snapshot_date) 
                FROM anime_snapshots 
                WHERE snapshot_type = :snapshot_type
            """)
            latest_date = session.execute(latest_date_query, {"snapshot_type": snapshot_type}).scalar()
            
            if not latest_date:
                return {"genres": [], "total_anime": 0, "total_genre_mentions": 0, "snapshot_date": None}
            
            # Get all anime with genres from latest snapshot
            query = text("""
                SELECT genres, mal_id
                FROM anime_snapshots 
                WHERE snapshot_type = :snapshot_type 
                  AND snapshot_date = :snapshot_date 
                  AND genres IS NOT NULL
            """)
            
            # Two different counting approaches:
            # 1. anime_count: How many unique anime have this genre (for coverage percentage)
            # 2. mention_count: How many times this genre appears total (for frequency percentage)
            genre_anime_sets = {}  # Track unique anime per genre
            genre_mention_counts = {}  # Count total mentions per genre
            total_anime = 0
            total_genre_mentions = 0
            
            for row in session.execute(query, {
                "snapshot_type": snapshot_type,
                "snapshot_date": latest_date
            }):
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
                
                genre_list.append({
                    "genre": genre_name,
                    "anime_count": anime_count,
                    "mention_count": mention_count,
                    "anime_percentage": round(anime_percentage, 2),
                    "mention_percentage": round(mention_percentage, 2)
                })
            
            # Sort by anime count (coverage) by default
            genre_list.sort(key=lambda x: x["anime_count"], reverse=True)
            
            result = {
                "genres": genre_list,
                "total_anime": total_anime,
                "total_genre_mentions": total_genre_mentions,
                "snapshot_date": latest_date.isoformat()
            }
            
            # After getting results, cache them (longer TTL for expensive queries)
            self._set_cached_data(cache_key, result, self.cache_ttl["genre_distribution"])
            return result
            
        except Exception as e:
            logger.error("Failed to get genre distribution", error=str(e))
            raise
        finally:
            session.close()
    
    def get_seasonal_trends(self) -> Dict[str, Any]:
        """Get seasonal anime trends"""
        session = self.SessionLocal()
        try:
            query = text("""
                SELECT 
                    snapshot_type,
                    COUNT(*) as anime_count,
                    MAX(snapshot_date) as latest_date
                FROM anime_snapshots 
                WHERE snapshot_type IN ('seasonal_current', 'upcoming')
                GROUP BY snapshot_type
                ORDER BY snapshot_type
            """)
            
            trends = []
            for row in session.execute(query):
                season_name = "Current Season" if row.snapshot_type == "seasonal_current" else "Upcoming"
                trends.append({
                    "season": season_name,
                    "type": row.snapshot_type,
                    "anime_count": row.anime_count,
                    # "average_score": round(float(row.avg_score), 2) if row.avg_score else None,
                    "latest_date": row.latest_date.isoformat() if row.latest_date else None
                })
            
            return {
                "trends": trends,
                "total_seasons": len(trends)
            }
            
        except Exception as e:
            logger.error("Failed to get seasonal trends", error=str(e))
            raise
        finally:
            session.close()
    
    def _get_unique_anime_count(self, session) -> int:
        """Get count of unique anime (distinct mal_id)"""
        query = text("SELECT COUNT(DISTINCT mal_id) FROM anime_snapshots")
        return session.execute(query).scalar()
    
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
