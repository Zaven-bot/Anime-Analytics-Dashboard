"""
Unit tests for ETL configuration and settings.
Tests config loading, validation, and ETL job definitions.
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

# Add ETL src to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/etl'))

from src.config import ETLSettings, get_settings, ETL_JOBS

@pytest.mark.unit
class TestETLSettings:
    """Test ETL settings configuration and validation"""
    
    def test_configuration_loads_with_valid_values(self):
        """Test that configuration loads successfully with valid values in any environment"""
        settings = ETLSettings()
        
        # Test that URLs are properly formatted
        assert settings.database_url.startswith("postgresql://")
        assert "localhost" in settings.database_url
        assert settings.redis_url.startswith("redis://")
        assert settings.jikan_base_url == "https://api.jikan.moe/v4"
        
        # Test that numeric values are within valid ranges
        assert settings.jikan_rate_limit_delay >= 0.1  # Minimum valid delay
        assert settings.jikan_max_retries >= 1
        assert settings.jikan_timeout > 0
        
        # Test boolean and string values are set
        assert isinstance(settings.debug, bool)
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        # Test that limits are positive integers
        assert settings.top_anime_limit > 0
        assert settings.seasonal_anime_limit > 0
        assert settings.upcoming_anime_limit > 0
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@testhost:5432/testdb',
            'REDIS_URL': 'redis://testhost:6379',
            'JIKAN_RATE_LIMIT_DELAY': '2.5',
            'DEBUG': 'True',
            'LOG_LEVEL': 'DEBUG'
        }):
            settings = ETLSettings()
            
            assert settings.database_url == 'postgresql://test:test@testhost:5432/testdb'
            assert settings.redis_url == 'redis://testhost:6379'
            assert settings.jikan_rate_limit_delay == 2.5
            assert settings.debug is True
            assert settings.log_level == 'DEBUG'
    
    
    def test_rate_limit_validation(self):
        """Test that rate limit delay validation works"""
        # Test that explicit values override any environment settings
        with patch.dict(os.environ, {}, clear=True):
            # Valid rate limit
            settings = ETLSettings(jikan_rate_limit_delay=0.5)
            assert settings.jikan_rate_limit_delay == 0.5
            
            # Invalid rate limit (too low)
            with pytest.raises(ValidationError) as exc_info:
                ETLSettings(jikan_rate_limit_delay=0.05)
            
            assert "Rate limit delay must be at least 0.1 seconds" in str(exc_info.value)
    
    def test_get_settings_function(self):
        """Test the get_settings convenience function"""
        settings = get_settings()
        assert isinstance(settings, ETLSettings)
        assert settings.database_url is not None
    
    
    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive"""
        with patch.dict(os.environ, {
            'database_url': 'postgresql://lowercase:test@localhost:5432/test',
            'REDIS_URL': 'redis://uppercase:6379'
        }, clear=True):
            settings = ETLSettings()
            assert settings.database_url == 'postgresql://lowercase:test@localhost:5432/test'
            assert settings.redis_url == 'redis://uppercase:6379'

@pytest.mark.unit
class TestETLJobs:
    """Test ETL job configuration definitions"""
    
    def test_etl_jobs_exist(self):
        """Test that all expected ETL jobs are defined"""
        expected_jobs = ['top_anime', 'seasonal_current', 'seasonal_upcoming', 'popular_movies']
        
        for job_name in expected_jobs:
            assert job_name in ETL_JOBS, f"ETL job '{job_name}' not found"
    
    def test_job_structure(self):
        """Test that each job has the required structure"""
        required_fields = ['endpoint', 'params', 'snapshot_type', 'description']
        
        for job_name, job_config in ETL_JOBS.items():
            for field in required_fields:
                assert field in job_config, f"Job '{job_name}' missing field '{field}'"
            
            # Test specific field types
            assert isinstance(job_config['endpoint'], str)
            assert isinstance(job_config['params'], dict)
            assert isinstance(job_config['snapshot_type'], str)
            assert isinstance(job_config['description'], str)
    
    def test_top_anime_job_config(self):
        """Test top anime job configuration"""
        job = ETL_JOBS['top_anime']
        
        assert job['endpoint'] == '/anime'
        assert job['params']['order_by'] == 'score'
        assert job['params']['sort'] == 'desc'
        assert job['params']['limit'] == 25
        assert job['params']['status'] == 'complete'
        assert job['snapshot_type'] == 'top'
        assert 'top-rated' in job['description'].lower()
    
    def test_seasonal_current_job_config(self):
        """Test seasonal current job configuration"""
        job = ETL_JOBS['seasonal_current']
        
        assert job['endpoint'] == '/anime'
        assert job['params']['order_by'] == 'score'
        assert 'season' not in job['params']  # Current season auto-detected
        assert job['snapshot_type'] == 'seasonal_current'
    
    def test_upcoming_job_config(self):
        """Test upcoming anime job configuration"""
        job = ETL_JOBS['seasonal_upcoming']
        
        assert job['endpoint'] == '/anime'
        assert job['params']['order_by'] == 'score'
        assert job['params']['status'] == 'upcoming'
        assert job['snapshot_type'] == 'upcoming'
    
    def test_popular_movies_job_config(self):
        """Test popular movies job configuration"""
        job = ETL_JOBS['popular_movies']
        
        assert job['endpoint'] == '/anime'
        assert job['params']['type'] == 'movie'
        assert job['params']['order_by'] == 'score'
        assert job['params']['sort'] == 'desc'
        assert job['params']['limit'] == 25
        assert job['snapshot_type'] == 'popular_movies'
        assert 'movie' in job['description'].lower()
    
    def test_job_params_are_valid(self):
        """Test that job parameters contain valid Jikan API values"""
        valid_order_by = ['mal_id', 'title', 'start_date', 'end_date', 'episodes', 
                         'score', 'scored_by', 'rank', 'popularity', 'members', 'favorites']
        valid_sort = ['desc', 'asc']
        valid_status = ['airing', 'complete', 'upcoming']
        valid_type = ['tv', 'movie', 'ova', 'special', 'ona', 'music', 'cm', 'pv', 'tv_special']
        
        for job_name, job_config in ETL_JOBS.items():
            params = job_config['params']
            
            if 'order_by' in params:
                assert params['order_by'] in valid_order_by, \
                    f"Invalid order_by in {job_name}: {params['order_by']}"
            
            if 'sort' in params:
                assert params['sort'] in valid_sort, \
                    f"Invalid sort in {job_name}: {params['sort']}"
            
            if 'status' in params:
                assert params['status'] in valid_status, \
                    f"Invalid status in {job_name}: {params['status']}"
            
            if 'type' in params:
                assert params['type'] in valid_type, \
                    f"Invalid type in {job_name}: {params['type']}"
            
            if 'limit' in params:
                assert isinstance(params['limit'], int), \
                    f"Limit should be int in {job_name}"
                assert 1 <= params['limit'] <= 100, \
                    f"Limit should be 1-100 in {job_name}: {params['limit']}"


if __name__ == "__main__":
    pytest.main([__file__])
