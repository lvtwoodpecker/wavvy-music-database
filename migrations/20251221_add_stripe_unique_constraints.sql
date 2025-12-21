-- Add unique constraints to StripeAccount table to ensure:
-- 1. One Stripe account per user (user_id unique)
-- 2. Each Stripe customer ID is only used once (stripe_customer_id unique)

-- Add unique constraint on user_id
-- This ensures each user can only have one Stripe account
ALTER TABLE public.StripeAccount 
ADD CONSTRAINT unique_stripe_user_id UNIQUE (user_id);

-- Add unique constraint on stripe_customer_id
-- This ensures each Stripe customer ID is only used once in our system
ALTER TABLE public.StripeAccount 
ADD CONSTRAINT unique_stripe_customer_id UNIQUE (stripe_customer_id);
