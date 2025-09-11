"""
API Response Models
Pydantic models for consistent API responses
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Database Stats Models
class SnapshotTypeInfo(BaseModel):
    type: str
    count: int
    latest_date: Optional[str]

class DatabaseStatsResponse(BaseModel):
    total_snapshots: int
    unique_anime: int
    latest_snapshot_date: Optional[str]
    snapshot_types: List[SnapshotTypeInfo]

# Anime Models
class AnimeItem(BaseModel):
    mal_id: int
    title: str
    score: Optional[float]
    rank: Optional[int]
    popularity: Optional[int]
    genres: List[str]
    studios: List[str]

class TopAnimeResponse(BaseModel):
    data: List[AnimeItem]
    total_results: int
    snapshot_type: str

# Genre Models
class GenreDistribution(BaseModel):
    genre: str
    anime_count: int  # Number of anime that have this genre
    mention_count: int  # Total number of times this genre is mentioned
    anime_percentage: float  # Percentage of anime that have this genre
    mention_percentage: float  # Percentage of total genre mentions

class GenreDistributionResponse(BaseModel):
    genres: List[GenreDistribution]
    total_anime: int
    total_genre_mentions: int
    snapshot_date: Optional[str]
    snapshot_type: str

# Seasonal Trends Models
class SeasonalTrend(BaseModel):
    season: str
    type: str
    anime_count: int
    latest_date: Optional[str]

class SeasonalTrendsResponse(BaseModel):
    trends: List[SeasonalTrend]
    total_seasons: int

# Generic API Response
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
