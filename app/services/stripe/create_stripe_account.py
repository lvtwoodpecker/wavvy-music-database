from uuid import uuid4
import stripe
from supabase import Client
from app.db.tables.User import User
from app.db.tables.StripeAccount import StripeAccount

class StripeAccountService:
    """Service for managing Stripe accounts and customers."""
    
    def __init__(self, stripe_api_key: str):
        stripe.api_key = stripe_api_key
        
    
    def create_local_stripe_account_record(
        self,
        sb : Client,
        user_id: str, 
        stripe_customer_id: str, 
        is_default: int = 1
        ) -> dict:
        """Creates a local record in the StripeAccount table for a user."""
        
        try:
            resp = (
                sb.table(StripeAccount.TABLE_NAME)
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

    def delete_stripe_account_by_user_id(
        self, 
        sb: Client,
        user_id: str
    ) -> None:
        """Deletes the Stripe account record for a given user ID."""
        print(f"Deleting stripe account for user ID: {user_id}")
        try:
            resp = (
                sb
                .table(StripeAccount.TABLE_NAME)
                .delete()
                .eq(StripeAccount.USER_ID, user_id)
                .execute()
            )
            return {"result": resp}
        except Exception as e:
            print(f"Error deleting stripe_account row for user ID {user_id}: {e}")
            raise RuntimeError("Failed to delete stripe_account row")

    def create_stripe_customer(
        self,
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