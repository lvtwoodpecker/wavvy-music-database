-- Create ods_track_search table for optimized search with FTS and trigram support
-- This table denormalizes track, artist, album, and genre data for efficient searching

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create the ods_track_search table
CREATE TABLE IF NOT EXISTS public.ods_track_search (
    track_id BIGINT PRIMARY KEY,
    title VARCHAR NOT NULL,
    artist_names TEXT,
    album_title VARCHAR,
    genre_names TEXT,
    duration_ms INTEGER,
    audio_file_url TEXT,
    cover_image_url TEXT,
    search_vector TSVECTOR,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_ods_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id) ON DELETE CASCADE
);

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_ods_track_search_fts ON public.ods_track_search USING GIN (search_vector);

-- Create trigram indexes for fuzzy matching
CREATE INDEX IF NOT EXISTS idx_ods_track_search_title_trgm ON public.ods_track_search USING GIN (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_ods_track_search_artist_trgm ON public.ods_track_search USING GIN (artist_names gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_ods_track_search_album_trgm ON public.ods_track_search USING GIN (album_title gin_trgm_ops);

-- Create a function to automatically update the search_vector column
CREATE OR REPLACE FUNCTION update_ods_track_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.artist_names, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.album_title, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.genre_names, '')), 'D');
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update search_vector on insert/update
DROP TRIGGER IF EXISTS trigger_update_ods_track_search_vector ON public.ods_track_search;
CREATE TRIGGER trigger_update_ods_track_search_vector
    BEFORE INSERT OR UPDATE ON public.ods_track_search
    FOR EACH ROW
    EXECUTE FUNCTION update_ods_track_search_vector();

-- Create a materialized view refresh function (optional, for batch updates)
CREATE OR REPLACE FUNCTION refresh_ods_track_search()
RETURNS void AS $$
BEGIN
    -- Clear existing data
    TRUNCATE public.ods_track_search;
    
    -- Populate with fresh data from Track, Artist, Album, Genre tables
    INSERT INTO public.ods_track_search (
        track_id,
        title,
        artist_names,
        album_title,
        genre_names,
        duration_ms,
        audio_file_url,
        cover_image_url
    )
    SELECT 
        t.track_id,
        t.title,
        STRING_AGG(DISTINCT a.name, ', ' ORDER BY a.name) AS artist_names,
        alb.title AS album_title,
        STRING_AGG(DISTINCT g.name, ', ' ORDER BY g.name) AS genre_names,
        t.duration_ms,
        t.audio_file_url,
        alb.cover_image_url
    FROM public.Track t
    LEFT JOIN public.TrackArtist ta ON t.track_id = ta.track_id
    LEFT JOIN public.Artist a ON ta.artist_id = a.artist_id
    LEFT JOIN public.AlbumTrack at ON t.track_id = at.track_id
    LEFT JOIN public.Album alb ON at.album_id = alb.album_id
    LEFT JOIN public.TrackGenre tg ON t.track_id = tg.track_id
    LEFT JOIN public.Genre g ON tg.genre_id = g.genre_id
    GROUP BY t.track_id, t.title, t.duration_ms, t.audio_file_url, alb.title, alb.cover_image_url;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON public.ods_track_search TO your_user;
