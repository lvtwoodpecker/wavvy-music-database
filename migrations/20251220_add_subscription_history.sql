-- Adds SubscriptionHistory table for tracking user subscription lifecycle
-- Safe to run once; idempotency is not handled here.

CREATE TABLE IF NOT EXISTS public.SubscriptionHistory (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES public.User(user_id),
  plan_id integer,
  plan_name character varying,
  status character varying NOT NULL DEFAULT 'active',
  started_at timestamp with time zone NOT NULL DEFAULT now(),
  expires_at timestamp with time zone,
  canceled_at timestamp with time zone,
  created_at timestamp with time zone NOT NULL DEFAULT now()
);

-- Optional index for quick lookups
CREATE INDEX IF NOT EXISTS idx_subscriptionhistory_user_id ON public.SubscriptionHistory(user_id);
