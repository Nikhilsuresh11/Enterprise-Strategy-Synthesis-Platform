"""Authentication service with JWT tokens and password hashing."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.logger import get_logger

logger = get_logger(__name__)

import bcrypt

# HTTP Bearer scheme for token extraction
security = HTTPBearer()

class AuthService:
    """
    Authentication service handling JWT tokens and password verification.
    
    Features:
    - JWT token creation and verification
    - Password hashing with bcrypt
    - FastAPI dependency for route protection
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_minutes: int = 1440):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes
        logger.info("auth_service_initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError:
            return False
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User's unique ID
            email: User's email
            
        Returns:
            Encoded JWT token string
        """
        expire = datetime.utcnow() + timedelta(minutes=self.expiration_minutes)
        
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info("access_token_created", user_id=user_id)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dict with 'sub' (user_id) and 'email'
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )
            return payload
        except JWTError as e:
            logger.warning("token_verification_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency that extracts and verifies the user ID from the JWT token.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user_id)):
            ...
    """
    from fastapi import Request
    
    token = credentials.credentials
    
    # We need access to app.state.auth_service, but since this is a module-level
    # dependency, we'll decode the token directly here using jose
    try:
        # Import settings to get the secret key
        from app.config import get_settings
        settings = get_settings()
        
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
