-- 1) COMPETITORS (DIMENSION)
CREATE TABLE IF NOT EXISTS public.Competitor (
  competitor_id bigserial PRIMARY KEY,
  name text NOT NULL UNIQUE,
  website text,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.CompetitorSubscriptionPlan (
  competitor_plan_id bigserial PRIMARY KEY,
  competitor_id bigint NOT NULL REFERENCES public.Competitor(competitor_id) ON DELETE CASCADE,
  plan_name text NOT NULL,
  billing_period text NOT NULL CHECK (billing_period IN ('monthly','yearly','weekly','other')),
  is_student boolean NOT NULL DEFAULT false,
  is_family boolean NOT NULL DEFAULT false,
  max_accounts integer,
  feature_set jsonb,
  UNIQUE (competitor_id, plan_name, billing_period)
);

CREATE TABLE IF NOT EXISTS public.CompetitorSubscriptionPriceSnapshot (
  snapshot_id bigserial PRIMARY KEY,
  competitor_plan_id bigint NOT NULL REFERENCES public.CompetitorSubscriptionPlan(competitor_plan_id) ON DELETE CASCADE,
  observed_at timestamptz NOT NULL DEFAULT now(),
  country_code char(2),
  currency_code char(3) NOT NULL DEFAULT 'USD',
  price numeric NOT NULL CHECK (price >= 0),
  promo_label text,
  promo_price numeric CHECK (promo_price IS NULL OR promo_price >= 0),
  promo_ends_at timestamptz,
  source text,
  source_url text,
  UNIQUE (competitor_plan_id, country_code, currency_code, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_comp_sub_price_plan_time
  ON public.CompetitorSubscriptionPriceSnapshot (competitor_plan_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_comp_sub_price_country_time
  ON public.CompetitorSubscriptionPriceSnapshot (country_code, observed_at DESC);

-- 2) COMPETITOR AD PRICING
CREATE TABLE IF NOT EXISTS public.CompetitorAdProduct (
  competitor_ad_product_id bigserial PRIMARY KEY,
  competitor_id bigint NOT NULL REFERENCES public.Competitor(competitor_id) ON DELETE CASCADE,
  product_name text NOT NULL,
  creative_type text CHECK (creative_type IN ('audio','video','display','other')),
  buying_model text NOT NULL CHECK (buying_model IN ('CPM','CPC','CPV','FLAT','OTHER')),
  notes text,
  UNIQUE (competitor_id, product_name, buying_model)
);

CREATE TABLE IF NOT EXISTS public.CompetitorAdRateSnapshot (
  ad_rate_snapshot_id bigserial PRIMARY KEY,
  competitor_ad_product_id bigint NOT NULL REFERENCES public.CompetitorAdProduct(competitor_ad_product_id) ON DELETE CASCADE,
  observed_at timestamptz NOT NULL DEFAULT now(),
  country_code char(2),
  currency_code char(3) NOT NULL DEFAULT 'USD',
  rate numeric NOT NULL CHECK (rate >= 0),
  min_spend numeric CHECK (min_spend IS NULL OR min_spend >= 0),
  targeting_notes text,
  inventory_notes text,
  source text,
  source_url text,
  UNIQUE (competitor_ad_product_id, country_code, currency_code, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_comp_ad_rate_product_time
  ON public.CompetitorAdRateSnapshot (competitor_ad_product_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_comp_ad_rate_country_time
  ON public.CompetitorAdRateSnapshot (country_code, observed_at DESC);

-- 3) WAVVY SUBSCRIPTION PLAN PRICING (HISTORY)
CREATE TABLE IF NOT EXISTS public.SubscriptionPlanPrice (
  plan_price_id bigserial PRIMARY KEY,
  plan_id integer NOT NULL REFERENCES public."SubscriptionPlan"(plan_id) ON DELETE CASCADE,
  currency_code char(3) NOT NULL DEFAULT 'USD',
  country_code char(2),
  price numeric NOT NULL CHECK (price >= 0),
  effective_from timestamptz NOT NULL DEFAULT now(),
  effective_to timestamptz,
  changed_by_user_id bigint REFERENCES public."User"(user_id),
  change_reason text,
  CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE INDEX IF NOT EXISTS idx_plan_price_lookup_current
  ON public.SubscriptionPlanPrice (plan_id, country_code, currency_code, effective_from DESC);

CREATE INDEX IF NOT EXISTS idx_plan_price_effective
  ON public.SubscriptionPlanPrice (plan_id, effective_from DESC);

-- 4) SUBSCRIPTION TRENDS / METRICS (DAILY)
CREATE TABLE IF NOT EXISTS public.SubscriptionMetricsDaily (
  metric_date date NOT NULL,
  plan_id integer NOT NULL REFERENCES public."SubscriptionPlan"(plan_id) ON DELETE CASCADE,
  country_code char(2),
  active_subscribers integer NOT NULL DEFAULT 0 CHECK (active_subscribers >= 0),
  new_subscribers integer NOT NULL DEFAULT 0 CHECK (new_subscribers >= 0),
  cancellations integer NOT NULL DEFAULT 0 CHECK (cancellations >= 0),
  gross_revenue_usd numeric NOT NULL DEFAULT 0 CHECK (gross_revenue_usd >= 0),
  refunds_usd numeric NOT NULL DEFAULT 0 CHECK (refunds_usd >= 0),
  trials_started integer NOT NULL DEFAULT 0 CHECK (trials_started >= 0),
  trials_converted integer NOT NULL DEFAULT 0 CHECK (trials_converted >= 0),
  PRIMARY KEY (metric_date, plan_id, country_code)
);

CREATE INDEX IF NOT EXISTS idx_sub_metrics_date
  ON public.SubscriptionMetricsDaily (metric_date DESC);

-- 5) PRICING MODEL RUNS + RECOMMENDATIONS
CREATE TABLE IF NOT EXISTS public.PricingModelRun (
  run_id bigserial PRIMARY KEY,
  model_name text NOT NULL,
  model_version text NOT NULL,
  run_started_at timestamptz NOT NULL DEFAULT now(),
  run_finished_at timestamptz,
  training_window_start date,
  training_window_end date,
  notes text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.PricingDemandEstimate (
  estimate_id bigserial PRIMARY KEY,
  run_id bigint NOT NULL REFERENCES public.PricingModelRun(run_id) ON DELETE CASCADE,
  plan_id integer NOT NULL REFERENCES public."SubscriptionPlan"(plan_id) ON DELETE CASCADE,
  country_code char(2),
  price_elasticity numeric,
  baseline_conversion_rate numeric CHECK (baseline_conversion_rate IS NULL OR baseline_conversion_rate >= 0),
  baseline_churn_rate numeric CHECK (baseline_churn_rate IS NULL OR baseline_churn_rate >= 0),
  confidence numeric CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (run_id, plan_id, country_code)
);

CREATE TABLE IF NOT EXISTS public.PricingRecommendation (
  recommendation_id bigserial PRIMARY KEY,
  run_id bigint NOT NULL REFERENCES public.PricingModelRun(run_id) ON DELETE CASCADE,
  plan_id integer NOT NULL REFERENCES public."SubscriptionPlan"(plan_id) ON DELETE CASCADE,
  country_code char(2),
  currency_code char(3) NOT NULL DEFAULT 'USD',
  current_price numeric CHECK (current_price IS NULL OR current_price >= 0),
  recommended_price numeric NOT NULL CHECK (recommended_price >= 0),
  predicted_delta_revenue_usd numeric,
  predicted_delta_churn numeric,
  predicted_delta_new_subscribers numeric,
  recommendation_reason text,
  confidence numeric CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (run_id, plan_id, country_code, currency_code)
);

CREATE INDEX IF NOT EXISTS idx_pricing_rec_plan_country
  ON public.PricingRecommendation (plan_id, country_code, created_at DESC);

-- 6) PRICE EXPERIMENTS (A/B)
CREATE TABLE IF NOT EXISTS public.PriceExperiment (
  experiment_id bigserial PRIMARY KEY,
  name text NOT NULL,
  plan_id integer NOT NULL REFERENCES public."SubscriptionPlan"(plan_id) ON DELETE CASCADE,
  country_code char(2),
  status text NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft','running','paused','completed','canceled')),
  start_at timestamptz,
  end_at timestamptz,
  control_price numeric NOT NULL CHECK (control_price >= 0),
  variant_price numeric NOT NULL CHECK (variant_price >= 0),
  created_by_user_id bigint REFERENCES public."User"(user_id),
  created_at timestamptz NOT NULL DEFAULT now(),
  notes text
);

CREATE TABLE IF NOT EXISTS public.PriceExperimentDailyResult (
  experiment_id bigint NOT NULL REFERENCES public.PriceExperiment(experiment_id) ON DELETE CASCADE,
  result_date date NOT NULL,
  arm text NOT NULL CHECK (arm IN ('control','variant')),
  exposures integer NOT NULL DEFAULT 0 CHECK (exposures >= 0),
  conversions integer NOT NULL DEFAULT 0 CHECK (conversions >= 0),
  cancellations integer NOT NULL DEFAULT 0 CHECK (cancellations >= 0),
  revenue_usd numeric NOT NULL DEFAULT 0 CHECK (revenue_usd >= 0),
  PRIMARY KEY (experiment_id, result_date, arm)
);

-- Ensure extension
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Drop existing constraint if present
ALTER TABLE public.SubscriptionPlanPrice
  DROP CONSTRAINT IF EXISTS subscriptionplanprice_no_overlap;

-- Add generated column if not exists (already added earlier, but safe)
ALTER TABLE public.SubscriptionPlanPrice
  ADD COLUMN IF NOT EXISTS price_range tstzrange GENERATED ALWAYS AS (tstzrange(effective_from, COALESCE(effective_to, 'infinity'))) STORED;

-- Add the exclusion constraint
ALTER TABLE public.SubscriptionPlanPrice
  ADD CONSTRAINT subscriptionplanprice_no_overlap EXCLUDE USING gist (
    plan_id WITH =,
    country_code WITH =,
    currency_code WITH =,
    price_range WITH &&
  );

-- Create function to close previous open-ended price ranges when inserting a new current price
CREATE OR REPLACE FUNCTION public.subscriptionplanprice_close_previous()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Only act when the new row has no effective_to (open-ended/current price)
  IF NEW.effective_to IS NULL THEN
    -- Set effective_to of any existing open-ended price for same plan/country/currency to just before NEW.effective_from
    UPDATE public.subscriptionplanprice
    SET effective_to = NEW.effective_from - INTERVAL '1 microsecond'
    WHERE plan_id = NEW.plan_id
      AND (country_code IS NOT DISTINCT FROM NEW.country_code)
      AND (currency_code IS NOT DISTINCT FROM NEW.currency_code)
      AND (effective_to IS NULL OR effective_to > NEW.effective_from)
      AND plan_price_id <> COALESCE(NEW.plan_price_id, -1);
  END IF;
  RETURN NEW;
END;
$$;

-- Create trigger that fires BEFORE INSERT OR UPDATE
DROP TRIGGER IF EXISTS subscriptionplanprice_close_previous_trigger ON public.subscriptionplanprice;
CREATE TRIGGER subscriptionplanprice_close_previous_trigger
BEFORE INSERT OR UPDATE ON public.subscriptionplanprice
FOR EACH ROW
EXECUTE FUNCTION public.subscriptionplanprice_close_previous();
