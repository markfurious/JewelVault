"""
Authentication API endpoints.
Handles user login, logout, registration, and user management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserChangePassword,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_user,
    get_user_by_id,
    get_user_by_username,
    list_users,
    update_user_role,
    toggle_user_active,
    toggle_user_locked,
    delete_user,
    update_login_status,
    create_admin_user_if_not_exists,
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme
security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Raises 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, payload.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require admin role (super_admin or company_admin).
    Raises 403 if user is not an admin.
    """
    if current_user.role not in ["super_admin", "company_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require super_admin role (access to all companies).
    Raises 403 if user is not a super admin.
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required",
        )
    return current_user


@router.post("/login", response_model=TokenResponse)
def login(request_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with username and password.
    Returns access token and refresh token.
    """
    user = authenticate_user(db, request_data.username, request_data.password)

    if not user:
        # Check if user exists but is locked
        existing_user = get_user_by_username(db, request_data.username)
        if existing_user and existing_user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked due to too many failed login attempts",
            )
        update_login_status(db, existing_user, success=False) if existing_user else None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update login status
    update_login_status(db, user, success=True)

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request_data: dict, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    """
    refresh_token = request_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )

    payload = decode_token(refresh_token)
    if not payload or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = get_user_by_id(db, payload.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Generate new tokens
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Register a new user (super_admin only).
    Only super admins can create new users and assign roles.
    """
    try:
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
            company_id=user_data.company_id,
        )
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    List all users (super_admin only).
    """
    return list_users(db, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Get a specific user by ID (super_admin only).
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Update a user (super_admin only).
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.role is not None:
        if user_data.role not in ["super_admin", "company_admin", "company_user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.company_id is not None:
        user.company_id = user_data.company_id

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: str,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Change a user's role (super_admin only).
    """
    try:
        user = update_user_role(db, user_id, role)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/users/{user_id}/toggle-active", response_model=UserResponse)
def toggle_active(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Toggle a user's active status (super_admin only).
    """
    user = toggle_user_active(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/toggle-locked", response_model=UserResponse)
def toggle_locked(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Toggle a user's locked status (super_admin only).
    """
    user = toggle_user_locked(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Delete a user (super_admin only).
    """
    # Prevent self-deletion
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    if not delete_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.on_event("startup")
async def startup_event():
    """Create default admin user on startup if not exists."""
    from app.db.base import SessionFactory

    db = SessionFactory()
    try:
        admin = create_admin_user_if_not_exists(db)
        if admin:
            print(f"Created default admin user: {admin.username}")
    finally:
        db.close()
