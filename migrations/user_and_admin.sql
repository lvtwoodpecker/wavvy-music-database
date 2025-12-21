BEGIN;

-- (A) Drop the old constraint that only allowed listener/advertiser
ALTER TABLE public."User"
  DROP CONSTRAINT IF EXISTS "User_role_check";

-- (B) Add new constraint: role is now permission tier
ALTER TABLE public."User"
  ADD CONSTRAINT "User_role_check"
  CHECK (role = ANY (ARRAY['user'::text, 'admin'::text]));

-- (C) Set default role for new users
ALTER TABLE public."User"
  ALTER COLUMN role SET DEFAULT 'user';

-- (D) Convert existing data:
-- If you previously stored 'listener' or 'advertiser', map them to 'user'
UPDATE public."User"
SET role = 'user'
WHERE role IN ('listener', 'advertiser');

COMMIT;
