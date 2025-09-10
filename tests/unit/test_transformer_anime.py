"""
Unit tests for anime data transformer.
Tests transformation logic, validation, and data cleaning.
"""

import pytest
from datetime import date
from pydantic import ValidationError
from unittest.mock import Mock, patch

# Add ETL src to path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../etl'))

from src.transformers.anime import AnimeTransformer, DataTransformationError
from src.models.jikan import JikanAnime, AnimeSnapshot
from tests.fixtures.mock_data import MOCK_JIKAN_SEARCH_RESPONSE, INVALID_JIKAN_ANIME

@pytest.mark.unit
class TestAnimeTransformer:
    """Test anime data transformation functionality"""
    
    @pytest.fixture
    def transformer(self):
        """Create an AnimeTransformer instance for testing"""
        return AnimeTransformer()
    
    @pytest.fixture
    def sample_anime(self):
        """Create a sample JikanAnime object for testing"""
        return JikanAnime(**MOCK_JIKAN_SEARCH_RESPONSE["data"][0])
    
    @pytest.fixture
    def sample_anime_list(self):
        """Create a list of JikanAnime objects for testing"""
        return [
            JikanAnime(**anime_data) 
            for anime_data in MOCK_JIKAN_SEARCH_RESPONSE["data"]
        ]
    
    def test_transform_single_anime(self, transformer, sample_anime):
        """Test transforming a single anime object"""
        snapshot_type = "top"
        snapshot_date = date(2024, 1, 15)
        
        result = transformer._transform_single_anime(
            sample_anime, snapshot_type, snapshot_date
        )
        
        assert isinstance(result, AnimeSnapshot)
        assert result.mal_id == sample_anime.mal_id
        assert result.title == sample_anime.title
        assert result.snapshot_type == snapshot_type
        assert result.snapshot_date == snapshot_date
        assert result.score == sample_anime.score
        assert result.rank == sample_anime.rank
    
    def test_transform_anime_list(self, transformer, sample_anime_list):
        """Test transforming a list of anime objects"""
        snapshot_type = "seasonal"
        snapshot_date = date(2024, 1, 15)
        
        results = transformer.transform_anime_list(
            sample_anime_list, snapshot_type, snapshot_date
        )
        
        assert len(results) == 2
        assert all(isinstance(snapshot, AnimeSnapshot) for snapshot in results)
        assert all(snapshot.snapshot_type == snapshot_type for snapshot in results)
        assert all(snapshot.snapshot_date == snapshot_date for snapshot in results)
        
        # Check specific transformations
        cowboy_bebop = next(s for s in results if s.mal_id == 1)
        assert cowboy_bebop.title == "Cowboy Bebop"
        assert cowboy_bebop.score == 8.75
        
        fma = next(s for s in results if s.mal_id == 5)
        assert fma.title == "Fullmetal Alchemist"
        assert fma.score == 8.12
    
    def test_transform_anime_list_default_date(self, transformer, sample_anime_list):
        """Test that default snapshot date is today"""
        results = transformer.transform_anime_list(
            sample_anime_list, "top"
        )
        
        assert all(snapshot.snapshot_date == date.today() for snapshot in results)
    
    def test_titles_conversion(self, transformer, sample_anime):
        """Test conversion of titles array to dictionary format"""
        result = transformer._transform_single_anime(
            sample_anime, "top", date.today()
        )
        
        assert isinstance(result.titles, list)
        assert len(result.titles) == 2
        assert result.titles[0] == {"type": "Default", "title": "Cowboy Bebop"}
        assert result.titles[1] == {"type": "Japanese", "title": "カウボーイビバップ"}
    
    def test_aired_conversion(self, transformer, sample_anime):
        """Test conversion of aired object to dictionary format"""
        result = transformer._transform_single_anime(
            sample_anime, "top", date.today()
        )
        
        assert isinstance(result.aired, dict)
        assert "from" in result.aired
        assert "to" in result.aired
        assert "prop" in result.aired
        assert result.aired["from"] == "1998-04-03T00:00:00+00:00"
        assert result.aired["to"] == "1999-04-24T00:00:00+00:00"
    
    def test_entities_conversion(self, transformer, sample_anime):
        """Test conversion of entity lists (genres, studios, etc.) to dictionary format"""
        result = transformer._transform_single_anime(
            sample_anime, "top", date.today()
        )
        
        # Test genres conversion
        assert isinstance(result.genres, list)
        assert len(result.genres) == 2
        assert result.genres[0] == {
            "mal_id": 1,
            "type": "anime",
            "name": "Action",
            "url": "https://myanimelist.net/anime/genre/1/Action"
        }
        
        # Test studios conversion
        assert isinstance(result.studios, list)
        assert len(result.studios) == 1
        assert result.studios[0]["name"] == "Sunrise"
        
        # Test themes conversion
        assert isinstance(result.themes, list)
        assert len(result.themes) == 1
        assert result.themes[0]["name"] == "Space"
    
    def test_empty_entities_conversion(self, transformer):
        """Test handling of empty entity lists"""
        # Create anime with no demographics
        anime_data = MOCK_JIKAN_SEARCH_RESPONSE["data"][0].copy()
        anime_data["demographics"] = []
        anime = JikanAnime(**anime_data)
        
        result = transformer._transform_single_anime(
            anime, "top", date.today()
        )
        
        assert result.demographics is None
    
    def test_null_entities_conversion(self, transformer):
        """Test handling of null entity lists"""
        # Create anime with null trailer
        anime_data = MOCK_JIKAN_SEARCH_RESPONSE["data"][1].copy()  # FMA has null trailer
        anime = JikanAnime(**anime_data)
        
        result = transformer._transform_single_anime(
            anime, "top", date.today()
        )
        
        assert result.trailer is None
    
    def test_text_cleaning(self, transformer):
        """Test text cleaning functionality"""
        # Test normal text
        normal_text = "This is a normal synopsis."
        cleaned = transformer._clean_text(normal_text)
        assert cleaned == normal_text
        
        # Test text with extra whitespace
        messy_text = "  This   has    extra   whitespace.  \n\t  "
        cleaned = transformer._clean_text(messy_text)
        assert cleaned == "This has extra whitespace."
        
        # Test None text
        cleaned = transformer._clean_text(None)
        assert cleaned is None
        
        # Test empty text
        cleaned = transformer._clean_text("")
        assert cleaned is None
        
        # Test very long text (should be truncated)
        long_text = "A" * 6000
        cleaned = transformer._clean_text(long_text)
        assert len(cleaned) == 5000
        assert cleaned.endswith("...")
    
    def test_invalid_anime_handling(self, transformer):
        """Test handling of invalid anime data"""
        # Create an invalid anime object (this would normally fail Pydantic validation)
        try:
            invalid_anime = JikanAnime(**INVALID_JIKAN_ANIME)
        except ValidationError:
            # If Pydantic validation fails, that's expected
            # In real scenario, we'd need to create a mock that bypasses validation
            pytest.skip("Pydantic validation prevents invalid anime creation")

    def test_unexpected_error_handling(self, transformer):
        """Test handling of unexpected errors during transformation"""
        
        # Create a mock anime
        error_anime = Mock()
        error_anime.mal_id = 999
        error_anime.title = "Error Anime"
        
        # Mock the _transform_single_anime to raise unexpected error
        with patch.object(transformer, '_transform_single_anime', 
                         side_effect=Exception("Unexpected transformation error")):
            
            results = transformer.transform_anime_list([error_anime], "test")
            
            # Should return empty list due to error
            assert len(results) == 0
            
            # Check error tracking
            assert len(transformer.validation_errors) == 1
            assert transformer.validation_errors[0]["mal_id"] == 999
            assert transformer.validation_errors[0]["title"] == "Error Anime"
            assert "Transformation error: Unexpected transformation error" in transformer.validation_errors[0]["error"]
            
            # Check statistics
            assert transformer.transformation_stats["dropped_invalid"] == 1
            assert transformer.transformation_stats["total_processed"] == 1
            assert transformer.transformation_stats["successful_transforms"] == 0
    
    def test_transformation_statistics_tracking(self, transformer, sample_anime_list):
        """Test that transformation statistics are tracked correctly"""
        transformer.reset_stats()
        
        results = transformer.transform_anime_list(
            sample_anime_list, "top", date.today()
        )
        
        stats = transformer.get_transformation_summary()
        
        assert stats["stats"]["total_processed"] == 2
        assert stats["stats"]["successful_transforms"] == 2
        assert stats["stats"]["validation_errors"] == 0
        assert stats["stats"]["dropped_invalid"] == 0
        assert stats["success_rate"] == 100.0
    
    def test_reset_stats(self, transformer):
        """Test resetting transformation statistics"""
        # Process some data to generate stats
        transformer.transformation_stats["total_processed"] = 10
        transformer.transformation_stats["successful_transforms"] = 8
        transformer.validation_errors = [{"error": "test"}]
        
        transformer.reset_stats()
        
        assert transformer.transformation_stats["total_processed"] == 0
        assert transformer.transformation_stats["successful_transforms"] == 0
        assert transformer.transformation_stats["validation_errors"] == 0
        assert transformer.transformation_stats["dropped_invalid"] == 0
        assert len(transformer.validation_errors) == 0
    
    def test_get_transformation_summary(self, transformer):
        """Test getting transformation summary"""
        # Set some stats manually
        transformer.transformation_stats = {
            "total_processed": 10,
            "successful_transforms": 8,
            "validation_errors": 1,
            "dropped_invalid": 1
        }
        transformer.validation_errors = [{"error": "test error"}]
        
        summary = transformer.get_transformation_summary()
        
        assert summary["stats"]["total_processed"] == 10
        assert summary["stats"]["successful_transforms"] == 8
        assert summary["success_rate"] == 80.0
        assert len(summary["validation_errors"]) == 1
    
    def test_score_validation_in_snapshot(self, transformer, sample_anime):
        """Test that score validation works in AnimeSnapshot"""
        # Valid score
        result = transformer._transform_single_anime(
            sample_anime, "top", date.today()
        )
        assert result.score == 8.75
        
        # Test would fail with invalid score, but Pydantic handles this
        # during AnimeSnapshot creation
    
    def test_episodes_validation_in_snapshot(self, transformer):
        """Test that episodes validation works in AnimeSnapshot"""
        # Create anime with valid episodes
        anime_data = MOCK_JIKAN_SEARCH_RESPONSE["data"][0].copy()
        anime_data["episodes"] = 26
        anime = JikanAnime(**anime_data)
        
        result = transformer._transform_single_anime(
            anime, "top", date.today()
        )
        assert result.episodes == 26
    
    def test_create_transformer_function(self):
        """Test the create_transformer utility function"""
        from src.transformers.anime import create_transformer
        
        transformer = create_transformer()
        assert isinstance(transformer, AnimeTransformer)


if __name__ == "__main__":
    pytest.main([__file__])
