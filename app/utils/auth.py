# app/utils/auth.py
# Authentication utilities for password hashing and JWT token management

import jwt
import bcrypt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from app.config import settings
from typing import Optional, Dict, Any

# JWT Configuration
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
# Token expiration in hours - configurable via environment variable
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "168"))  # Default 7 days


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password as a string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Hashed password to verify against
        
    Returns:
        True if password matches hash, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id: int, email: str) -> str:
    """Generate a JWT token for a user.
    
    Args:
        user_id: User's unique ID
        email: User's email address
        
    Returns:
        JWT token as a string
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_request() -> Optional[str]:
    """Extract token from request headers.
    
    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    # Expect format: "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def login_required(f):
    """Decorator to protect routes that require authentication.
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            # Access current_user from request context
            user_id = request.current_user['user_id']
            return jsonify({"message": "Protected data"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Attach user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function
