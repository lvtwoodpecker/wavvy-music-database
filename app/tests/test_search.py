"""
Tests for search functionality.
Tests the SearchService, SearchRepository, and search API endpoints.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.search.search_service import SearchService
from app.services.search.search_repository import SearchRepository
from app.models.ODSTrackSearch import ODSTrackSearch


class TestSearchService:
    """Test cases for SearchService."""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock Flask app."""
        app = Mock()
        app.settings = Mock()
        app.db_session_factory = Mock()
        return app
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock SearchRepository."""
        return Mock(spec=SearchRepository)
    
    @pytest.fixture
    def search_service(self, mock_app, mock_repository):
        """Create a SearchService instance with mocked dependencies."""
        service = SearchService(mock_app)
        service._repository = mock_repository
        return service
    
    def test_search_with_empty_query(self, search_service):
        """Test search with empty query returns empty results."""
        result = search_service.search("")
        
        assert result["results"] == []
        assert result["count"] == 0
        assert result["query"] == ""
    
    def test_search_with_valid_query(self, search_service, mock_repository):
        """Test search with valid query returns results."""
        mock_track = Mock(spec=ODSTrackSearch)
        mock_track.track_id = 1
        mock_track.title = "Test Track"
        mock_track.to_dict = lambda: {
            "track_id": 1,
            "title": "Test Track",
            "artist_names": "Test Artist"
        }
        
        mock_repository.search_tracks_hybrid.return_value = [mock_track]
        
        result = search_service.search("test", mode="hybrid", limit=50)
        
        assert len(result["results"]) == 1
        assert result["results"][0]["track_id"] == 1
        assert result["query"] == "test"
        assert result["count"] == 1
    
    def test_search_mode_fts(self, search_service, mock_repository):
        """Test search with FTS mode."""
        mock_repository.search_tracks_fts.return_value = []
        
        result = search_service.search("test", mode="fts")
        
        mock_repository.search_tracks_fts.assert_called_once()
        assert result["results"] == []
    
    def test_search_mode_fuzzy(self, search_service, mock_repository):
        """Test search with fuzzy mode."""
        mock_repository.search_tracks_fuzzy.return_value = []
        
        result = search_service.search("test", mode="fuzzy")
        
        mock_repository.search_tracks_fuzzy.assert_called_once()
        assert result["results"] == []
    
    def test_search_limit_clamping(self, search_service, mock_repository):
        """Test that limit is clamped to valid range."""
        mock_repository.search_tracks_hybrid.return_value = []
        
        # Test upper bound
        search_service.search("test", limit=200)
        args, kwargs = mock_repository.search_tracks_hybrid.call_args
        assert args[1] == 100  # limit is second positional arg
        
        # Test lower bound
        search_service.search("test", limit=-5)
        args, kwargs = mock_repository.search_tracks_hybrid.call_args
        assert args[1] == 1  # limit is second positional arg
    
    def test_sanitize_query(self, search_service):
        """Test query sanitization."""
        # Test whitespace stripping
        assert search_service._sanitize_query("  test  ") == "test"
        
        # Test length limiting
        long_query = "a" * 300
        result = search_service._sanitize_query(long_query)
        assert len(result) == 200
        
        # Test empty query
        assert search_service._sanitize_query("") == ""
        assert search_service._sanitize_query(None) == ""
    
    def test_search_by_title(self, search_service, mock_repository):
        """Test searching by title."""
        mock_repository.search_tracks_hybrid.return_value = []
        
        result = search_service.search_by_title("Test Title")
        
        assert isinstance(result, list)
        mock_repository.search_tracks_hybrid.assert_called_once()
    
    def test_search_by_artist(self, search_service, mock_repository):
        """Test searching by artist."""
        mock_repository.search_tracks_hybrid.return_value = []
        
        result = search_service.search_by_artist("Test Artist")
        
        assert isinstance(result, list)
        mock_repository.search_tracks_hybrid.assert_called_once()
    
    def test_get_track(self, search_service, mock_repository):
        """Test getting a single track by ID."""
        mock_track = Mock(spec=ODSTrackSearch)
        mock_track.to_dict = lambda: {"track_id": 1, "title": "Test"}
        mock_repository.get_track_by_id.return_value = mock_track
        
        result = search_service.get_track(1)
        
        assert result is not None
        assert result["track_id"] == 1
        mock_repository.get_track_by_id.assert_called_once_with(1)
    
    def test_get_track_not_found(self, search_service, mock_repository):
        """Test getting a track that doesn't exist."""
        mock_repository.get_track_by_id.return_value = None
        
        result = search_service.get_track(999)
        
        assert result is None
    
    def test_refresh_index(self, search_service, mock_repository):
        """Test refreshing the search index."""
        mock_repository.refresh_search_index.return_value = True
        
        result = search_service.refresh_index()
        
        assert result is True
        mock_repository.refresh_search_index.assert_called_once()
    
    def test_get_stats(self, search_service, mock_repository):
        """Test getting search index statistics."""
        mock_repository.get_total_tracks.return_value = 100
        
        result = search_service.get_stats()
        
        assert result["total_tracks"] == 100
        assert result["index_name"] == "ods_track_search"


class TestODSTrackSearchModel:
    """Test cases for ODSTrackSearch model."""
    
    def test_model_to_dict(self):
        """Test converting model to dictionary."""
        track = ODSTrackSearch()
        track.track_id = 1
        track.title = "Test Track"
        track.artist_names = "Artist 1, Artist 2"
        track.album_title = "Test Album"
        track.genre_names = "Rock, Pop"
        track.duration_ms = 180000
        track.audio_file_url = "http://example.com/audio.mp3"
        track.cover_image_url = "http://example.com/cover.jpg"
        track.updated_at = None
        
        result = track.to_dict()
        
        assert result["track_id"] == 1
        assert result["title"] == "Test Track"
        assert result["artist_names"] == "Artist 1, Artist 2"
        assert result["album_title"] == "Test Album"
        assert result["genre_names"] == "Rock, Pop"
        assert result["duration_ms"] == 180000
    
    def test_model_repr(self):
        """Test model string representation."""
        track = ODSTrackSearch()
        track.track_id = 1
        track.title = "Test Track"
        track.artist_names = "Test Artist"
        
        repr_str = repr(track)
        
        assert "ODSTrackSearch" in repr_str
        assert "track_id=1" in repr_str
        assert "Test Track" in repr_str


def test_query_sanitization():
    """Test various query sanitization scenarios."""
    # Mock app for service initialization
    mock_app = Mock()
    mock_app.settings = Mock()
    mock_app.db_session_factory = Mock()
    
    service = SearchService(mock_app)
    service._repository = Mock()
    
    # Test whitespace handling
    assert service._sanitize_query("   hello   ") == "hello"
    
    # Test length limiting
    long_query = "x" * 250
    result = service._sanitize_query(long_query)
    assert len(result) <= 200
    
    # Test None handling
    assert service._sanitize_query(None) == ""
