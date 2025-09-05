"""Database models for the ToVéCo voting platform."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VoteRecord(Base):
    """SQLAlchemy model for storing vote records."""

    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    voter_first_name = Column(String(50), nullable=False)
    voter_last_name = Column(String(50), nullable=False)
    voter_name = Column(String(100), nullable=True)  # Keep for backward compatibility
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    ratings = Column(Text, nullable=False)  # JSON string of logo ratings

    def __repr__(self) -> str:
        full_name = f"{self.voter_first_name} {self.voter_last_name}"
        return f"<VoteRecord(id={self.id}, voter='{full_name}')>"

    @property
    def full_name(self) -> str:
        """Get the full name of the voter."""
        return f"{self.voter_first_name} {self.voter_last_name}"


class AdminUser(Base):
    """SQLAlchemy model for admin users."""

    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime)

    def __repr__(self) -> str:
        return f"<AdminUser(id={self.id}, username='{self.username}')>"


class AdminSession(Base):
    """SQLAlchemy model for admin sessions."""

    __tablename__ = "admin_sessions"

    id = Column(String(64), primary_key=True)  # Session token
    user_id = Column(Integer, nullable=False)  # Reference to admin user
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    ip_address = Column(String(45))  # IPv4/IPv6 address
    user_agent = Column(Text)

    def __repr__(self) -> str:
        return f"<AdminSession(id='{self.id[:8]}...', user_id={self.user_id})>"


class VoteSubmission(BaseModel):
    """Pydantic model for vote submission validation."""

    voter_first_name: str = Field(
        ..., min_length=1, max_length=50, description="First name of the voter"
    )
    voter_last_name: str = Field(
        ..., min_length=1, max_length=50, description="Last name of the voter"
    )
    ratings: dict[str, int] = Field(..., description="Logo ratings dictionary")

    @validator("voter_first_name")
    def validate_voter_first_name(cls, v: str) -> str:
        """Validate and sanitize voter first name."""
        v = v.strip()
        if not v:
            raise ValueError("First name cannot be empty")
        return v

    @validator("voter_last_name")
    def validate_voter_last_name(cls, v: str) -> str:
        """Validate and sanitize voter last name."""
        v = v.strip()
        if not v:
            raise ValueError("Last name cannot be empty")
        return v

    @validator("ratings")
    def validate_ratings(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate ratings dictionary."""
        if not v:
            raise ValueError("Ratings cannot be empty")

        # Validate rating values are in allowed range
        for logo, rating in v.items():
            if not isinstance(rating, int) or rating < -2 or rating > 2:
                raise ValueError(
                    f"Invalid rating {rating} for {logo}. Must be integer between -2 and 2"
                )

            # Validate logo filename format
            if not logo.startswith("toveco") or not logo.endswith(".png"):
                raise ValueError(f"Invalid logo filename: {logo}")

        return v


class VoteResponse(BaseModel):
    """Pydantic model for vote submission response."""

    success: bool
    message: str
    vote_id: int | None = None


class LogoListResponse(BaseModel):
    """Pydantic model for logo list response."""

    logos: list[str]
    total_count: int


class VoteResultSummary(BaseModel):
    """Pydantic model for individual logo vote summary."""

    average: float = Field(..., description="Average rating for this logo")
    total_votes: int = Field(..., description="Number of votes for this logo")
    total_score: int = Field(..., description="Sum of all ratings for this logo")
    ranking: int = Field(..., description="Ranking position (1-based)")


class VoteResults(BaseModel):
    """Pydantic model for complete voting results."""

    summary: dict[str, VoteResultSummary] = Field(
        ..., description="Per-logo voting summary"
    )
    total_voters: int = Field(..., description="Total number of voters")
    votes: list[dict[str, Any]] | None = Field(
        None, description="Individual vote records (admin only)"
    )


class DatabaseError(Exception):
    """Custom exception for database operations."""

    pass


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


# Admin Pydantic Models
class AdminLogin(BaseModel):
    """Pydantic model for admin login validation."""

    username: str = Field(
        ..., min_length=3, max_length=50, description="Admin username"
    )
    password: str = Field(..., min_length=6, description="Admin password")

    @validator("username")
    def validate_username(cls, v: str) -> str:
        """Validate and sanitize username."""
        v = v.strip().lower()
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers, hyphens, and underscores"
            )
        return v


class AdminUserData(BaseModel):
    """Pydantic model for admin user data."""

    id: int
    username: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class LogoUpload(BaseModel):
    """Pydantic model for logo upload validation."""

    filename: str = Field(..., description="Original filename")
    new_name: str | None = Field(None, description="New filename (optional)")

    @validator("filename")
    def validate_filename(cls, v: str) -> str:
        """Validate filename format."""
        if not v.lower().endswith(".png"):
            raise ValueError("Logo must be a PNG file")
        return v


class LogoManagement(BaseModel):
    """Pydantic model for logo management operations."""

    operation: str = Field(
        ..., description="Operation type: delete, rename, bulk_delete"
    )
    logos: list[str] = Field(..., description="List of logo filenames")
    new_name: str | None = Field(None, description="New name for rename operation")

    @validator("operation")
    def validate_operation(cls, v: str) -> str:
        """Validate operation type."""
        allowed_ops = ["delete", "rename", "bulk_delete"]
        if v not in allowed_ops:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_ops)}")
        return v


class VoteManagement(BaseModel):
    """Pydantic model for vote management operations."""

    operation: str = Field(
        ..., description="Operation type: reset, export, delete_voter"
    )
    format: str | None = Field(None, description="Export format: csv, json")
    voter_name: str | None = Field(None, description="Voter name for delete operation")

    @validator("operation")
    def validate_operation(cls, v: str) -> str:
        """Validate operation type."""
        allowed_ops = ["reset", "export", "delete_voter"]
        if v not in allowed_ops:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_ops)}")
        return v


class SystemStats(BaseModel):
    """Pydantic model for system statistics."""

    total_votes: int
    total_voters: int
    total_logos: int
    database_size: str
    uptime: str
    last_vote: datetime | None = None
    disk_usage: dict[str, Any]
    memory_usage: dict[str, Any]


class AdminDashboardData(BaseModel):
    """Pydantic model for admin dashboard data."""

    stats: SystemStats
    recent_votes: list[dict[str, Any]]
    logo_count: int
    session_info: dict[str, Any]
