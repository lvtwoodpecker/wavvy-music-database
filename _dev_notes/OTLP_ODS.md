## Search Architecture (OLTP + ODS)

Wavvy separates transactional workloads from search workloads to ensure both data integrity and fast query performance.

### OLTP (Transactional Layer)
- Fully normalized PostgreSQL schema
- Source of truth for:
  - Users, Tracks, Artists, Albums, Genres
  - Play history, playlists, subscriptions, advertisers
- Optimized for correctness and write-heavy operations
- Join tables indexed to support common access patterns

### ODS (Search Read Model)
- Denormalized table: `ods_track_search`
- Materializes track metadata with aggregated:
  - artist names
  - album titles
  - genre names
- Stores:
  - `search_tsv` (tsvector) for full-text search
  - normalized text columns for trigram search
- Refreshed via an UPSERT query from OLTP tables

### Search Optimization
- PostgreSQL Full-Text Search (GIN index on `search_tsv`)
- Trigram similarity for typo/partial matching
- Normalized columns used to avoid IMMUTABLE function issues in indexes
- No runtime joins during search queries

### ORM & Service Layer
- `ODSTrackSearch` ORM model represents the search surface
- Search logic implemented in `services/search/`
- ORM-based queries using Postgres-specific operators
- Clean separation between:
  - database access
  - business logic
  - API routes

### API
- `GET /api/search?q=...`
- Dynamically selects FTS or trigram search
- Merges and ranks results before returning JSON

This design enables fast, scalable music search while keeping the core OLTP schema clean and maintainable.
