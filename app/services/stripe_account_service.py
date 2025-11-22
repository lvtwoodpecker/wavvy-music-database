from uuid import uuid4
import stripe
from app.config import settings
from app.db.supabase_client import supabase

STRIPE_TABLE = "StripeAccount"  
USERS_TABLE = "User" 

if settings.PAYMENTS_PROVIDER == "stripe":
    stripe.api_key = settings.STRIPE_API_KEY
    
def create_local_stripe_account_record(
    user_id: str, 
    stripe_customer_id: str, 
    is_default: int = 1) -> dict:
    """Creates a local record in the StripeAccount table for a user."""
    
    try:
        resp = (
            supabase.table(STRIPE_TABLE)
            .insert({
                "user_id": user_id,
                "stripe_customer_id": stripe_customer_id,
                "is_default": is_default
            })
            .execute()
        )
    except Exception as e:
        print(f"Error creating stripe_account row for user ID {user_id}: {e}")
        raise RuntimeError("Failed to create stripe_account row")
    
    return resp.data[0]

def delete_stripe_account_by_user_id(user_id: str) -> None:
    """Deletes the Stripe account record for a given user ID."""
    print(f"Deleting stripe account for user ID: {user_id}")
    try:
        resp = (
            supabase
            .table(STRIPE_TABLE)
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as e:
        print(f"Error deleting stripe_account row for user ID {user_id}: {e}")
        raise RuntimeError("Failed to delete stripe_account row")

def create_stripe_customer(
    email: str,
    first_name: str,
    last_name: str,
    payment_method: str = None,
    phone: str = None,
    shipping: dict = None
    ) -> str:
    """Create a real or mock Stripe customer ID."""
    # Real Stripe (test mode)
    customer = stripe.Customer.create(
        email=email,
        name=f"{first_name} {last_name}",
        payment_method=payment_method,
        phone=phone,
        shipping=shipping
    )
    
    print(f"Created Stripe customer with ID: {customer.id}")
    return customer.id