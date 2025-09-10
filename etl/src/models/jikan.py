"""
Pydantic models for Jikan API responses and database entities.
These models provide validation and type safety for our ETL pipeline.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class JikanImage(BaseModel):
    """Image URLs from Jikan API"""
    image_url: Optional[str] = None
    small_image_url: Optional[str] = None
    large_image_url: Optional[str] = None


class JikanImages(BaseModel):
    """Image collection from Jikan API"""
    jpg: Optional[JikanImage] = None
    webp: Optional[JikanImage] = None


class JikanTrailer(BaseModel):
    """Trailer information from Jikan API"""
    youtube_id: Optional[str] = None
    url: Optional[str] = None
    embed_url: Optional[str] = None


class JikanTitle(BaseModel):
    """Individual title entry"""
    type: str
    title: str


class JikanDateProp(BaseModel):
    """Date property structure"""
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None


class JikanAiredProp(BaseModel):
    """Aired property structure"""
    from_: Optional[JikanDateProp] = Field(None, alias="from")
    to: Optional[JikanDateProp] = None
    string: Optional[str] = None


class JikanAired(BaseModel):
    """Aired date information"""
    from_: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    prop: Optional[JikanAiredProp] = None


class JikanBroadcast(BaseModel):
    """Broadcast information"""
    day: Optional[str] = None
    time: Optional[str] = None
    timezone: Optional[str] = None
    string: Optional[str] = None


class JikanEntity(BaseModel):
    """Generic entity (producer, studio, genre, etc.)"""
    mal_id: int
    type: str
    name: str
    url: str

# Raw Anime Response Model
class JikanAnime(BaseModel):
    """Main anime data structure from Jikan API search response"""
    mal_id: int
    url: Optional[str] = None
    images: Optional[JikanImages] = None
    trailer: Optional[JikanTrailer] = None
    approved: Optional[bool] = None
    titles: Optional[List[JikanTitle]] = None
    title: str
    title_english: Optional[str] = None
    title_japanese: Optional[str] = None
    title_synonyms: Optional[List[str]] = None
    type: Optional[str] = None
    source: Optional[str] = None
    episodes: Optional[int] = None
    status: Optional[str] = None
    airing: Optional[bool] = None
    aired: Optional[JikanAired] = None
    duration: Optional[str] = None
    rating: Optional[str] = None
    score: Optional[float] = None
    scored_by: Optional[int] = None
    rank: Optional[int] = None
    popularity: Optional[int] = None
    members: Optional[int] = None
    favorites: Optional[int] = None
    synopsis: Optional[str] = None
    background: Optional[str] = None
    season: Optional[str] = None
    year: Optional[int] = None
    broadcast: Optional[JikanBroadcast] = None
    producers: Optional[List[JikanEntity]] = None
    licensors: Optional[List[JikanEntity]] = None
    studios: Optional[List[JikanEntity]] = None
    genres: Optional[List[JikanEntity]] = None
    explicit_genres: Optional[List[JikanEntity]] = None
    themes: Optional[List[JikanEntity]] = None
    demographics: Optional[List[JikanEntity]] = None


class JikanPaginationItems(BaseModel):
    """Pagination item counts"""
    count: int
    total: int
    per_page: int


class JikanPagination(BaseModel):
    """Pagination information"""
    last_visible_page: int
    has_next_page: bool
    current_page: int
    items: JikanPaginationItems


class JikanSearchResponse(BaseModel):
    """Complete search response from Jikan API"""
    data: List[JikanAnime]
    pagination: JikanPagination

# Cleaned, Transformed Anime Snapshot Model
class AnimeSnapshot(BaseModel):
    """Database model for anime snapshots"""
    mal_id: int
    url: Optional[str] = None
    title: str
    title_english: Optional[str] = None
    title_japanese: Optional[str] = None
    title_synonyms: Optional[List[str]] = None
    titles: Optional[List[Dict[str, str]]] = None
    type: Optional[str] = None
    source: Optional[str] = None
    episodes: Optional[int] = None
    status: Optional[str] = None
    airing: Optional[bool] = None
    duration: Optional[str] = None
    rating: Optional[str] = None
    score: Optional[float] = None
    scored_by: Optional[int] = None
    rank: Optional[int] = None
    popularity: Optional[int] = None
    members: Optional[int] = None
    favorites: Optional[int] = None
    approved: Optional[bool] = None
    season: Optional[str] = None
    year: Optional[int] = None
    aired: Optional[Dict[str, Any]] = None
    synopsis: Optional[str] = None
    background: Optional[str] = None
    images: Optional[Dict[str, Any]] = None
    trailer: Optional[Dict[str, Any]] = None
    genres: Optional[List[Dict[str, Any]]] = None
    explicit_genres: Optional[List[Dict[str, Any]]] = None
    themes: Optional[List[Dict[str, Any]]] = None
    demographics: Optional[List[Dict[str, Any]]] = None
    studios: Optional[List[Dict[str, Any]]] = None
    producers: Optional[List[Dict[str, Any]]] = None
    licensors: Optional[List[Dict[str, Any]]] = None
    broadcast: Optional[Dict[str, Any]] = None
    snapshot_type: str  # 'top', 'seasonal', 'upcoming', etc.
    snapshot_date: date
    
    @field_validator('score')
    def validate_score(cls, v):
        """Ensure score is within valid range"""
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Score must be between 0 and 10')
        return v
    
    @field_validator('episodes')
    def validate_episodes(cls, v):
        """Ensure episodes is positive"""
        if v is not None and v < 0:
            raise ValueError('Episodes cannot be negative')
        return v
