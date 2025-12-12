

`db/` --> Database infrastructure; contains code that interacts with the database itself.

- create engine

- create session

- manage Base class

- manage migrations (optional)

`models/` --> ORM classes that represent tables

- User

- Playlist

- CompetitorPricing

- SubscriptionPlans

- Tracks, Albums, Artists

- Advertiser, Campaign

`services/` --> Business logic (queries, inserts, domain logic, analytics, etc)

`api/` --> our site possible GET, POST routes 

`tests/` --> write tests to test our logic as we go

`utils/` --> any shared logic