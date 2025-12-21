from save_mrmaid import mm_to_img

flowchart_code = """
flowchart TD
    ADMIN[Admin] --> UI[Pricing UI]
    
    UI --> LIST[GET /api/admin/pricing/plans]
    LIST --> PLANS[(SubscriptionPlan<br/>plan_id, name<br/>price_usd<br/>feature_set<br/>is_active)]
    
    UI --> CREATE[POST /api/admin/pricing/plans]
    CREATE --> PLANS
    
    UI --> UPDATE[PUT /api/admin/pricing/plans/:id]
    UPDATE --> CHOICE{Update Price}
    CHOICE -->|Yes| PRICE_REC[(SubscriptionPlanPrice<br/>plan_id, price<br/>currency_code<br/>country_code<br/>effective_from<br/>effective_to<br/>changed_by_user_id)]
    CHOICE -->|No| SET_INACTIVE[Set is_active=false]
    
    SET_INACTIVE --> PLANS
    PRICE_REC --> AUDIT[Audit Trail<br/>change_reason]
    
    FE[Frontend] --> BROWSE[GET /api/pricing/plans]
    BROWSE --> |is_active=true| PLANS
    BROWSE --> CARDS[Display pricing cards]
    
    FEAT1[Multi-currency support]
    FEAT2[Geo-pricing by country]
    FEAT3[Feature sets as JSON]
    FEAT4[Temporal pricing history]
    
    PLANS -.-> FEAT3
    PRICE_REC -.-> FEAT1
    PRICE_REC -.-> FEAT2
    PRICE_REC -.-> FEAT4
"""

mm_to_img(flowchart_code, filename="images/subscription_pricing_management.png", fmt="png")
print("✓ Subscription Pricing Management diagram generated!")
