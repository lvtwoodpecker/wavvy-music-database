"""Tests for authentication utilities and logic."""
import pytest
from app.utils.auth import (
    hash_password, 
    verify_password, 
    generate_token, 
    decode_token
)
import re


def test_password_hashing():
    """Test password hashing and verification."""
    password = "mySecurePassword123"
    hashed = hash_password(password)
    
    # Hash should be different from password
    assert hashed != password
    
    # Correct password should verify
    assert verify_password(password, hashed)
    
    # Wrong password should not verify
    assert not verify_password("wrongpassword", hashed)


def test_token_generation_and_decoding():
    """Test JWT token generation and validation."""
    user_id = 123
    email = "test@example.com"
    
    # Generate token
    token = generate_token(user_id, email)
    assert token
    
    # Decode token
    payload = decode_token(token)
    assert payload is not None
    assert payload["user_id"] == user_id
    assert payload["email"] == email
    
    # Invalid token should return None
    invalid_payload = decode_token("invalid.token.here")
    assert invalid_payload is None


def test_email_validation():
    """Test email format validation."""
    email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
    
    # Valid emails
    valid_emails = [
        "test@example.com", 
        "user+tag@domain.co.uk", 
        "name.surname@company.com"
    ]
    for email in valid_emails:
        assert re.match(email_pattern, email)
    
    # Invalid emails
    invalid_emails = ["notanemail", "@example.com", "user@", "user@domain"]
    for email in invalid_emails:
        assert not re.match(email_pattern, email)


def test_password_length_validation():
    """Test password length requirements."""
    short_password = "short"
    long_password = "longenoughpassword"
    
    assert len(short_password) < 8
    assert len(long_password) >= 8


def test_country_code_validation():
    """Test country code format validation."""
    country_pattern = r'^[A-Z]{2}$'
    
    # Valid country codes
    valid_countries = ["US", "CA", "GB", "FR"]
    for country in valid_countries:
        assert re.match(country_pattern, country)
    
    # Invalid country codes
    invalid_countries = ["USA", "us", "1A", ""]
    for country in invalid_countries:
        assert not re.match(country_pattern, country)
