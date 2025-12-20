"""
Tests for search functionality.
Tests the SearchService, SearchRepository, and search API endpoints.
"""

import pytest
from unittest.mock import Mock
from app.services.search.search_service import SearchService
from app.services.search.search_repository import SearchRepository
from app.services.search.search_track import SearchTrack
from app.services.search.search_types import TrackSearchHit
from app.models.ODSTrackSearch import ODSTrackSearch


class TestSearchService:
    """Test cases for SearchService."""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock Flask app."""
        app = Mock()
        app.settings = Mock()
        app.db_session_factory = Mock()
        app._db_session_factory = Mock()
        return app
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock SearchRepository."""
        return Mock(spec=SearchRepository)
    
    @pytest.fixture
    def mock_track_search(self):
        """Create a mock SearchTrack."""
        return Mock(spec=SearchTrack)
    
    @pytest.fixture
    def search_service(self, mock_app):
        """Create a SearchService instance with mocked dependencies."""
        service = SearchService(mock_app)
        service._repo = Mock(spec=SearchRepository)
        service._track_search = Mock(spec=SearchTrack)
        return service
    
    def test_search_with_valid_query(self, search_service):
        """Test search with valid query returns results."""
        mock_result = {
            "query": "test",
            "results": [
                {
                    "track_id": 1,
                    "track_title": "Test Track",
                    "artist_names": "Test Artist",
                    "album_titles": "Test Album",
                    "genre_names": "Rock",
                    "score": 0.9,
                    "source": "fts"
                }
            ],
            "used": {"fts": True, "trigram": False}
        }
        
        search_service._track_search.search_tracks.return_value = mock_result
        
        result = search_service.search("test", limit=25)
        
        assert result["query"] == "test"
        assert len(result["results"]) == 1
        assert result["results"][0]["track_id"] == 1
        search_service._track_search.search_tracks.assert_called_once_with("test", limit=25)
    
    def test_refresh_index(self, search_service):
        """Test refreshing the search index."""
        search_service._repo.refresh_search_index.return_value = True
        
        result = search_service.refresh_index()
        
        assert result is True
        search_service._repo.refresh_search_index.assert_called_once()
    
    def test_get_stats(self, search_service):
        """Test getting search index statistics."""
        search_service._repo.get_total_tracks.return_value = 100
        
        result = search_service.get_stats()
        
        assert result["total_tracks"] == 100
        assert result["index_name"] == "ods_track_search"


class TestSearchTrack:
    """Test cases for SearchTrack."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock SearchRepository."""
        return Mock(spec=SearchRepository)
    
    @pytest.fixture
    def search_track(self, mock_repository):
        """Create a SearchTrack instance."""
        return SearchTrack(mock_repository)
    
    def test_search_empty_query(self, search_track):
        """Test search with empty query."""
        result = search_track.search_tracks("")
        
        assert result["query"] == ""
        assert result["results"] == []
        assert result["used"]["fts"] is False
        assert result["used"]["trigram"] is False
    
    def test_search_short_query_prefers_trigram(self, search_track, mock_repository):
        """Test that short queries (<=3 chars) prefer trigram."""
        mock_hit = TrackSearchHit(
            track_id=1,
            track_title="ABC",
            artist_names="Artist",
            album_titles="Album",
            genre_names="Pop",
            score=0.8,
            source="trigram"
        )
        mock_repository.trigram_search.return_value = [mock_hit]
        
        result = search_track.search_tracks("abc")
        
        # Should only use trigram for short queries
        assert result["used"]["fts"] is False
        assert result["used"]["trigram"] is True
        mock_repository.trigram_search.assert_called_once()
    
    def test_search_long_query_uses_fts_first(self, search_track, mock_repository):
        """Test that longer queries use FTS first."""
        mock_hit = TrackSearchHit(
            track_id=1,
            track_title="Long Track Name",
            artist_names="Artist",
            album_titles="Album",
            genre_names="Rock",
            score=0.9,
            source="fts"
        )
        mock_repository.fts_search.return_value = [mock_hit] * 10  # Return enough results
        
        result = search_track.search_tracks("long track name")
        
        # Should use FTS for longer queries and not need trigram
        assert result["used"]["fts"] is True
        assert result["used"]["trigram"] is False
        mock_repository.fts_search.assert_called_once()
    
    def test_merge_best_deduplicates(self, search_track, mock_repository):
        """Test that merge_best deduplicates and picks highest score."""
        hit1 = TrackSearchHit(1, "Track", "Artist", "Album", "Rock", 0.8, "fts")
        hit2 = TrackSearchHit(1, "Track", "Artist", "Album", "Rock", 0.9, "trigram")
        hit3 = TrackSearchHit(2, "Track2", "Artist2", "Album2", "Pop", 0.7, "fts")
        
        merged = search_track._merge_best([hit1], [hit2, hit3], limit=10)
        
        assert len(merged) == 2
        # Should keep hit2 (score 0.9) over hit1 (score 0.8) for track_id=1
        assert merged[0].track_id == 1
        assert merged[0].score == 0.9


class TestODSTrackSearchModel:
    """Test cases for ODSTrackSearch model."""
    
    def test_model_to_dict(self):
        """Test converting model to dictionary."""
        track = ODSTrackSearch()
        track.track_id = 1
        track.track_title = "Test Track"
        track.artist_names = "Artist 1, Artist 2"
        track.album_titles = "Test Album"
        track.genre_names = "Rock, Pop"
        track.duration_ms = 180000
        track.spotify_id = "spotify123"
        track.date_added = None
        track.updated_at = None
        
        result = track.to_dict()
        
        assert result["track_id"] == 1
        assert result["title"] == "Test Track"
        assert result["artist_names"] == "Artist 1, Artist 2"
        assert result["album_title"] == "Test Album"
        assert result["genre_names"] == "Rock, Pop"
        assert result["duration_ms"] == 180000
        assert result["spotify_id"] == "spotify123"
    
    def test_model_repr(self):
        """Test model string representation."""
        track = ODSTrackSearch()
        track.track_id = 1
        track.track_title = "Test Track"
        track.artist_names = "Test Artist"
        
        repr_str = repr(track)
        
        assert "ODSTrackSearch" in repr_str
        assert "track_id=1" in repr_str
        assert "Test Track" in repr_str
