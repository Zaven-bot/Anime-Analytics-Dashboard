"""
Unit tests for Pydantic response models and validation
Tests API response models, validation rules, and serialization
"""

import pytest
from pydantic import ValidationError
from typing import List, Dict, Any

from services.backend.app.models.responses import (
    SnapshotTypeInfo,
    DatabaseStatsResponse,
    AnimeItem,
    TopAnimeResponse,
    GenreDistribution,
    GenreDistributionResponse,
    SeasonalTrend,
    SeasonalTrendsResponse,
    APIResponse,
)


class TestSnapshotTypeInfo:
    """Test SnapshotTypeInfo model"""

    def test_valid_snapshot_type_info(self):
        """Test valid snapshot type info creation"""
        data = {
            "type": "top",
            "count": 50,
            "latest_date": "2025-09-13"
        }
        
        info = SnapshotTypeInfo(**data)
        
        assert info.type == "top"
        assert info.count == 50
        assert info.latest_date == "2025-09-13"

    def test_snapshot_type_info_optional_date(self):
        """Test snapshot type info with optional date"""
        data = {
            "type": "upcoming",
            "count": 25,
            "latest_date": None
        }
        
        info = SnapshotTypeInfo(**data)
        
        assert info.type == "upcoming"
        assert info.count == 25
        assert info.latest_date is None

    def test_snapshot_type_info_validation_errors(self):
        """Test validation errors for snapshot type info"""
        # Missing required field
        with pytest.raises(ValidationError):
            SnapshotTypeInfo(type="top")  # Missing count
        
        # Invalid type
        with pytest.raises(ValidationError):
            SnapshotTypeInfo(type="top", count="not_a_number")


class TestDatabaseStatsResponse:
    """Test DatabaseStatsResponse model"""

    def test_valid_database_stats_response(self):
        """Test valid database stats response creation"""
        data = {
            "total_snapshots": 1000,
            "unique_anime": 750,
            "latest_snapshot_date": "2025-09-13",
            "snapshot_types": [
                {"type": "top", "count": 250, "latest_date": "2025-09-13"},
                {"type": "airing", "count": 200, "latest_date": "2025-09-13"}
            ]
        }
        
        response = DatabaseStatsResponse(**data)
        
        assert response.total_snapshots == 1000
        assert response.unique_anime == 750
        assert response.latest_snapshot_date == "2025-09-13"
        assert len(response.snapshot_types) == 2
        assert isinstance(response.snapshot_types[0], SnapshotTypeInfo)

    def test_database_stats_response_optional_date(self):
        """Test database stats response with optional date"""
        data = {
            "total_snapshots": 0,
            "unique_anime": 0,
            "latest_snapshot_date": None,
            "snapshot_types": []
        }
        
        response = DatabaseStatsResponse(**data)
        
        assert response.latest_snapshot_date is None
        assert response.snapshot_types == []


class TestAnimeItem:
    """Test AnimeItem model"""

    def test_valid_anime_item(self):
        """Test valid anime item creation"""
        data = {
            "mal_id": 5114,
            "title": "Fullmetal Alchemist: Brotherhood",
            "score": 9.64,
            "rank": 1,
            "popularity": 3,
            "genres": ["Action", "Drama", "Fantasy"],
            "studios": ["Bones"]
        }
        
        anime = AnimeItem(**data)
        
        assert anime.mal_id == 5114
        assert anime.title == "Fullmetal Alchemist: Brotherhood"
        assert anime.score == 9.64
        assert anime.rank == 1
        assert anime.popularity == 3
        assert anime.genres == ["Action", "Drama", "Fantasy"]
        assert anime.studios == ["Bones"]

    def test_anime_item_optional_fields(self):
        """Test anime item with optional fields"""
        data = {
            "mal_id": 12345,
            "title": "Test Anime",
            "score": None,
            "rank": None,
            "popularity": None,
            "genres": [],
            "studios": []
        }
        
        anime = AnimeItem(**data)
        
        assert anime.score is None
        assert anime.rank is None
        assert anime.popularity is None
        assert anime.genres == []
        assert anime.studios == []

    def test_anime_item_validation_errors(self):
        """Test validation errors for anime item"""
        # Missing required fields
        with pytest.raises(ValidationError):
            AnimeItem(mal_id=123)  # Missing title, genres, studios
        
        # Invalid data types
        with pytest.raises(ValidationError):
            AnimeItem(
                mal_id="not_a_number",
                title="Test",
                genres=[],
                studios=[]
            )


class TestTopAnimeResponse:
    """Test TopAnimeResponse model"""

    def test_valid_top_anime_response(self):
        """Test valid top anime response creation"""
        anime_data = {
            "mal_id": 5114,
            "title": "Fullmetal Alchemist: Brotherhood",
            "score": 9.64,
            "rank": 1,
            "popularity": 3,
            "genres": ["Action", "Drama"],
            "studios": ["Bones"]
        }
        
        data = {
            "data": [anime_data],
            "total_results": 50,
            "snapshot_type": "top"
        }
        
        response = TopAnimeResponse(**data)
        
        assert len(response.data) == 1
        assert isinstance(response.data[0], AnimeItem)
        assert response.total_results == 50
        assert response.snapshot_type == "top"

    def test_empty_top_anime_response(self):
        """Test empty top anime response"""
        data = {
            "data": [],
            "total_results": 0,
            "snapshot_type": "upcoming"
        }
        
        response = TopAnimeResponse(**data)
        
        assert response.data == []
        assert response.total_results == 0


class TestGenreDistribution:
    """Test GenreDistribution model"""

    def test_valid_genre_distribution(self):
        """Test valid genre distribution creation"""
        data = {
            "genre": "Action",
            "anime_count": 45,
            "mention_count": 45,
            "anime_percentage": 18.0,
            "mention_percentage": 12.5
        }
        
        genre = GenreDistribution(**data)
        
        assert genre.genre == "Action"
        assert genre.anime_count == 45
        assert genre.mention_count == 45
        assert genre.anime_percentage == 18.0
        assert genre.mention_percentage == 12.5

    def test_genre_distribution_percentage_validation(self):
        """Test genre distribution percentage bounds"""
        # Valid percentages
        data = {
            "genre": "Drama",
            "anime_count": 10,
            "mention_count": 15,
            "anime_percentage": 0.0,
            "mention_percentage": 100.0
        }
        
        genre = GenreDistribution(**data)
        assert genre.anime_percentage == 0.0
        assert genre.mention_percentage == 100.0


class TestGenreDistributionResponse:
    """Test GenreDistributionResponse model"""

    def test_valid_genre_distribution_response(self):
        """Test valid genre distribution response creation"""
        genre_data = {
            "genre": "Action",
            "anime_count": 45,
            "mention_count": 45,
            "anime_percentage": 18.0,
            "mention_percentage": 12.5
        }
        
        data = {
            "genres": [genre_data],
            "total_anime": 250,
            "total_genre_mentions": 360,
            "snapshot_date": "2025-09-13",
            "snapshot_type": "top"
        }
        
        response = GenreDistributionResponse(**data)
        
        assert len(response.genres) == 1
        assert isinstance(response.genres[0], GenreDistribution)
        assert response.total_anime == 250
        assert response.total_genre_mentions == 360
        assert response.snapshot_date == "2025-09-13"
        assert response.snapshot_type == "top"

    def test_genre_distribution_response_optional_date(self):
        """Test genre distribution response with optional date"""
        data = {
            "genres": [],
            "total_anime": 0,
            "total_genre_mentions": 0,
            "snapshot_date": None,
            "snapshot_type": "airing"
        }
        
        response = GenreDistributionResponse(**data)
        
        assert response.snapshot_date is None
        assert response.genres == []


class TestSeasonalTrend:
    """Test SeasonalTrend model"""

    def test_valid_seasonal_trend(self):
        """Test valid seasonal trend creation"""
        data = {
            "season": "fall",
            "year": 2024,
            "anime_count": 25,
            "avg_score": 7.45,
            "total_scored_by": 125000,
            "avg_scored_by": 5000.0,
            "avg_rank": 1500.0,
            "avg_popularity": 800.0,
            "total_members": 750000,
            "avg_members": 30000.0,
            "total_favorites": 15000,
            "avg_favorites": 600.0,
            "latest_snapshot_date": "2025-09-13"
        }
        
        trend = SeasonalTrend(**data)
        
        assert trend.season == "fall"
        assert trend.year == 2024
        assert trend.anime_count == 25
        assert trend.avg_score == 7.45
        assert trend.total_scored_by == 125000

    def test_seasonal_trend_optional_fields(self):
        """Test seasonal trend with optional fields"""
        data = {
            "season": "spring",
            "year": 2023,
            "anime_count": 0,
            "avg_score": None,
            "total_scored_by": 0,
            "avg_scored_by": None,
            "avg_rank": None,
            "avg_popularity": None,
            "total_members": 0,
            "avg_members": None,
            "total_favorites": 0,
            "avg_favorites": None,
            "latest_snapshot_date": None
        }
        
        trend = SeasonalTrend(**data)
        
        assert trend.avg_score is None
        assert trend.avg_scored_by is None
        assert trend.latest_snapshot_date is None

    def test_seasonal_trend_year_validation(self):
        """Test seasonal trend year validation"""
        # Valid year with all required fields
        data = {
            "season": "summer",
            "year": 2025,
            "anime_count": 20,
            "avg_score": 7.5,
            "total_scored_by": 1000,
            "avg_scored_by": 50.0,
            "avg_rank": 500.0,
            "avg_popularity": 250.0,
            "total_members": 5000,
            "avg_members": 250.0,
            "total_favorites": 100,
            "avg_favorites": 5.0,
            "latest_snapshot_date": "2025-09-13"
        }
        
        trend = SeasonalTrend(**data)
        assert trend.year == 2025


class TestSeasonalTrendsResponse:
    """Test SeasonalTrendsResponse model"""

    def test_valid_seasonal_trends_response(self):
        """Test valid seasonal trends response creation"""
        trend_data = {
            "season": "fall",
            "year": 2024,
            "anime_count": 25,
            "avg_score": 7.5,
            "total_scored_by": 125000,
            "avg_scored_by": 5000.0,
            "avg_rank": 800.0,
            "avg_popularity": 400.0,
            "total_members": 750000,
            "avg_members": 30000.0,
            "total_favorites": 15000,
            "avg_favorites": 600.0,
            "latest_snapshot_date": "2025-09-13"
        }
        
        data = {
            "trends": [trend_data],
            "total_periods": 12
        }
        
        response = SeasonalTrendsResponse(**data)
        
        assert len(response.trends) == 1
        assert isinstance(response.trends[0], SeasonalTrend)
        assert response.total_periods == 12

    def test_empty_seasonal_trends_response(self):
        """Test empty seasonal trends response"""
        data = {
            "trends": [],
            "total_periods": 0
        }
        
        response = SeasonalTrendsResponse(**data)
        
        assert response.trends == []
        assert response.total_periods == 0


class TestAPIResponse:
    """Test generic APIResponse model"""

    def test_valid_api_response_success(self):
        """Test valid successful API response"""
        data = {
            "success": True,
            "message": "Operation completed successfully",
            "data": {"result": "test_data"}
        }
        
        response = APIResponse(**data)
        
        assert response.success is True
        assert response.message == "Operation completed successfully"
        assert response.data == {"result": "test_data"}

    def test_valid_api_response_error(self):
        """Test valid error API response"""
        data = {
            "success": False,
            "message": "Operation failed",
            "data": None
        }
        
        response = APIResponse(**data)
        
        assert response.success is False
        assert response.message == "Operation failed"
        assert response.data is None

    def test_api_response_optional_data(self):
        """Test API response with optional data field"""
        data = {
            "success": True,
            "message": "Success without data"
        }
        
        response = APIResponse(**data)
        
        assert response.success is True
        assert response.message == "Success without data"
        assert response.data is None


class TestModelSerialization:
    """Test model serialization and JSON compatibility"""

    def test_anime_item_serialization(self):
        """Test anime item serializes to JSON properly"""
        data = {
            "mal_id": 5114,
            "title": "Fullmetal Alchemist: Brotherhood",
            "score": 9.64,
            "rank": 1,
            "popularity": 3,
            "genres": ["Action", "Drama"],
            "studios": ["Bones"]
        }
        
        anime = AnimeItem(**data)
        json_data = anime.model_dump()
        
        # Should be able to recreate from JSON
        anime_copy = AnimeItem(**json_data)
        assert anime_copy.mal_id == anime.mal_id
        assert anime_copy.title == anime.title

    def test_nested_model_serialization(self):
        """Test nested model serialization"""
        data = {
            "total_snapshots": 1000,
            "unique_anime": 750,
            "latest_snapshot_date": "2025-09-13",
            "snapshot_types": [
                {"type": "top", "count": 250, "latest_date": "2025-09-13"}
            ]
        }
        
        response = DatabaseStatsResponse(**data)
        json_data = response.model_dump()
        
        # Nested models should serialize properly
        assert json_data["snapshot_types"][0]["type"] == "top"
        
        # Should be able to recreate from JSON
        response_copy = DatabaseStatsResponse(**json_data)
        assert len(response_copy.snapshot_types) == 1


if __name__ == "__main__":
    pytest.main([__file__])
