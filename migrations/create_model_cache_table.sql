-- Create table to store trained recommendation models in Supabase
-- Using BYTEA to store raw binary payloads
-- Stores multiple model types: content_based_similarity, content_based_recommender_playlist, content_based_recommender_user
CREATE TABLE IF NOT EXISTS public.ModelCache (
  model_id SERIAL PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL DEFAULT 'content_based_similarity',
  model_data BYTEA NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  UNIQUE(model_name)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_model_cache_name ON public.ModelCache(model_name);
CREATE INDEX IF NOT EXISTS idx_model_cache_created_at ON public.ModelCache(created_at DESC);

