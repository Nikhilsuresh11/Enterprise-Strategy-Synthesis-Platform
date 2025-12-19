"""Authentication router for user signup and login."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Depends
from jose import JWTError, jwt
from pymongo.errors import DuplicateKeyError

from app.models.user import UserCreate, UserLogin, UserResponse
from app.utils.auth import hash_password, verify_password
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # TODO: Move to env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Global service instances (set by main.py)
db_service = None


def set_services(db):
    """Set global service instances."""
    global db_service
    db_service = db


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@router.post("/signup")
async def signup(user_data: UserCreate):
    """
    Create a new user account.
    
    Args:
        user_data: User registration data (email, password)
        
    Returns:
        Access token and user info
    """
    try:
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user in database
        email = await db_service.create_user(
            email=user_data.email,
            password_hash=password_hash
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": email})
        
        logger.info("user_signed_up", email=email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": email
            }
        }
        
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    except Exception as e:
        logger.error("signup_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create account"
        )


@router.post("/login")
async def login(credentials: UserLogin):
    """
    Authenticate user and return access token.
    
    Args:
        credentials: Login credentials (email, password)
        
    Returns:
        Access token and user info
    """
    try:
        # Get user from database
        user = await db_service.get_user_by_email(credentials.email)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Update last login
        await db_service.update_last_login(credentials.email)
        
        # Create access token
        access_token = create_access_token(data={"sub": credentials.email})
        
        logger.info("user_logged_in", email=credentials.email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": credentials.email,
                "last_login": user.get("last_login")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    
    Returns:
        Current user data
    """
    return {
        "email": current_user["email"],
        "created_at": current_user["created_at"],
        "last_login": current_user.get("last_login")
    }
