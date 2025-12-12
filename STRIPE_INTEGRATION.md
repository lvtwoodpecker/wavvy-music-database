# Stripe Account Linking Integration

## Overview
This integration allows authenticated Wavvy users to link exactly one Stripe account to their profile. The Stripe connection will be used for payments, subscriptions, and advertiser billing.

## Features Implemented

### Backend (Flask)

#### Database Model
- **StripeAccount** model with one-to-one relationship to User
- Unique constraints enforce single Stripe account per user
- Fields: `id`, `stripe_id`, `user_id`, `stripe_customer_id`, `is_default`, `created_at`

#### API Endpoints

1. **POST /api/stripe/connect**
   - Requires authentication (Bearer token)
   - Creates or retrieves Stripe Customer for user
   - Returns: `{ stripe_customer_id, status, message }`
   - Prevents duplicate accounts per user

2. **GET /api/stripe/status**
   - Requires authentication (Bearer token)
   - Returns connection status for current user
   - Returns: `{ connected, stripe_customer_id, created_at }`

3. **POST /api/stripe/webhook**
   - Handles Stripe webhook events
   - Listens for: `customer.updated`, `customer.deleted`
   - Verifies webhook signature for security

#### Services

**StripeAccountService** methods:
- `get_stripe_account_by_user_id(user_id)` - Retrieves existing Stripe account
- `create_or_get_stripe_customer(user_id, email, name)` - Creates new or returns existing Stripe Customer
- `create_local_stripe_account_record(user_id, stripe_customer_id)` - Saves Stripe account to database

### Frontend (React)

#### New Components

**Settings Page** (`/settings`)
- Displays user account information
- Shows Stripe connection status with visual indicator (green dot = connected)
- "Connect Stripe Account" button when not connected
- Displays Stripe Customer ID and connection date when connected
- Error and success message handling
- Back to Home and Logout buttons

#### Services

**stripeService.js**
- `getStripeStatus(token)` - Fetches Stripe connection status
- `connectStripeAccount(token)` - Initiates Stripe account connection

#### Routing
- Added `/settings` protected route
- Home page now includes "Settings" button in navigation

## Security Features

- ✅ JWT authentication required for all Stripe endpoints
- ✅ CORS properly configured for frontend origin
- ✅ Webhook signature verification
- ✅ One-to-one enforcement via database unique constraints
- ✅ No SQL injection vulnerabilities (using ORM)
- ✅ Proper error handling without exposing sensitive data

## Testing

### Unit Tests (6 tests, all passing)
1. `test_get_stripe_account_by_user_id_found` - Retrieving existing account
2. `test_get_stripe_account_by_user_id_not_found` - Handling missing account
3. `test_create_or_get_stripe_customer_new` - Creating new Stripe customer
4. `test_create_or_get_stripe_customer_existing` - Returning existing customer
5. `test_stripe_customer_uniqueness` - Verifying user_id unique constraint
6. `test_stripe_customer_id_uniqueness` - Verifying stripe_customer_id unique constraint

## Usage Flow

1. User logs into Wavvy app
2. User navigates to Settings page
3. User sees "Not connected" status
4. User clicks "Connect Stripe Account" button
5. Backend creates Stripe Customer and saves to database
6. UI updates to show "Stripe account connected" with customer ID
7. Subsequent clicks return existing account (no duplicates)

## Environment Variables Required

```
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:5173
```

## Future Enhancements

- Stripe Connect for advertisers (Express/Standard accounts)
- Payment method management
- Subscription handling
- Transaction history
- Stripe Dashboard link for connected accounts
