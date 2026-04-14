"""
Authentication service.
Handles password hashing, JWT token generation/validation, and user authentication.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import TokenPayload, TokenResponse
from app.core.config import settings

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(
            user_id=payload.get("sub"),
            username=payload.get("username"),
            role=payload.get("role"),
            type=payload.get("type"),
            exp=payload.get("exp"),
        )
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    Returns the user if authenticated, None otherwise.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not user.is_active:
        return None
    if user.is_locked:
        return None
    # Truncate password to 72 bytes to avoid bcrypt limitation
    if not verify_password(password[:72], user.password_hash):
        return None
    return user


def update_login_status(db: Session, user: User, success: bool = True) -> None:
    """Update user login status (last login or failed attempts)."""
    if success:
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
    else:
        # Increment failed login attempts
        current_attempts = int(user.failed_login_attempts or 0)
        user.failed_login_attempts = str(current_attempts + 1)

        # Lock account after 5 failed attempts
        if current_attempts + 1 >= 5:
            user.is_locked = True

    db.commit()


def create_user(db: Session, username: str, email: str, password: str,
                full_name: Optional[str] = None, role: str = "company_user",
                company_id: Optional[str] = None) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        username: Unique username
        email: Unique email
        password: Plain text password (will be hashed)
        full_name: Optional full name
        role: User role (super_admin, company_admin, or company_user)
        company_id: Optional company UUID

    Returns:
        Created User instance

    Raises:
        ValueError: If username or email already exists
    """
    # Check for existing user
    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing:
        if existing.username == username:
            raise ValueError(f"Username '{username}' already exists")
        raise ValueError(f"Email '{email}' already exists")

    # Validate role
    if role not in ["super_admin", "company_admin", "company_user"]:
        raise ValueError(f"Invalid role: {role}")

    # Create new user
    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        role=role,
        company_id=company_id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_admin_user_if_not_exists(db: Session) -> Optional[User]:
    """Create a default super admin user if one doesn't exist."""
    admin = db.query(User).filter(User.role == "super_admin").first()
    if admin:
        return admin

    try:
        return create_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="admin123",  # TODO: Change in production
            full_name="System Administrator",
            role="super_admin",
        )
    except ValueError:
        return None


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get a user by their UUID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by their username."""
    return db.query(User).filter(User.username == username).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list:
    """List all users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()


def update_user_role(db: Session, user_id: str, role: str) -> Optional[User]:
    """Update a user's role."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    if role not in ["super_admin", "company_admin", "company_user"]:
        raise ValueError(f"Invalid role: {role}")

    user.role = role
    db.commit()
    db.refresh(user)
    return user


def toggle_user_active(db: Session, user_id: str) -> Optional[User]:
    """Toggle a user's active status."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


def toggle_user_locked(db: Session, user_id: str) -> Optional[User]:
    """Toggle a user's locked status."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    user.is_locked = not user.is_locked
    if not user.is_locked:
        user.failed_login_attempts = 0
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user by ID."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True
