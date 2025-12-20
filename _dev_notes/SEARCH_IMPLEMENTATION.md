# ODS Track Search Implementation

## Overview

This implementation provides a high-performance search engine for tracks using PostgreSQL's Full-Text Search (FTS) and trigram fuzzy matching. The search is backed by the `ods_track_search` table, which is an Operational Data Store (ODS) - a denormalized view optimized for search operations.

## Architecture

### Components

1. **Database Layer** (`migrations/create_ods_track_search.sql`)
   - Denormalized search table with FTS and trigram indexes
   - Automatic search vector updates via triggers
   - Batch refresh function for rebuilding the index

2. **ORM Model** (`app/models/ODSTrackSearch.py`)
   - SQLAlchemy model for the search table
   - Serialization methods for API responses

3. **Repository** (`app/services/search/search_repository.py`)
   - Data access layer
   - Three search strategies: FTS, Fuzzy, and Hybrid

4. **Service** (`app/services/search/search_service.py`)
   - Business logic layer
   - Query validation and sanitization
   - Result formatting

5. **API Routes** (`app/api/search_routes.py`)
   - RESTful endpoints for search operations

## Setup

### 1. Run the Migration

Execute the SQL migration to create the search table and indexes:

```bash
psql -d your_database -f migrations/create_ods_track_search.sql
```

### 2. Populate the Search Index

After running the migration, populate the search index with existing data:

```sql
SELECT refresh_ods_track_search();
```

Or use the API endpoint:

```bash
curl -X POST http://localhost:5000/api/search/refresh \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## API Endpoints

### Search Tracks

**Endpoint:** `GET /api/search?q={query}&mode={mode}&limit={limit}&offset={offset}`

**Parameters:**
- `q` (required): Search query string
- `mode` (optional): Search mode - `fts`, `fuzzy`, or `hybrid` (default: `hybrid`)
  - `fts`: Full-text search only (exact word matching, ranked results)
  - `fuzzy`: Trigram similarity only (handles typos, partial matches)
  - `hybrid`: Combines both strategies for best results
- `limit` (optional): Max results (1-100, default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "results": [
    {
      "track_id": 123,
      "title": "Song Title",
      "artist_names": "Artist 1, Artist 2",
      "album_title": "Album Name",
      "genre_names": "Rock, Pop",
      "duration_ms": 240000,
      "audio_file_url": "https://...",
      "cover_image_url": "https://..."
    }
  ],
  "query": "search term",
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

**Examples:**
```bash
# Basic search (hybrid mode)
curl "http://localhost:5000/api/search?q=bohemian+rhapsody" \
  -H "Authorization: Bearer YOUR_TOKEN"

# FTS search with pagination
curl "http://localhost:5000/api/search?q=queen&mode=fts&limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Fuzzy search (good for typos)
curl "http://localhost:5000/api/search?q=bihemian&mode=fuzzy" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search by Title

**Endpoint:** `GET /api/search/by-title?title={title}&limit={limit}`

Search specifically by track title.

**Example:**
```bash
curl "http://localhost:5000/api/search/by-title?title=imagine&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search by Artist

**Endpoint:** `GET /api/search/by-artist?artist={artist}&limit={limit}`

Search tracks by artist name.

**Example:**
```bash
curl "http://localhost:5000/api/search/by-artist?artist=beatles&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Track by ID

**Endpoint:** `GET /api/search/track/{track_id}`

Get a single track from the search index.

**Example:**
```bash
curl "http://localhost:5000/api/search/track/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Refresh Search Index

**Endpoint:** `POST /api/search/refresh`

Rebuild the entire search index from source tables. Use this after bulk updates to tracks, artists, or albums.

**Example:**
```bash
curl -X POST "http://localhost:5000/api/search/refresh" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Index Statistics

**Endpoint:** `GET /api/search/stats`

Get statistics about the search index.

**Response:**
```json
{
  "total_tracks": 1000,
  "index_name": "ods_track_search"
}
```

## Integration with Library

The search is also integrated with the library tracks endpoint. You can now filter library tracks using a search query:

**Endpoint:** `GET /api/library/tracks?q={query}&limit={limit}`

**Example:**
```bash
# Get all tracks
curl "http://localhost:5000/api/library/tracks" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter tracks with search
curl "http://localhost:5000/api/library/tracks?q=rock&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Search Modes Explained

### Full-Text Search (FTS)
- Uses PostgreSQL's `tsvector` and `tsquery`
- Weighted ranking: Title (A) > Artist (B) > Album (C) > Genre (D)
- Fast and accurate for exact word matches
- Supports boolean operators and phrase matching
- Best for: Precise searches with correct spelling

### Fuzzy Search (Trigram)
- Uses PostgreSQL's `pg_trgm` extension
- Calculates similarity scores between strings
- Tolerates typos and partial matches
- Threshold: 0.3 (30% similarity minimum)
- Best for: Handling typos and partial names

### Hybrid Search (Recommended)
- Combines both FTS and fuzzy matching
- First tries FTS for exact matches
- Falls back to fuzzy search if few results
- Deduplicates results
- Best for: General-purpose search

## Performance Considerations

1. **Indexes:**
   - GIN index on `search_vector` for FTS
   - GIN trigram indexes on title, artist_names, and album_title
   - These indexes make searches very fast even with large datasets

2. **Denormalization:**
   - The `ods_track_search` table duplicates data from Track, Artist, Album, and Genre tables
   - This trade-off improves search performance at the cost of storage
   - Keep the index updated using the refresh function

3. **Query Limits:**
   - Maximum query length: 200 characters
   - Maximum results per request: 100
   - Use pagination for large result sets

## Maintenance

### When to Refresh the Index

Refresh the search index when:
- New tracks are added
- Track metadata is updated (title, artist, album, genre)
- Artist names are changed
- Album titles are changed

### Automatic Refresh (Future Enhancement)

Consider setting up automatic index refresh using:
- Database triggers on Track, Artist, Album, Genre changes
- Scheduled jobs (e.g., nightly refresh)
- Event-driven updates using message queues

## Testing

Run the test suite:

```bash
python3 -m pytest app/tests/test_search.py -v
```

All 15 tests should pass:
- Search service functionality
- Query sanitization
- Search mode selection
- Model serialization
- Error handling

## Troubleshooting

### Search returns no results
1. Check if the search index is populated: `GET /api/search/stats`
2. If total_tracks is 0, run: `POST /api/search/refresh`
3. Verify the database has track data in the Track, Artist, Album tables

### Search is slow
1. Check if indexes exist:
   ```sql
   SELECT indexname FROM pg_indexes WHERE tablename = 'ods_track_search';
   ```
2. Ensure pg_trgm extension is enabled:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'pg_trgm';
   ```

### Error: "pg_trgm extension not found"
Install the extension:
```sql
CREATE EXTENSION pg_trgm;
```

## Future Enhancements

Potential improvements:
1. Real-time index updates via database triggers
2. Search suggestions/autocomplete
3. Advanced filters (by genre, year, duration range)
4. Search history and popular searches
5. Personalized search ranking based on user preferences
6. Spell correction suggestions
7. Search analytics and logging
