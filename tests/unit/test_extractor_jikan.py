"""
Unit tests for Jikan API extractor.
Tests API extraction logic, retry behavior, and error handling.
"""

import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from tenacity import RetryError

# Add ETL src to path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/etl'))

from src.extractors.jikan import JikanExtractor, JikanAPIError
from src.models.jikan import JikanSearchResponse, JikanAnime
from tests.fixtures.mock_data import MOCK_JIKAN_SEARCH_RESPONSE, MOCK_ETL_JOB_CONFIG

@pytest.mark.unit
class TestJikanExtractor:
    """Test Jikan API extractor functionality"""
    
    @pytest.fixture
    def extractor(self):
        """Create a JikanExtractor instance for testing"""
        return JikanExtractor()
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response"""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = MOCK_JIKAN_SEARCH_RESPONSE
        response.headers = {}
        return response
    
    @pytest.mark.asyncio
    async def test_successful_request(self, extractor, mock_response):
        """Test successful API request"""
        with patch.object(extractor.client, 'get', return_value=mock_response) as mock_get:
            result = await extractor._make_request('/anime', {'limit': 25})
            
            assert result == MOCK_JIKAN_SEARCH_RESPONSE
            mock_get.assert_called_once_with(
                'https://api.jikan.moe/v4/anime',
                params={'limit': 25}
            )
    
    @pytest.mark.asyncio
    async def test_rate_limiting_delay(self, extractor):
        """Test that rate limiting delay is applied"""
        with patch.object(extractor.client, 'get') as mock_get, \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_JIKAN_SEARCH_RESPONSE
            mock_get.return_value = mock_response
            
            await extractor._make_request('/anime', {})
            
            mock_sleep.assert_called_once_with(extractor.rate_limiter.delay)
    
    @pytest.mark.asyncio
    async def test_429_rate_limit_handling(self, extractor):
        """Test handling of 429 rate limit responses with retry"""
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '60'}

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = MOCK_JIKAN_SEARCH_RESPONSE

        with patch.object(extractor.client, 'get', side_effect=[rate_limit_response, success_response]), \
            patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:

            result = await extractor._make_request('/anime', {})

            # Verify final success result
            assert result == MOCK_JIKAN_SEARCH_RESPONSE

            # Verify that we slept for both rate limit delay and retry-after
            mock_sleep.assert_any_call(60)

        
    @pytest.mark.asyncio
    async def test_http_error_handling(self, extractor):
        """Test handling of HTTP errors"""
        with patch.object(extractor.client, 'get') as mock_get:
            # Mock 500 error
            mock_get.side_effect = httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )
            
            with pytest.raises(JikanAPIError, match="HTTP error"):
                await extractor._make_request('/anime', {})
    
    @pytest.mark.asyncio
    async def test_fetch_anime_search_single_page(self, extractor):
        """Test fetching anime search results for single page"""
        with patch.object(extractor, '_make_request', return_value=MOCK_JIKAN_SEARCH_RESPONSE):
            result = await extractor.fetch_anime_search({'limit': 25})
            
            assert len(result) == 2  # Two anime in mock data
            assert all(isinstance(anime, JikanAnime) for anime in result)
            assert result[0].mal_id == 1
            assert result[0].title == "Cowboy Bebop"
            assert result[1].mal_id == 5
            assert result[1].title == "Fullmetal Alchemist"
    
    @pytest.mark.asyncio
    async def test_fetch_anime_search_pagination(self, extractor):
        """Test fetching anime search results with pagination"""
        # Mock first page with next page available
        first_page = {
            "data": [MOCK_JIKAN_SEARCH_RESPONSE["data"][0]],
            "pagination": {
                "last_visible_page": 2,
                "has_next_page": True,
                "current_page": 1,
                "items": {"count": 1, "total": 2, "per_page": 1}
            }
        }
        
        # Mock second page (final)
        second_page = {
            "data": [MOCK_JIKAN_SEARCH_RESPONSE["data"][1]],
            "pagination": {
                "last_visible_page": 2,
                "has_next_page": False,
                "current_page": 2,
                "items": {"count": 1, "total": 2, "per_page": 1}
            }
        }
        
        with patch.object(extractor, '_make_request', side_effect=[first_page, second_page]):
            result = await extractor.fetch_anime_search({'limit': 1})
            
            assert len(result) == 2
            assert result[0].title == "Cowboy Bebop"
            assert result[1].title == "Fullmetal Alchemist"
    
    @pytest.mark.asyncio
    async def test_fetch_anime_search_max_pages_limit(self, extractor):
        """Test respecting max_pages parameter"""
        # Mock response that would have more pages
        paginated_response = {
            "data": [MOCK_JIKAN_SEARCH_RESPONSE["data"][0]],
            "pagination": {
                "last_visible_page": 5,
                "has_next_page": True,
                "current_page": 1,
                "items": {"count": 1, "total": 5, "per_page": 1}
            }
        }
        
        with patch.object(extractor, '_make_request', return_value=paginated_response):
            result = await extractor.fetch_anime_search({'limit': 1}, max_pages=1)
            
            assert len(result) == 1  # Only one page fetched
    
    @pytest.mark.asyncio
    async def test_fetch_top_anime(self, extractor):
        """Test fetching top anime with correct parameters"""
        with patch.object(extractor, 'fetch_anime_search') as mock_fetch:
            mock_fetch.return_value = [JikanAnime(**MOCK_JIKAN_SEARCH_RESPONSE["data"][0])]
            
            result = await extractor.fetch_top_anime(limit=50)
            
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            params = call_args[0][0]  # First positional argument
            
            assert params['order_by'] == 'score'
            assert params['sort'] == 'desc'
            assert params['limit'] == 25  # API limit per page
            assert params['status'] == 'complete'
    
    @pytest.mark.asyncio
    async def test_fetch_seasonal_anime(self, extractor):
        """Test fetching seasonal anime with correct parameters"""
        with patch.object(extractor, 'fetch_anime_search') as mock_fetch:
            mock_fetch.return_value = []
            
            await extractor.fetch_seasonal_anime('summer', 2024, limit=25)
            
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            params = call_args[0][0]
            
            assert params['season'] == 'summer'
            assert params['year'] == 2024
            assert params['order_by'] == 'popularity'
            assert params['sort'] == 'desc'
    
    @pytest.mark.asyncio
    async def test_fetch_anime_search_api_error_handling(self, extractor):
        """Test handling of JikanAPIError during pagination"""
        # Mock first page success, second page fails
        first_page = {
            "data": [MOCK_JIKAN_SEARCH_RESPONSE["data"][0]],
            "pagination": {
                "last_visible_page": 2,
                "has_next_page": True,
                "current_page": 1,
                "items": {"count": 1, "total": 2, "per_page": 1}
            }
        }
        
        async def mock_request_side_effect(endpoint, params):
            if params.get("page") == 1:
                return first_page
            else:
                # Simulate API error on second page
                raise JikanAPIError("API error on page 2")
        
        with patch.object(extractor, '_make_request', side_effect=mock_request_side_effect):
            result = await extractor.fetch_anime_search({'limit': 1})
            
            # Should return results from first page only, stop on error
            assert len(result) == 1
            assert result[0].title == "Cowboy Bebop"

    @pytest.mark.asyncio
    async def test_fetch_upcoming_anime(self, extractor):
        """Test fetching upcoming anime with correct parameters"""
        with patch.object(extractor, 'fetch_anime_search') as mock_fetch:
            mock_fetch.return_value = []
            
            await extractor.fetch_upcoming_anime(limit=25)
            
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            params = call_args[0][0]
            
            assert params['status'] == 'upcoming'
            assert params['order_by'] == 'popularity'
            assert params['sort'] == 'desc'
    
    @pytest.mark.asyncio
    async def test_fetch_by_job_config(self, extractor):
        """Test fetching anime using job configuration"""
        with patch.object(extractor, 'fetch_anime_search') as mock_fetch:
            mock_fetch.return_value = []
            
            await extractor.fetch_by_job_config(MOCK_ETL_JOB_CONFIG)
            
            mock_fetch.assert_called_once_with(MOCK_ETL_JOB_CONFIG['params'], max_pages=None)
    
    @pytest.mark.asyncio
    async def test_fetch_by_job_config_unsupported_endpoint(self, extractor):
        """Test error handling for unsupported endpoints"""
        invalid_config = {
            "endpoint": "/unsupported",
            "params": {},
            "snapshot_type": "test"
        }
        
        with pytest.raises(ValueError, match="Unsupported endpoint"):
            await extractor.fetch_by_job_config(invalid_config)
    
    @pytest.mark.asyncio
    async def test_invalid_json_response_handling(self, extractor):
        """Test handling of invalid JSON responses"""
        invalid_response = {
            "data": "invalid_structure",  # Should be a list
            "pagination": {}
        }
        
        with patch.object(extractor, '_make_request', return_value=invalid_response):
            result = await extractor.fetch_anime_search({'limit': 25})
            
            # Should return empty list when parsing fails
            assert result == []
    
    @pytest.mark.asyncio
    async def test_context_manager_usage(self):
        """Test using JikanExtractor as async context manager"""
        async with JikanExtractor() as extractor:
            assert isinstance(extractor, JikanExtractor)
            assert extractor.client is not None
        
        # Client should be closed after context
        # Note: We can't easily test if client is closed without accessing private attributes
    
    def test_create_extractor_function(self):
        """Test the create_extractor utility function"""
        from src.extractors.jikan import create_extractor
        
        extractor = create_extractor()
        assert isinstance(extractor, JikanExtractor)
    
    @pytest.mark.asyncio
    async def test_user_agent_header(self, extractor):
        """Test that User-Agent header is set correctly"""
        with patch.object(extractor.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_JIKAN_SEARCH_RESPONSE
            mock_get.return_value = mock_response
            
            await extractor._make_request('/anime', {})
            
            # Check that client was initialized with correct headers
            assert extractor.client.headers['User-Agent'] == 'AnimeDashboard-ETL/1.0'


if __name__ == "__main__":
    pytest.main([__file__])
