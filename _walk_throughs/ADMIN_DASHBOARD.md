## Admin Dashboard (Wavvy)

The **Admin Dashboard** is the control center for managing Wavvy’s business + platform operations. It’s a React page (`src/pages/AdminDashboard.jsx`) that lets admins monitor trends, review competitive context, and take action (pricing + user management) from one place.

### What it does

#### 1) Price Trends (SubscriptionPlanPrice history)
- Shows **current and historical subscription prices** (pulled from `/api/admin/pricing-trends`).
- Displays rollups like:
  - number of active plans
  - total price changes
  - average current price
- Supports **admin price updates** via `/api/admin/update-price`.
- Pricing UI is rendered per-plan with `PricingCard`.

#### 2) Competitors (Market Intelligence)
- Pulls competitor metadata + plan info from `/api/admin/competitor-data`.
- Lets admins compare:
  - competitor plan names / billing periods
  - student/family flags
  - latest observed competitor pricing
- This is how we keep Wavvy’s pricing grounded in the actual market.

#### 3) ML Price Analysis (Decision Support)
- Pulls model-backed recommendations from `/api/admin/ml-price-analysis`.
- Shows recommended price changes alongside competitor averages.
- Intended to support “raise/lower/hold” decisions with confidence signals and reasoning.

#### 4) User Management (Trust & Safety / Admin Ops)
- Lists users with pagination from `/api/admin/users?page=...`.
- Allows admins to:
  - update status (active / banned / inactive) via `/api/admin/update-user-status`
  - update role (user / admin) via `/api/admin/update-user-role`

#### 5) Analytics Tabs (Expandable)
These tabs are currently mocked in the frontend but represent the intended admin observability layer:
- **Music Analytics**: top tracks + plays over time
- **Revenue Analytics**: MRR/ARR, revenue by plan, trend chart
- **Platform Stats**: total users, library sizes, storage/bandwidth signals
- **User Activity**: DAU/WAU/MAU, peak usage hours, retention

### How it works (high level)
- The dashboard is tab-based (`activeTab` state).
- When you switch tabs, a single `useEffect` triggers the correct fetch function.
- All fetch calls include the auth token:
  - `Authorization: Bearer <token>`
- The UI shows loading + error states globally.

### Key files
- `src/pages/AdminDashboard.jsx` — dashboard logic + layout
- `src/components/PricingCard.jsx` — per-plan pricing trend + “update price” UI
- `src/styles/AdminDashboard.css` — styling

## Walk Through
