# Stripe Integration Guide

This document describes the Stripe integration in Wavvy, including how users connect their Stripe accounts and how payments are processed.

## Overview

Wavvy uses Stripe for payment processing. Users must connect a Stripe account before they can make payments for subscriptions or other services.

## Architecture

### Database Model

The `StripeAccount` table stores the connection between Wavvy users and their Stripe customer accounts:

```sql
CREATE TABLE public.StripeAccount (
  stripe_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL UNIQUE,  -- One Stripe account per user
  stripe_customer_id text NOT NULL UNIQUE,  -- Unique Stripe customer ID
  is_default boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.User(user_id)
);
```

**Key Constraints:**
- `user_id` is UNIQUE - each user can only have one Stripe account
- `stripe_customer_id` is UNIQUE - each Stripe customer ID can only be used once

**Note on Constraints:** The unique constraints are defined both in the SQLAlchemy model (`app/models/StripeAccount.py`) and in the database migration (`migrations/20251221_add_stripe_unique_constraints.sql`). For existing databases, run the migration. For new databases created from the model, the constraints will be automatically applied. When making changes to constraints, update both the model definition and create a new migration file.

### Backend Services

#### StripeAccountService (`app/services/stripe/create_stripe_account.py`)

Manages Stripe customer creation and account linking:

- `create_or_get_stripe_customer(user_id, email, name)`: Creates a new Stripe customer or retrieves existing one
- `get_stripe_account_by_user_id(user_id)`: Gets the Stripe account for a user

#### StripeCheckoutService (`app/services/stripe/checkout.py`)

Handles payment checkout sessions:

- `create_checkout_session(user_id, amount_cents, payment_for, ...)`: Creates a Stripe checkout session
- **Default behavior**: Requires user to have a connected Stripe account (`require_connected_account=True`)
- If user has a connected account, the checkout session will be linked to their Stripe customer ID

### API Endpoints

All endpoints are prefixed with `/api/stripe`:

#### `POST /api/stripe/connect`

Connects a Stripe account for the authenticated user.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "stripe_customer_id": "cus_xxx",
  "status": "created|existing",
  "message": "Stripe account connected successfully"
}
```

#### `GET /api/stripe/status`

Gets the Stripe connection status for the authenticated user.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "connected": true,
  "stripe_customer_id": "cus_xxx",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### `POST /api/stripe/create-checkout-session`

Creates a Stripe checkout session for payment.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "amount_cents": 999,
  "currency": "usd",
  "payment_for": "1-Month Premium Subscription"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_xxx"
}
```

**Error Response (if not connected):**
```json
{
  "error": "User must connect a Stripe account before making payments. Please connect your account in Settings."
}
```

### Frontend Integration

#### Settings Page (`frontend/src/pages/Settings.jsx`)

The Settings page provides a UI for users to:
1. View their Stripe connection status
2. Connect a Stripe account with a single button click
3. See their connected Stripe customer ID and connection date

#### PayButton Component (`frontend/src/components/PayButton.jsx`)

The PayButton component:
1. Sends payment request to `/api/stripe/create-checkout-session`
2. Includes authentication token
3. Handles errors gracefully - if user hasn't connected Stripe, shows error with link to Settings
4. Redirects to Stripe checkout on success

## User Flow

### Connecting a Stripe Account

1. User navigates to Settings page
2. User sees "Not connected" status
3. User clicks "Connect Stripe Account" button
4. Backend creates a Stripe Customer and stores the connection in the database
5. User sees "Connected" status with their customer ID

### Making a Payment

1. User clicks "Get Premium!" or similar payment button
2. Frontend sends request to create checkout session
3. Backend checks if user has connected Stripe account:
   - **If connected:** Creates checkout session linked to their customer ID
   - **If not connected:** Returns error with helpful message
4. If successful, user is redirected to Stripe checkout page
5. After payment, user is redirected back to success/cancel page

## Database Migration

To apply the unique constraints to an existing database:

```bash
# Run the migration SQL
psql -U your_user -d your_database -f migrations/20251221_add_stripe_unique_constraints.sql
```

The migration adds:
- Unique constraint on `user_id` to ensure one Stripe account per user
- Unique constraint on `stripe_customer_id` to ensure each Stripe customer ID is only used once

## Configuration

Add the following to your `.env` file:

```env
# Payments
PAYMENTS_PROVIDER=stripe
STRIPE_API_KEY=sk_test_...  # Your Stripe secret key
STRIPE_WEBHOOK_SECRET=whsec_...  # Your Stripe webhook secret

# Frontend URL (for redirect after payment)
FRONTEND_URL=http://localhost:5173
```

## Testing

Run the Stripe integration tests:

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest app/tests/test_stripe.py -v
```

All tests should pass (9 tests total):
- StripeAccountService tests (5)
- StripeCheckoutService tests (3)
- Model constraint tests (2)

## Security Considerations

1. **Authentication Required**: All payment endpoints require user authentication
2. **Unique Constraints**: Database constraints prevent duplicate accounts
3. **Server-side Validation**: Stripe connection is validated server-side before creating checkout sessions
4. **Stripe Customer Linking**: Payments are linked to verified Stripe customer IDs
5. **Webhook Verification**: Stripe webhooks should verify signatures (webhook endpoint included)

## Future Enhancements

Potential improvements to consider:

1. **Payment Methods**: Allow users to save multiple payment methods
2. **Subscription Management**: Integrate with Stripe Subscriptions API
3. **Invoice History**: Display payment history from Stripe
4. **Refunds**: Add refund functionality through Stripe
5. **Webhook Events**: Handle more Stripe webhook events (payment success, subscription changes, etc.)
