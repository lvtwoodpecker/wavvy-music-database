-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.AdCampaign (
  campaign_id bigint NOT NULL DEFAULT nextval('"AdCampaign_campaign_id_seq"'::regclass),
  advertiser_id bigint NOT NULL,
  name character varying NOT NULL,
  budget numeric NOT NULL CHECK (budget > 0::numeric),
  status character varying NOT NULL DEFAULT 'draft'::character varying CHECK (status::text = ANY (ARRAY['draft'::character varying, 'active'::character varying, 'paused'::character varying, 'completed'::character varying]::text[])),
  target_country text,
  CONSTRAINT AdCampaign_pkey PRIMARY KEY (campaign_id),
  CONSTRAINT fk_advertiser FOREIGN KEY (advertiser_id) REFERENCES public.Advertiser(advertiser_id)
);
CREATE TABLE public.AdClick (
  impression_id uuid NOT NULL,
  click_time timestamp with time zone NOT NULL DEFAULT now(),
  redirect_url character varying,
  country_code text,
  device_type text,
  CONSTRAINT AdClick_pkey PRIMARY KEY (impression_id),
  CONSTRAINT fk_impression FOREIGN KEY (impression_id) REFERENCES public.AdImpression(impression_id)
);
CREATE TABLE public.AdCreative (
  creative_id bigint NOT NULL DEFAULT nextval('"AdCreative_creative_id_seq"'::regclass),
  campaign_id bigint NOT NULL,
  creative_type character varying NOT NULL CHECK (creative_type::text = ANY (ARRAY['audio'::character varying, 'video'::character varying, 'display'::character varying]::text[])),
  asset_url character varying NOT NULL CHECK (asset_url::text ~* '^https?://'::text),
  headline character varying,
  language text,
  format text,
  CONSTRAINT AdCreative_pkey PRIMARY KEY (creative_id),
  CONSTRAINT fk_campaign FOREIGN KEY (campaign_id) REFERENCES public.AdCampaign(campaign_id)
);
CREATE TABLE public.AdImpression (
  impression_id uuid NOT NULL DEFAULT gen_random_uuid(),
  creative_id bigint NOT NULL,
  served_at timestamp with time zone NOT NULL DEFAULT now(),
  view_time_ms integer,
  device_type text,
  interaction_type text,
  CONSTRAINT AdImpression_pkey PRIMARY KEY (impression_id),
  CONSTRAINT fk_creative FOREIGN KEY (creative_id) REFERENCES public.AdCreative(creative_id)
);
CREATE TABLE public.Advertiser (
  advertiser_id bigint NOT NULL DEFAULT nextval('"Advertiser_advertiser_id_seq"'::regclass),
  user_id bigint NOT NULL UNIQUE,
  company_name text,
  advertiser_type text,
  industry_category text,
  CONSTRAINT Advertiser_pkey PRIMARY KEY (advertiser_id),
  CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.User(user_id)
);
CREATE TABLE public.Album (
  album_id bigint NOT NULL DEFAULT nextval('"Album_album_id_seq"'::regclass),
  title character varying NOT NULL,
  release_date date CHECK (release_date IS NULL OR release_date <= CURRENT_DATE),
  type character varying CHECK (type::text = ANY (ARRAY['album'::character varying, 'single'::character varying, 'compilation'::character varying, 'EP'::character varying]::text[])),
  label_id integer,
  cover_image_url text,
  CONSTRAINT Album_pkey PRIMARY KEY (album_id),
  CONSTRAINT fk_label FOREIGN KEY (label_id) REFERENCES public.Label(label_id)
);
CREATE TABLE public.AlbumArtist (
  album_id bigint NOT NULL,
  artist_id bigint NOT NULL,
  CONSTRAINT AlbumArtist_pkey PRIMARY KEY (album_id, artist_id),
  CONSTRAINT fk_album FOREIGN KEY (album_id) REFERENCES public.Album(album_id),
  CONSTRAINT fk_artist FOREIGN KEY (artist_id) REFERENCES public.Artist(artist_id)
);
CREATE TABLE public.AlbumTrack (
  album_id bigint NOT NULL,
  track_id bigint NOT NULL,
  disc_no integer NOT NULL DEFAULT 1 CHECK (disc_no >= 1),
  track_no integer NOT NULL CHECK (track_no >= 1),
  CONSTRAINT AlbumTrack_pkey PRIMARY KEY (album_id, track_id),
  CONSTRAINT fk_album FOREIGN KEY (album_id) REFERENCES public.Album(album_id),
  CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id)
);
CREATE TABLE public.Artist (
  artist_id bigint NOT NULL DEFAULT nextval('"Artist_artist_id_seq"'::regclass),
  name character varying NOT NULL UNIQUE,
  bio text,
  type character varying CHECK (type::text = ANY (ARRAY['Solo'::character varying, 'Group'::character varying, 'Orchestra'::character varying, 'Other'::character varying]::text[])),
  CONSTRAINT Artist_pkey PRIMARY KEY (artist_id)
);
CREATE TABLE public.ArtistGenre (
  artist_id bigint NOT NULL,
  genre_id integer NOT NULL,
  CONSTRAINT ArtistGenre_pkey PRIMARY KEY (artist_id, genre_id),
  CONSTRAINT fk_artist FOREIGN KEY (artist_id) REFERENCES public.Artist(artist_id),
  CONSTRAINT fk_genre FOREIGN KEY (genre_id) REFERENCES public.Genre(genre_id)
);
CREATE TABLE public.AudioFeatures (
  track_id bigint NOT NULL,
  tempo double precision NOT NULL CHECK (tempo > 0::double precision),
  loudness double precision NOT NULL CHECK (loudness >= '-60'::integer::double precision AND loudness <= 10::double precision),
  danceability double precision NOT NULL,
  energy double precision,
  valence double precision,
  acousticness double precision,
  CONSTRAINT AudioFeatures_pkey PRIMARY KEY (track_id),
  CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id)
);
CREATE TABLE public.CampaignAudience (
  campaign_id bigint NOT NULL,
  genre_id integer NOT NULL,
  CONSTRAINT CampaignAudience_pkey PRIMARY KEY (campaign_id, genre_id),
  CONSTRAINT fk_campaign FOREIGN KEY (campaign_id) REFERENCES public.AdCampaign(campaign_id),
  CONSTRAINT fk_genre FOREIGN KEY (genre_id) REFERENCES public.Genre(genre_id)
);
CREATE TABLE public.CampaignEvent (
  campaign_id bigint NOT NULL,
  event_id bigint NOT NULL,
  CONSTRAINT CampaignEvent_pkey PRIMARY KEY (campaign_id, event_id),
  CONSTRAINT fk_campaign FOREIGN KEY (campaign_id) REFERENCES public.AdCampaign(campaign_id),
  CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES public.Event(event_id)
);
CREATE TABLE public.Event (
  event_id bigint NOT NULL DEFAULT nextval('"Event_event_id_seq"'::regclass),
  name character varying NOT NULL,
  event_type character varying CHECK (event_type::text = ANY (ARRAY['Concert'::character varying, 'Festival'::character varying, 'ListeningParty'::character varying, 'Conference'::character varying, 'Other'::character varying]::text[])),
  start_date timestamp with time zone,
  end_date timestamp with time zone,
  city character varying,
  venue character varying,
  CONSTRAINT Event_pkey PRIMARY KEY (event_id)
);
CREATE TABLE public.Genre (
  genre_id integer NOT NULL DEFAULT nextval('"Genre_genre_id_seq"'::regclass),
  name character varying NOT NULL UNIQUE,
  CONSTRAINT Genre_pkey PRIMARY KEY (genre_id)
);
CREATE TABLE public.ImpressionUser (
  impression_id uuid NOT NULL,
  listener_id uuid NOT NULL,
  CONSTRAINT ImpressionUser_pkey PRIMARY KEY (impression_id, listener_id),
  CONSTRAINT fk_impressionuser_impression FOREIGN KEY (impression_id) REFERENCES public.AdImpression(impression_id),
  CONSTRAINT fk_impressionuser_listener FOREIGN KEY (listener_id) REFERENCES public.Listener(listener_id)
);
CREATE TABLE public.Label (
  label_id integer NOT NULL DEFAULT nextval('"Label_label_id_seq"'::regclass),
  name character varying NOT NULL UNIQUE,
  location character varying,
  manager character varying,
  CONSTRAINT Label_pkey PRIMARY KEY (label_id)
);
CREATE TABLE public.Listener (
  listener_id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id bigint UNIQUE,
  ad_free boolean NOT NULL DEFAULT false,
  CONSTRAINT Listener_pkey PRIMARY KEY (listener_id),
  CONSTRAINT Listener_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.User(user_id)
);
CREATE TABLE public.ModelCache (
  model_id integer NOT NULL DEFAULT nextval('modelcache_model_id_seq'::regclass),
  model_name character varying NOT NULL DEFAULT 'content_based_similarity'::character varying UNIQUE,
  model_data bytea NOT NULL,
  metadata jsonb NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT ModelCache_pkey PRIMARY KEY (model_id)
);
CREATE TABLE public.PasswordResetToken (
  id integer NOT NULL DEFAULT nextval('"PasswordResetToken_id_seq"'::regclass),
  user_id integer NOT NULL,
  token character varying NOT NULL,
  expires_at timestamp without time zone,
  used boolean,
  created_at timestamp without time zone,
  CONSTRAINT PasswordResetToken_pkey PRIMARY KEY (id),
  CONSTRAINT PasswordResetToken_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.User(user_id)
);
CREATE TABLE public.PlayHistory (
  listener_id uuid NOT NULL,
  track_id bigint NOT NULL,
  played_at timestamp with time zone NOT NULL DEFAULT now() CHECK (played_at <= now()),
  is_skip boolean NOT NULL DEFAULT false,
  CONSTRAINT PlayHistory_pkey PRIMARY KEY (listener_id, track_id, played_at),
  CONSTRAINT fk_playhistory_listener FOREIGN KEY (listener_id) REFERENCES public.Listener(listener_id),
  CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id)
);
CREATE TABLE public.Playlist (
  playlist_id bigint NOT NULL DEFAULT nextval('"Playlist_playlist_id_seq"'::regclass),
  owner_listener_id uuid,
  title character varying,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  is_public boolean NOT NULL DEFAULT true,
  is_collaborative boolean NOT NULL DEFAULT false,
  CONSTRAINT Playlist_pkey PRIMARY KEY (playlist_id),
  CONSTRAINT fk_playlist_owner_listener FOREIGN KEY (owner_listener_id) REFERENCES public.Listener(listener_id)
);
CREATE TABLE public.PlaylistTrack (
  playlist_id bigint NOT NULL,
  track_id bigint NOT NULL,
  date_added timestamp with time zone NOT NULL DEFAULT now(),
  added_by_user_id uuid,
  date_removed timestamp with time zone,
  removed_by_user_id uuid,
  CONSTRAINT PlaylistTrack_pkey PRIMARY KEY (playlist_id, track_id, date_added),
  CONSTRAINT fk_playlisttrack_playlist FOREIGN KEY (playlist_id) REFERENCES public.Playlist(playlist_id),
  CONSTRAINT fk_playlisttrack_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id),
  CONSTRAINT fk_playlisttrack_added_by FOREIGN KEY (added_by_user_id) REFERENCES public.Listener(listener_id),
  CONSTRAINT fk_playlisttrack_removed_by FOREIGN KEY (removed_by_user_id) REFERENCES public.Listener(listener_id)
);
CREATE TABLE public.Session (
  session_id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id bigint NOT NULL,
  start_time timestamp with time zone NOT NULL DEFAULT now(),
  end_time timestamp with time zone,
  device_type text,
  CONSTRAINT Session_pkey PRIMARY KEY (session_id),
  CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.User(user_id)
);
CREATE TABLE public.StripeAccount (
  user_id bigint NOT NULL,
  is_default boolean NOT NULL DEFAULT true,
  stripe_customer_id text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  stripe_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  CONSTRAINT StripeAccount_pkey PRIMARY KEY (stripe_id),
  CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.User(user_id)
);
CREATE TABLE public.StripeInvoice (
  invoice_id character varying NOT NULL,
  stripe_id bigint NOT NULL,
  amount_cents integer NOT NULL CHECK (amount_cents > 0),
  date_processed timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT StripeInvoice_pkey PRIMARY KEY (invoice_id),
  CONSTRAINT fk_stripe_account FOREIGN KEY (stripe_id) REFERENCES public.StripeAccount(stripe_id)
);
CREATE TABLE public.SubscriptionHistory (
  id integer NOT NULL DEFAULT nextval('"SubscriptionHistory_id_seq"'::regclass),
  user_id integer NOT NULL,
  plan_id integer,
  plan_name character varying,
  status character varying NOT NULL,
  started_at timestamp with time zone NOT NULL DEFAULT now(),
  expires_at timestamp with time zone,
  canceled_at timestamp with time zone,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT SubscriptionHistory_pkey PRIMARY KEY (id),
  CONSTRAINT SubscriptionHistory_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.User(user_id)
);
CREATE TABLE public.SubscriptionPlan (
  plan_id integer NOT NULL DEFAULT nextval('"SubscriptionPlan_plan_id_seq"'::regclass),
  name character varying NOT NULL UNIQUE,
  price_usd numeric NOT NULL CHECK (price_usd >= 0::numeric),
  feature_set jsonb,
  CONSTRAINT SubscriptionPlan_pkey PRIMARY KEY (plan_id)
);
CREATE TABLE public.Track (
  track_id bigint NOT NULL DEFAULT nextval('"Track_track_id_seq"'::regclass),
  title character varying NOT NULL,
  duration_ms integer NOT NULL,
  isrc character varying UNIQUE,
  audio_file_url text,
  date_added timestamp with time zone NOT NULL DEFAULT now(),
  spotify_id character varying UNIQUE,
  CONSTRAINT Track_pkey PRIMARY KEY (track_id)
);
CREATE TABLE public.TrackArtist (
  track_id bigint NOT NULL,
  artist_id bigint NOT NULL,
  role character varying NOT NULL DEFAULT 'Main'::character varying,
  CONSTRAINT TrackArtist_pkey PRIMARY KEY (track_id, artist_id, role),
  CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id),
  CONSTRAINT fk_artist FOREIGN KEY (artist_id) REFERENCES public.Artist(artist_id)
);
CREATE TABLE public.TrackGenre (
  track_id bigint NOT NULL,
  genre_id integer NOT NULL,
  CONSTRAINT TrackGenre_pkey PRIMARY KEY (track_id, genre_id),
  CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id),
  CONSTRAINT fk_genre FOREIGN KEY (genre_id) REFERENCES public.Genre(genre_id)
);
CREATE TABLE public.TrackWork (
  track_id bigint NOT NULL,
  work_id bigint NOT NULL,
  CONSTRAINT TrackWork_pkey PRIMARY KEY (track_id, work_id),
  CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES public.Track(track_id),
  CONSTRAINT fk_work FOREIGN KEY (work_id) REFERENCES public.Work(work_id)
);
CREATE TABLE public.User (
  user_id bigint NOT NULL DEFAULT nextval('"User_user_id_seq"'::regclass),
  username character varying NOT NULL UNIQUE,
  email character varying NOT NULL UNIQUE CHECK (email::text ~* '^[^@]+@[^@]+\.[^@]+$'::text),
  password_hash character varying NOT NULL,
  country character NOT NULL CHECK (country ~ '^[A-Z]{2}$'::text),
  role text NOT NULL CHECK (role = ANY (ARRAY['listener'::text, 'advertiser'::text])),
  first_name text NOT NULL,
  last_name text NOT NULL,
  status USER-DEFINED NOT NULL,
  CONSTRAINT User_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.Work (
  work_id bigint NOT NULL DEFAULT nextval('"Work_work_id_seq"'::regclass),
  title character varying NOT NULL,
  iswc character varying UNIQUE,
  language text,
  decals_release numeric,
  CONSTRAINT Work_pkey PRIMARY KEY (work_id)
);
CREATE TABLE public.WorkComposer (
  work_id bigint NOT NULL,
  artist_id bigint NOT NULL,
  CONSTRAINT WorkComposer_pkey PRIMARY KEY (work_id, artist_id),
  CONSTRAINT fk_work FOREIGN KEY (work_id) REFERENCES public.Work(work_id),
  CONSTRAINT fk_artist FOREIGN KEY (artist_id) REFERENCES public.Artist(artist_id)
);
CREATE TABLE public.ods_track_search (
  track_id bigint NOT NULL,
  track_title text NOT NULL,
  artist_names text NOT NULL,
  album_titles text,
  genre_names text,
  duration_ms integer,
  spotify_id text,
  date_added timestamp with time zone,
  popularity_score numeric DEFAULT 0,
  search_tsv tsvector,
  track_title_norm text,
  artist_names_norm text,
  album_titles_norm text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT ods_track_search_pkey PRIMARY KEY (track_id)
);