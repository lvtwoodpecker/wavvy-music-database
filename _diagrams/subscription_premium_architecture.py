from save_mrmaid import mm_to_img

flowchart_code = """
flowchart TB
    U[User] --> FE[Frontend]
    
    FE --> PB[PayButton: Get Premium]
    PB --> CHECKOUT[POST /api/stripe/create-checkout-session]
    CHECKOUT --> SESS[Stripe Session Created]
    SESS --> REDIRECT[Redirect to Stripe Checkout]
    REDIRECT --> PAYMENT[User pays with Stripe]
    PAYMENT --> SUCCESS[Stripe redirects to PaymentSuccess]
    
    SUCCESS --> ACTIVATE[subscriptionService.activate]
    ACTIVATE --> ACT_API[POST /api/stripe/subscription/activate]
    ACT_API --> AUTH[JWT Auth @login_required]
    AUTH --> DB[(SubscriptionHistory<br/>user_id, plan_name<br/>status=active<br/>expires_at=+30days)]
    
    SUCCESS --> LOCAL[AuthContext.markPremium<br/>AuthContext.setPremiumExpiry]
    LOCAL --> NAV[Navigate to /app]
    NAV --> U
    
    FE --> STATUS[GET /api/stripe/subscription/status]
    STATUS --> QUERY[Query latest active subscription<br/>Check expiry vs now]
    QUERY --> RET[Return status: active/expired/canceled]
    RET --> FE
    
    FE --> CANCEL[POST /api/stripe/subscription/cancel]
    CANCEL --> CANCEL_AUTH[JWT Auth @login_required]
    CANCEL_AUTH --> UPDATE[(Update SubscriptionHistory<br/>status=canceled<br/>canceled_at=now)]
    UPDATE --> CTA[Show resubscribe CTA]
    CTA --> FE
    
    DB -.SubscriptionHistory model.-> U
"""

mm_to_img(flowchart_code, filename="images/subscription_premium_architecture.png", fmt="png")
print("✓ Subscription/Premium architecture diagram generated!")
