"""
Unit tests for database loader.
Tests DB insert/upsert behavior, error handling, and connection management.
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

# Add ETL src to path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/etl'))

from src.loaders.database import DatabaseLoader
from src.models.jikan import AnimeSnapshot
from tests.fixtures.mock_data import SAMPLE_ANIME_SNAPSHOT

@pytest.mark.unit
class TestDatabaseLoader:
    """Test database loader functionality"""
    
    @pytest.fixture
    def loader(self):
        """Create a DatabaseLoader instance for testing"""
        with patch('src.loaders.database.create_engine'), \
             patch('src.loaders.database.sessionmaker'):
            return DatabaseLoader()
    
    @pytest.fixture
    def sample_snapshot(self):
        """Create a sample AnimeSnapshot for testing"""
        return AnimeSnapshot(**SAMPLE_ANIME_SNAPSHOT)
    
    @pytest.fixture
    def sample_snapshots(self):
        """Create a list of sample AnimeSnapshots for testing"""
        snapshot1 = SAMPLE_ANIME_SNAPSHOT.copy()
        snapshot1["mal_id"] = 1
        snapshot1["title"] = "Test Anime 1"
        
        snapshot2 = SAMPLE_ANIME_SNAPSHOT.copy()
        snapshot2["mal_id"] = 2
        snapshot2["title"] = "Test Anime 2"
        
        return [
            AnimeSnapshot(**snapshot1),
            AnimeSnapshot(**snapshot2)
        ]
    
    def test_initialization(self, loader):
        """Test that DatabaseLoader initializes correctly"""
        assert loader.settings is not None
        assert loader.engine is not None
        assert loader.SessionLocal is not None
        assert loader.anime_snapshots_table is not None
    
    def test_connection_test_success(self, loader):
        """Test successful database connection test"""
        mock_result = Mock()
        mock_result.fetchone.return_value = [1]
        
        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result
        
        with patch.object(loader.engine, 'connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_connection
            
            result = loader.test_connection()
            
            assert result is True
            mock_connection.execute.assert_called_once()
    
    def test_connection_test_failure(self, loader):
        """Test failed database connection test"""
        with patch.object(loader.engine, 'connect', side_effect=Exception("Connection failed")):
            result = loader.test_connection()
            assert result is False
    
    def test_snapshot_to_dict_conversion(self, loader, sample_snapshot):
        """Test conversion of AnimeSnapshot to dictionary"""
        result = loader._snapshot_to_dict(sample_snapshot)
        
        assert isinstance(result, dict)
        assert result["mal_id"] == sample_snapshot.mal_id
        assert result["title"] == sample_snapshot.title
        assert result["score"] == float(sample_snapshot.score)
        assert result["snapshot_type"] == sample_snapshot.snapshot_type
        assert result["snapshot_date"] == sample_snapshot.snapshot_date
        
        # Test JSON fields are serialized to strings
        assert isinstance(result["genres"], str)
        assert isinstance(result["images"], str)
        
        # Test that JSON strings can be parsed back to original types
        import json
        assert isinstance(json.loads(result["genres"]), list)
        assert isinstance(json.loads(result["images"]), dict)
    
    def test_snapshot_to_dict_with_none_score(self, loader):
        """Test conversion when score is None"""
        snapshot_data = SAMPLE_ANIME_SNAPSHOT.copy()
        snapshot_data["score"] = None
        snapshot = AnimeSnapshot(**snapshot_data)
        
        result = loader._snapshot_to_dict(snapshot)
        assert result["score"] is None
    
    def test_load_snapshots_empty_list(self, loader):
        """Test loading empty list of snapshots"""
        result = loader.load_snapshots([])
        
        assert result["total_snapshots"] == 0
        assert result["successful_inserts"] == 0
        assert result["duplicate_skips"] == 0
        assert result["errors"] == 0
    
    def test_load_snapshots_successful(self, loader, sample_snapshots):
        """Test successful loading of snapshots"""
        mock_session = Mock()
        
        # Mock the execute().fetchone() call for duplicate checking
        mock_result = Mock()
        mock_result.fetchone.return_value = None  # No existing records
        mock_session.execute.return_value = mock_result
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader.load_snapshots(sample_snapshots, batch_size=2, upsert=True)
            
            assert result["total_snapshots"] == 2
            assert result["successful_inserts"] == 2
            assert result["errors"] == 0
            
            # Verify session operations
            mock_session.commit.assert_called()
            mock_session.close.assert_called()
    
    def test_load_snapshots_with_duplicates(self, loader, sample_snapshots):
        """Test loading snapshots with duplicate detection"""
        mock_session = Mock()
        # Mock existing record for first snapshot
        mock_session.execute.side_effect = [
            Mock(fetchone=Mock(return_value=[1])),  # Existing record found
            Mock(fetchone=Mock(return_value=None)),  # No existing record
            None, None  # Insert operations
        ]
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader.load_snapshots(sample_snapshots, batch_size=2, upsert=False)
            
            assert result["total_snapshots"] == 2
            assert result["successful_inserts"] == 1  # Only one inserted
            assert result["duplicate_skips"] == 1  # One duplicate skipped
            assert result["errors"] == 0
    
    def test_load_snapshots_with_sql_error(self, loader, sample_snapshots):
        """Test handling of SQL errors during loading"""
        # Create a mock session
        mock_session = Mock()

        # Mock result for SELECT queries
        mock_result = Mock()
        mock_result.fetchone.return_value = None

        # Configure execute to return SELECT results first,
        # then raise error on INSERT, then SELECTs again
        mock_session.execute.side_effect = [
            mock_result,                         # SELECT (check existing row)
            SQLAlchemyError("Database error"),   # INSERT fails
            mock_result,                         # SELECT for second snapshot
            mock_result                          # INSERT works
        ]

        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader.load_snapshots(sample_snapshots, batch_size=2, upsert=False)
            
            assert result["total_snapshots"] == 2
            assert result["successful_inserts"] == 1  # One succeeded
            assert result["errors"] == 1  # One failed
            assert len(result["error_details"]) == 1
            assert "Database error" in result["error_details"][0]["error"]
    
    def test_load_snapshots_batch_processing(self, loader, sample_snapshots):
        """Test that large lists are processed in batches"""
        # Create more snapshots than batch size
        many_snapshots = sample_snapshots * 3  # 6 snapshots total
        
        mock_session = Mock()
        mock_session.execute.return_value = None
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session), \
             patch.object(loader, '_load_batch', return_value={
                 "successful_inserts": 2,
                 "successful_updates": 0,
                 "duplicate_skips": 0,
                 "errors": 0,
                 "error_details": []
             }) as mock_load_batch:
            
            result = loader.load_snapshots(many_snapshots, batch_size=2)
            
            # Should be called 3 times (6 snapshots / 2 per batch)
            assert mock_load_batch.call_count == 3
            assert result["successful_inserts"] == 6  # 3 batches * 2 each
    
    def test_load_batch_no_rollback_on_inner_exceptions(self, loader, sample_snapshots):
        """Test that session is rolled back on exception"""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Unexpected error")
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader._load_batch(sample_snapshots, upsert=True)
    
            mock_session.rollback.assert_not_called()
            mock_session.close.assert_called_once()
            assert result["errors"] == len(sample_snapshots)
    
    def test_load_batch_rollback_on_commit_exception(self, loader, sample_snapshots):
        """Test that session is rolled back when commit fails"""
        mock_session = Mock()
        # Let execute succeed, but make commit fail
        mock_session.execute.return_value = None
        mock_session.commit.side_effect = Exception("Commit failed")
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader._load_batch(sample_snapshots, upsert=True)
            
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            assert result["errors"] == len(sample_snapshots)

    def test_get_latest_snapshot_date(self, loader):
        """Test getting latest snapshot date"""
        test_date = date(2024, 1, 15)
        mock_session = Mock()
        mock_session.execute.return_value.fetchone.return_value = [test_date]
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader.get_latest_snapshot_date("top")
            
            assert result == test_date
            mock_session.close.assert_called_once()
    
    def test_get_latest_snapshot_date_no_records(self, loader):
        """Test getting latest snapshot date when no records exist"""
        mock_session = Mock()
        mock_session.execute.return_value.fetchone.return_value = [None]
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader.get_latest_snapshot_date("top")
            
            assert result == date.today()
    
    def test_cleanup_old_snapshots(self, loader):
        """Test cleaning up old snapshots"""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader.cleanup_old_snapshots("top", keep_days=30)
            
            assert result == 5
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_cleanup_old_snapshots_with_error(self, loader):
        """Test cleanup with database error"""
        mock_session = Mock()
        mock_session.execute.side_effect = SQLAlchemyError("Delete failed")
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            result = loader.cleanup_old_snapshots("top", keep_days=30)
            
            assert result == 0
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_upsert_sql_generation(self, loader, sample_snapshot):
        """Test that upsert SQL is generated correctly for conflicts"""
        mock_session = Mock()
        
        # Mock the execute().fetchone() call for duplicate checking
        mock_result = Mock()
        mock_result.fetchone.return_value = None  # No existing records
        mock_session.execute.return_value = mock_result
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            loader._load_batch([sample_snapshot], upsert=True)
            
            # Should be called multiple times: SELECT for duplicate check + INSERT with ON CONFLICT
            assert mock_session.execute.call_count >= 2
            
            # Check that one of the SQL calls contains ON CONFLICT clause (the upsert)
            all_calls = mock_session.execute.call_args_list
            sql_texts = [str(call[0][0]) for call in all_calls]
            
            # Look for the ON CONFLICT in any of the SQL statements
            has_on_conflict = any("ON CONFLICT" in sql for sql in sql_texts)
            assert has_on_conflict, f"No ON CONFLICT found in SQL calls: {sql_texts}"
            
            has_do_update = any("DO UPDATE SET" in sql for sql in sql_texts)
            assert has_do_update, f"No DO UPDATE SET found in SQL calls: {sql_texts}"
    
    def test_simple_insert_sql_generation(self, loader, sample_snapshot):
        """Test that simple insert SQL is generated correctly"""
        mock_session = Mock()
        # Mock no existing record
        mock_session.execute.side_effect = [
            Mock(fetchone=Mock(return_value=None)),  # No existing record
            None  # Insert operation
        ]
        
        with patch.object(loader, 'SessionLocal', return_value=mock_session):
            loader._load_batch([sample_snapshot], upsert=False)
            
            # Should be called twice: once for check, once for insert
            assert mock_session.execute.call_count == 2
    
    def test_create_loader_function(self):
        """Test the create_loader utility function"""
        with patch('src.loaders.database.create_engine'), \
             patch('src.loaders.database.sessionmaker'):
            from src.loaders.database import create_loader
            
            loader = create_loader()
            assert isinstance(loader, DatabaseLoader)


if __name__ == "__main__":
    pytest.main([__file__])
