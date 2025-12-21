"""Tests for Stripe account linking endpoints and services."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.stripe.create_stripe_account import StripeAccountService
from app.services.stripe.checkout import StripeCheckoutService
from app.models.StripeAccount import StripeAccount


class TestStripeAccountService:
    """Test StripeAccountService methods."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.rollback = Mock()
        session.close = Mock()
        return session
    
    @pytest.fixture
    def mock_session_factory(self, mock_db_session):
        """Create a mock session factory."""
        return lambda: mock_db_session
    
    @pytest.fixture
    def stripe_account_service(self, mock_session_factory):
        """Create StripeAccountService with mock dependencies."""
        return StripeAccountService(
            stripe_api_key="sk_test_fake_key",
            db_session_factory=mock_session_factory
        )
    
    def test_get_stripe_account_by_user_id_found(self, stripe_account_service, mock_db_session):
        """Test retrieving existing Stripe account by user ID."""
        # Mock existing account
        mock_account = StripeAccount(
            stripe_id=1,
            user_id=123,
            stripe_customer_id="cus_test123",
            is_default=True
        )
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db_session.query.return_value = mock_query
        
        # Call method
        result = stripe_account_service.get_stripe_account_by_user_id(123)
        
        # Assertions
        assert result == mock_account
        assert result.user_id == 123
        assert result.stripe_customer_id == "cus_test123"
        mock_db_session.close.assert_called_once()
    
    def test_get_stripe_account_by_user_id_not_found(self, stripe_account_service, mock_db_session):
        """Test retrieving non-existent Stripe account by user ID."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        result = stripe_account_service.get_stripe_account_by_user_id(999)
        
        assert result is None
        mock_db_session.close.assert_called_once()
    
    @patch('app.services.stripe.create_stripe_account.stripe.Customer.create')
    def test_create_or_get_stripe_customer_new(self, mock_stripe_create, stripe_account_service, mock_db_session):
        """Test creating a new Stripe customer when user has none."""
        # Mock no existing account
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Mock Stripe API response
        mock_stripe_create.return_value = Mock(id="cus_new123")
        
        # Mock the created account
        mock_account = Mock(
            stripe_id=1,
            user_id=123,
            stripe_customer_id="cus_new123",
            is_default=True
        )
        mock_account.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'created_at', mock_account.created_at)
        
        # Call method
        result = stripe_account_service.create_or_get_stripe_customer(
            user_id=123,
            email="test@example.com",
            name="Test User"
        )
        
        # Assertions
        assert result["status"] == "created"
        assert result["stripe_customer_id"] == "cus_new123"
        mock_stripe_create.assert_called_once_with(
            email="test@example.com",
            name="Test User",
            metadata={"user_id": "123"}
        )
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_or_get_stripe_customer_existing(self, stripe_account_service, mock_db_session):
        """Test retrieving existing Stripe customer."""
        from datetime import datetime
        
        # Mock existing account
        mock_account = Mock()
        mock_account.stripe_customer_id = "cus_existing123"
        mock_account.created_at = Mock()
        mock_account.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db_session.query.return_value = mock_query
        
        # Call method
        result = stripe_account_service.create_or_get_stripe_customer(
            user_id=123,
            email="test@example.com",
            name="Test User"
        )
        
        # Assertions
        assert result["status"] == "existing"
        assert result["stripe_customer_id"] == "cus_existing123"
        assert result["created_at"] == "2024-01-01T00:00:00"
        # Should not create new customer
        mock_db_session.add.assert_not_called()


def test_stripe_customer_uniqueness():
    """Test that the model enforces one Stripe account per user."""
    # This is enforced by the unique constraint on user_id in the model
    # The constraint is: user_id = Column(Integer, ForeignKey("User.user_id"), unique=True, nullable=False)
    assert hasattr(StripeAccount, 'user_id')
    
    # Verify the unique constraint exists in the column
    user_id_column = StripeAccount.__table__.columns.get('user_id')
    assert user_id_column is not None
    assert user_id_column.unique == True


def test_stripe_customer_id_uniqueness():
    """Test that stripe_customer_id is unique."""
    stripe_customer_id_column = StripeAccount.__table__.columns.get('stripe_customer_id')
    assert stripe_customer_id_column is not None
    assert stripe_customer_id_column.unique == True


class TestStripeCheckoutService:
    """Test StripeCheckoutService methods."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock()
        session.query = Mock()
        session.close = Mock()
        return session
    
    @pytest.fixture
    def mock_session_factory(self, mock_db_session):
        """Create a mock session factory."""
        return lambda: mock_db_session
    
    @pytest.fixture
    def checkout_service(self, mock_session_factory):
        """Create StripeCheckoutService with mock dependencies."""
        return StripeCheckoutService(
            stripe_api_key="sk_test_fake_key",
            front_end_url="http://localhost:5173",
            db_session_factory=mock_session_factory
        )
    
    def test_checkout_requires_connected_account(self, checkout_service, mock_db_session):
        """Test that checkout requires a connected Stripe account by default."""
        # Mock no existing account
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Should raise ValueError when user doesn't have connected account
        with pytest.raises(ValueError) as exc_info:
            checkout_service.create_checkout_session(
                user_id=123,
                amount_cents=999,
                payment_for="Premium Subscription"
            )
        
        assert "connect a Stripe account" in str(exc_info.value)
        mock_db_session.close.assert_called_once()
    
    @patch('app.services.stripe.checkout.stripe.checkout.Session.create')
    def test_checkout_with_connected_account(self, mock_stripe_create, checkout_service, mock_db_session):
        """Test that checkout works when user has connected Stripe account."""
        # Mock existing account
        mock_account = Mock()
        mock_account.stripe_customer_id = "cus_test123"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db_session.query.return_value = mock_query
        
        # Mock Stripe session creation
        mock_session = Mock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test123"
        mock_stripe_create.return_value = mock_session
        
        # Call method
        result = checkout_service.create_checkout_session(
            user_id=123,
            amount_cents=999,
            payment_for="Premium Subscription"
        )
        
        # Assertions
        assert result["checkout_url"] == "https://checkout.stripe.com/test"
        assert result["session_id"] == "cs_test123"
        
        # Verify Stripe was called with customer ID
        call_args = mock_stripe_create.call_args
        assert call_args[1]["customer"] == "cus_test123"
        mock_db_session.close.assert_called_once()
    
    @patch('app.services.stripe.checkout.stripe.checkout.Session.create')
    def test_checkout_without_requirement(self, mock_stripe_create, checkout_service, mock_db_session):
        """Test that checkout can work without connected account when not required."""
        # Mock no existing account
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Mock Stripe session creation
        mock_session = Mock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test123"
        mock_stripe_create.return_value = mock_session
        
        # Call method with require_connected_account=False
        result = checkout_service.create_checkout_session(
            user_id=123,
            amount_cents=999,
            payment_for="Premium Subscription",
            require_connected_account=False
        )
        
        # Assertions
        assert result["checkout_url"] == "https://checkout.stripe.com/test"
        assert result["session_id"] == "cs_test123"
        
        # Verify Stripe was called without customer ID
        call_args = mock_stripe_create.call_args
        assert "customer" not in call_args[1]
        mock_db_session.close.assert_called_once()
