"""Authentication router — register, login, and user info."""

from fastapi import APIRouter, HTTPException, Request, Depends, status

from app.models.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import get_current_user_id
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, body: UserRegister):
    """Register a new user account."""
    
    db = request.app.state.db_service
    auth = request.app.state.auth_service
    
    # Check if email already exists
    existing = await db.get_user_by_email(body.email.lower())
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )
    
    # Create user
    hashed_pw = auth.hash_password(body.password)
    user_data = {
        "name": body.name,
        "email": body.email.lower(),
        "hashed_password": hashed_pw,
    }
    
    user = await db.create_user(user_data)
    
    # Generate token
    token = auth.create_access_token(user["_id"], user["email"])
    
    logger.info("user_registered", user_id=user["_id"], email=user["email"])
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["_id"],
            name=user["name"],
            email=user["email"],
            created_at=user["created_at"]
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: UserLogin):
    """Login with email and password."""
    print('hi')
    db = request.app.state.db_service
    auth = request.app.state.auth_service
    
    # Find user
    user = await db.get_user_by_email(body.email.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not auth.verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = auth.create_access_token(user["_id"], user["email"])
    
    logger.info("user_logged_in", user_id=user["_id"])
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["_id"],
            name=user["name"],
            email=user["email"],
            created_at=user["created_at"]
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, user_id: str = Depends(get_current_user_id)):
    """Get the current authenticated user's info."""
    
    db = request.app.state.db_service
    
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["_id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"]
    )
