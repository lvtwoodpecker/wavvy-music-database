from app.services.user.user_service import UserService
from app.services.stripe.stripe_service import StripeService


class APIServices:
    
    def __init__(self, app):
        self._stripe_service = StripeService(app)
        self._user_service = UserService(app, stripe_service=self._stripe_service)
    
    @property
    def user_service(self) -> UserService:
        return self._user_service
    
    @property
    def stripe_service(self) -> StripeService:
        return self._stripe_service
    
    def create_services(self):
        self._stripe_service.create_service()
        self._user_service.create_service()