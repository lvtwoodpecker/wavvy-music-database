-- Initial Indexs
create index if not exists trackartist_artist_id_idx
on public."TrackArtist" (artist_id);

create index if not exists trackartist_track_id_idx
on public."TrackArtist" (track_id);

create index if not exists albumtrack_track_id_idx
on public."AlbumTrack" (track_id);

create index if not exists albumtrack_album_id_idx
on public."AlbumTrack" (album_id);

create index if not exists trackgenre_genre_id_idx
on public."TrackGenre" (genre_id);

create index if not exists artistgenre_genre_id_idx
on public."ArtistGenre" (genre_id);

create index if not exists playhistory_listener_played_at_idx
on public."PlayHistory" (listener_id, played_at desc);

create index if not exists playhistory_track_played_at_idx
on public."PlayHistory" (track_id, played_at desc);
create index if not exists playlisttrack_playlist_date_added_idx
on public."PlaylistTrack" (playlist_id, date_added desc);

create index if not exists playlisttrack_track_id_idx
on public."PlaylistTrack" (track_id);


Create the Track Searcher Table
create table if not exists public.ods_track_search (
  track_id bigint primary key,
  track_title text not null,
  artist_names text not null,
  album_titles text,
  genre_names text,
  duration_ms integer,
  spotify_id text,
  date_added timestamptz,
  popularity_score numeric default 0, -- optional (you can compute later)
  search_tsv tsvector
);

-- Populating the ods_trak_search
-- That gives you a single “search row” per track. Now searches don’t need 5 joins.
insert into public.ods_track_search (
  track_id, track_title, artist_names, album_titles, genre_names,
  duration_ms, spotify_id, date_added, search_tsv
)
select
  t.track_id,
  t.title::text as track_title,

  coalesce(string_agg(distinct a.name, ' | ' order by a.name), '') as artist_names,

  nullif(string_agg(distinct al.title, ' | ' order by al.title), '') as album_titles,

  nullif(string_agg(distinct g.name, ' | ' order by g.name), '') as genre_names,

  t.duration_ms,
  t.spotify_id,
  t.date_added,

  (
    setweight(to_tsvector('simple', unaccent(coalesce(t.title::text,''))), 'A') ||
    setweight(to_tsvector('simple', unaccent(coalesce(string_agg(distinct a.name, ' '),''))), 'A') ||
    setweight(to_tsvector('simple', unaccent(coalesce(string_agg(distinct al.title, ' '),''))), 'B') ||
    setweight(to_tsvector('simple', unaccent(coalesce(string_agg(distinct g.name, ' '),''))), 'C')
  ) as search_tsv

from public."Track" as t
left join public."TrackArtist" ta on ta.track_id = t.track_id
left join public."Artist" a on a.artist_id = ta.artist_id

left join public."AlbumTrack" at on at.track_id = t.track_id
left join public."Album" al on al.album_id = at.album_id

left join public."TrackGenre" tg on tg.track_id = t.track_id
left join public."Genre" g on g.genre_id = tg.genre_id

group by t.track_id
on conflict (track_id) do update set
  track_title = excluded.track_title,
  artist_names = excluded.artist_names,
  album_titles = excluded.album_titles,
  genre_names = excluded.genre_names,
  duration_ms = excluded.duration_ms,
  spotify_id = excluded.spotify_id,
  date_added = excluded.date_added,
  search_tsv = excluded.search_tsv;

-- Enable Searches
create index if not exists ods_track_search_tsv_idx
on public.ods_track_search
using gin (search_tsv);

-- Store normalized columns, index those
-- Instead of indexing unaccent(col) directly, you:
-- Add “normalized” columns (already unaccented + lowercased)
-- Fill them via your ETL/upsert (ODS refresh) or triggers
-- Index the normalized columns directly (no functions in index expression)
-- 1) Add normalized columns
alter table public.ods_track_search
  add column if not exists track_title_norm text,
  add column if not exists artist_names_norm text,
  add column if not exists album_titles_norm text;
-- 2) Backfill existing rows
update public.ods_track_search
set
  track_title_norm   = lower(unaccent(track_title)),
  artist_names_norm  = lower(unaccent(artist_names)),
  album_titles_norm  = lower(unaccent(coalesce(album_titles,'')));

-- 3) Create trigram indexes on the plain columns
create extension if not exists pg_trgm;
create extension if not exists unaccent;

create index if not exists ods_track_title_norm_trgm_idx
on public.ods_track_search
using gin (track_title_norm gin_trgm_ops);

create index if not exists ods_artist_names_norm_trgm_idx
on public.ods_track_search
using gin (artist_names_norm gin_trgm_ops);

create index if not exists ods_album_titles_norm_trgm_idx
on public.ods_track_search
using gin (album_titles_norm gin_trgm_ops);

Typos + Partials
create index if not exists ods_track_search_title_trgm_idx
on public.ods_track_search
using gin (unaccent(track_title) gin_trgm_ops);

create index if not exists ods_track_search_artist_trgm_idx
on public.ods_track_search
using gin (unaccent(artist_names) gin_trgm_ops);

create index if not exists ods_track_search_album_trgm_idx
on public.ods_track_search
using gin (unaccent(coalesce(album_titles,'')) gin_trgm_ops);

-- Column + GIN index for FTS
alter table public.ods_track_search
  add column if not exists search_tsv tsvector;

-- FTS
create index if not exists ods_track_search_tsv_idx
on public.ods_track_search using gin (search_tsv);

-- Trigram (on normalized columns)
create index if not exists ods_track_title_norm_trgm_idx
on public.ods_track_search using gin (track_title_norm gin_trgm_ops);

create index if not exists ods_artist_names_norm_trgm_idx
on public.ods_track_search using gin (artist_names_norm gin_trgm_ops);

create index if not exists ods_album_titles_norm_trgm_idx
on public.ods_track_search using gin (album_titles_norm gin_trgm_ops);

-- Populate search_tsv during your upsert
insert into public.ods_track_search (
  track_id,
  track_title,
  artist_names,
  album_titles,
  genre_names,

  track_title_norm,
  artist_names_norm,
  album_titles_norm,

  search_tsv,

  duration_ms,
  spotify_id,
  date_added,

  created_at,
  updated_at
)
select
  t.track_id,
  t.title::text as track_title,

  coalesce(string_agg(distinct a.name, ' | ' order by a.name), '') as artist_names,
  coalesce(string_agg(distinct al.title, ' | ' order by al.title), '') as album_titles,
  coalesce(string_agg(distinct g.name, ' | ' order by g.name), '') as genre_names,

  lower(unaccent(coalesce(t.title::text, ''))) as track_title_norm,
  lower(unaccent(coalesce(string_agg(distinct a.name, ' '), ''))) as artist_names_norm,
  lower(unaccent(coalesce(string_agg(distinct al.title, ' '),''))) as album_titles_norm,

  (
    setweight(to_tsvector('simple', unaccent(coalesce(t.title::text,''))), 'A') ||
    setweight(to_tsvector('simple', unaccent(coalesce(string_agg(distinct a.name, ' '),''))), 'A') ||
    setweight(to_tsvector('simple', unaccent(coalesce(string_agg(distinct al.title, ' '),''))), 'B') ||
    setweight(to_tsvector('simple', unaccent(coalesce(string_agg(distinct g.name, ' '),''))), 'C')
  ) as search_tsv,

  t.duration_ms,
  t.spotify_id,
  t.date_added,

  now() as created_at,
  now() as updated_at

from public."Track" t
left join public."TrackArtist" ta on ta.track_id = t.track_id
left join public."Artist" a on a.artist_id = ta.artist_id

left join public."AlbumTrack" at on at.track_id = t.track_id
left join public."Album" al on al.album_id = at.album_id

left join public."TrackGenre" tg on tg.track_id = t.track_id
left join public."Genre" g on g.genre_id = tg.genre_id

group by t.track_id
on conflict (track_id) do update
set
  track_title       = excluded.track_title,
  artist_names      = excluded.artist_names,
  album_titles      = excluded.album_titles,
  genre_names       = excluded.genre_names,

  track_title_norm  = excluded.track_title_norm,
  artist_names_norm = excluded.artist_names_norm,
  album_titles_norm = excluded.album_titles_norm,

  search_tsv        = excluded.search_tsv,

  duration_ms       = excluded.duration_ms,
  spotify_id        = excluded.spotify_id,
  date_added        = excluded.date_added,

  updated_at        = now();

-- Normalized gin trigram indexes
create index if not exists ods_track_title_norm_trgm_idx
on public.ods_track_search using gin (track_title_norm gin_trgm_ops);

create index if not exists ods_album_titles_norm_trgm_idx
on public.ods_track_search using gin (album_titles_norm gin_trgm_ops);

create index if not exists ods_search_tsv_idx on public.ods_track_search using gin (search_tsv);








