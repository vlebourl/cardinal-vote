"""Database models for the Cardinal Vote generalized voting platform."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import CITEXT, INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

Base: DeclarativeMeta = declarative_base()


class VoteRecord(Base):
    """SQLAlchemy model for storing vote records."""

    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    voter_first_name = Column(String(50), nullable=False)
    voter_last_name = Column(String(50), nullable=False)
    voter_name = Column(String(100), nullable=True)  # Keep for backward compatibility
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    ratings = Column(Text, nullable=False)  # JSON string of option ratings

    def __repr__(self) -> str:
        full_name = f"{self.voter_first_name} {self.voter_last_name}"
        return f"<VoteRecord(id={self.id}, voter='{full_name}')>"

    @property
    def full_name(self) -> str:
        """Get the full name of the voter."""
        return f"{self.voter_first_name} {self.voter_last_name}"


# Generalized Platform Models (PostgreSQL)


class User(Base):
    """SQLAlchemy model for generalized platform users."""

    __tablename__ = "users"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    email = Column(CITEXT, unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login = Column(DateTime(timezone=True))

    # Dashboard system enhancements
    role = Column(
        Enum("user", "super_admin", name="user_role_enum"),
        nullable=False,
        server_default="user",
    )
    preferences = Column(JSONB, nullable=True)  # Dashboard settings and preferences

    # Relationships
    votes: Mapped["list[Vote]"] = relationship(
        "Vote", back_populates="creator", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_is_super_admin", "is_super_admin"),
        Index("idx_users_role", "role"),
        Index("idx_users_role_active", "role", "is_verified"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

    @property
    def full_name(self) -> str:
        """Get the full name of the user."""
        return f"{self.first_name} {self.last_name}"


class Dashboard(Base):
    """SQLAlchemy model for user dashboard configurations."""

    __tablename__ = "dashboards"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    layout_config = Column(JSONB, nullable=True)
    theme_preference = Column(String(20), nullable=False, server_default="light")
    notification_settings = Column(JSONB, nullable=True)
    last_accessed = Column(DateTime(timezone=True))
    widget_states = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "theme_preference IN ('light', 'dark', 'auto')",
            name="check_theme_preference",
        ),
        Index("idx_dashboards_user_id", "user_id"),
        Index("idx_dashboards_last_accessed", "last_accessed"),
        Index("idx_dashboards_theme", "theme_preference"),
    )

    def __repr__(self) -> str:
        return f"<Dashboard(id={self.id}, user_id={self.user_id}, theme='{self.theme_preference}')>"


class UserActivity(Base):
    """SQLAlchemy model for tracking user activities and analytics."""

    __tablename__ = "user_activities"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_type = Column(
        Enum(
            "login",
            "logout",
            "vote_created",
            "vote_participated",
            "vote_modified",
            "vote_closed",
            "vote_shared",
            "dashboard_viewed",
            "profile_updated",
            "preferences_updated",
            name="activity_type_enum",
        ),
        nullable=False,
    )
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(PostgreSQL_UUID(as_uuid=True), nullable=True)
    activity_data = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "(entity_type IS NULL AND entity_id IS NULL) OR (entity_type IS NOT NULL AND entity_id IS NOT NULL)",
            name="check_entity_consistency",
        ),
        Index("idx_user_activities_user_id", "user_id"),
        Index("idx_user_activities_created_at", "created_at"),
        Index("idx_user_activities_user_time", "user_id", "created_at"),
        Index("idx_user_activities_activity_type", "activity_type"),
        Index("idx_user_activities_entity", "entity_type", "entity_id"),
        Index(
            "idx_user_activities_dashboard", "user_id", "activity_type", "created_at"
        ),
    )

    def __repr__(self) -> str:
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type='{self.activity_type}')>"


class Statistics(Base):
    """SQLAlchemy model for aggregated metrics and dashboard statistics."""

    __tablename__ = "statistics"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    metric_type = Column(
        Enum(
            "votes_created",
            "votes_participated",
            "votes_closed",
            "responses_received",
            "user_logins",
            "dashboard_views",
            "vote_shares",
            "avg_response_time",
            "system_total_users",
            "system_total_votes",
            "system_total_responses",
            "system_active_votes",
            "user_engagement_score",
            name="metric_type_enum",
        ),
        nullable=False,
    )
    user_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # NULL for system-wide statistics
    )
    time_period = Column(
        Enum(
            "daily",
            "weekly",
            "monthly",
            "quarterly",
            "yearly",
            "all_time",
            name="time_period_enum",
        ),
        nullable=False,
    )
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    metric_value = Column(Numeric(precision=15, scale=4), nullable=False)
    additional_data = Column(JSONB, nullable=True)
    calculated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_current = Column(Boolean, nullable=False, server_default="true")

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("period_start <= period_end", name="check_period_order"),
        UniqueConstraint(
            "metric_type",
            "user_id",
            "time_period",
            "period_start",
            "is_current",
            name="unique_current_statistic",
        ),
        Index("idx_statistics_metric_type", "metric_type"),
        Index("idx_statistics_user_id", "user_id"),
        Index("idx_statistics_time_period", "time_period"),
        Index("idx_statistics_calculated_at", "calculated_at"),
        Index("idx_statistics_is_current", "is_current"),
        Index("idx_statistics_user_current", "user_id", "is_current"),
        Index(
            "idx_statistics_metric_user_current", "metric_type", "user_id", "is_current"
        ),
        Index(
            "idx_statistics_period_range", "time_period", "period_start", "period_end"
        ),
    )

    def __repr__(self) -> str:
        return f"<Statistics(id={self.id}, metric='{self.metric_type}', value={self.metric_value})>"


class Notification(Base):
    """SQLAlchemy model for system notifications and user messages."""

    __tablename__ = "notifications"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # NULL for system-wide notifications
    )
    notification_type = Column(
        Enum(
            "system_announcement",
            "vote_created",
            "vote_response",
            "vote_closed",
            "vote_shared",
            "account_update",
            "security_alert",
            "feature_update",
            "maintenance_notice",
            "welcome_message",
            name="notification_type_enum",
        ),
        nullable=False,
    )
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(
        Enum("low", "medium", "high", "urgent", name="priority_enum"),
        nullable=False,
        server_default="medium",
    )
    is_read = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    action_url = Column(String(500), nullable=True)
    notification_metadata = Column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("LENGTH(title) >= 1", name="check_title_length"),
        CheckConstraint("LENGTH(message) >= 1", name="check_message_length"),
        CheckConstraint(
            "expires_at IS NULL OR expires_at > created_at", name="check_expires_future"
        ),
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_created_at", "created_at"),
        Index("idx_notifications_is_read", "is_read"),
        Index("idx_notifications_priority", "priority"),
        Index("idx_notifications_type", "notification_type"),
        Index("idx_notifications_expires_at", "expires_at"),
        Index("idx_notifications_user_unread", "user_id", "is_read", "created_at"),
        Index("idx_notifications_user_priority", "user_id", "priority", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title='{self.title}', priority='{self.priority}')>"


class Vote(Base):
    """SQLAlchemy model for generalized platform votes."""

    __tablename__ = "generalized_votes"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    creator_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(200), nullable=False)
    description = Column(Text)
    slug = Column(String(255), unique=True, nullable=False)
    status = Column(String(20), default="draft", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    starts_at = Column(DateTime(timezone=True))
    ends_at = Column(DateTime(timezone=True))
    require_auth = Column(Boolean, default=False, nullable=False)
    access_code = Column(String(50), nullable=True)

    # Dashboard draft support fields
    is_draft = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    draft_expires_at = Column(DateTime(timezone=True), nullable=True)
    choice_count = Column(Integer, default=0, nullable=False)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="votes")
    options: Mapped["list[VoteOption]"] = relationship(
        "VoteOption", back_populates="vote", cascade="all, delete-orphan"
    )
    responses: Mapped["list[VoterResponse]"] = relationship(
        "VoterResponse", back_populates="vote", cascade="all, delete-orphan"
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'closed', 'disabled', 'hidden')",
            name="check_vote_status",
        ),
        Index("idx_votes_creator_id", "creator_id"),
        Index("idx_votes_slug", "slug"),
        Index("idx_votes_status", "status"),
        Index("idx_votes_created_at", "created_at"),
        # Dashboard-specific indexes
        Index("idx_votes_draft_status", "is_draft", "is_active"),
        Index("idx_votes_creator_status", "creator_id", "is_draft", "is_active"),
        Index("idx_votes_draft_expires", "draft_expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Vote(id={self.id}, title='{self.title}', status='{self.status}')>"


class VoteOption(Base):
    """SQLAlchemy model for vote options."""

    __tablename__ = "vote_options"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    vote_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("generalized_votes.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_type = Column(String(20), default="text", nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)  # Text content or image filename
    display_order = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Dashboard image upload support
    image_path = Column(String(500), nullable=True)
    text_content = Column(Text, nullable=True)  # Clearer field name for text content

    # Relationships
    vote: Mapped["Vote"] = relationship("Vote", back_populates="options")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("option_type IN ('text', 'image')", name="check_option_type"),
        Index("idx_vote_options_vote_id", "vote_id"),
        Index("idx_vote_options_display_order", "vote_id", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<VoteOption(id={self.id}, title='{self.title}', type='{self.option_type}')>"


class VoterResponse(Base):
    """SQLAlchemy model for voter responses."""

    __tablename__ = "voter_responses"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    vote_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("generalized_votes.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Optional user_id for authenticated voting (for duplicate prevention)
    user_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    voter_first_name = Column(String(100), nullable=False)
    voter_last_name = Column(String(100), nullable=False)
    voter_ip = Column(INET)
    responses = Column(JSONB, nullable=False)  # {option_id: rating}
    submitted_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    vote: Mapped["Vote"] = relationship("Vote", back_populates="responses")

    # Relationships
    user: Mapped["User"] = relationship("User")

    # Constraints and Indexes
    __table_args__ = (
        # IP-based duplicate prevention for anonymous users
        Index("idx_voter_responses_ip_unique", "vote_id", "voter_ip", unique=True),
        # User-based duplicate prevention for authenticated users
        Index("idx_voter_responses_user_unique", "vote_id", "user_id", unique=True),
        # General indexes
        Index("idx_voter_responses_vote_id", "vote_id"),
        Index("idx_voter_responses_submitted_at", "submitted_at"),
        Index("idx_voter_responses_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        full_name = f"{self.voter_first_name} {self.voter_last_name}"
        return f"<VoterResponse(id={self.id}, voter='{full_name}', vote_id={self.vote_id})>"

    @property
    def voter_full_name(self) -> str:
        """Get the full name of the voter."""
        return f"{self.voter_first_name} {self.voter_last_name}"


class VoteSubmission(BaseModel):
    """Pydantic model for vote submission validation."""

    voter_first_name: str = Field(
        ..., min_length=1, max_length=50, description="First name of the voter"
    )
    voter_last_name: str = Field(
        ..., min_length=1, max_length=50, description="Last name of the voter"
    )
    ratings: dict[str, int] = Field(..., description="Option ratings dictionary")

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
        for item, rating in v.items():
            if not isinstance(rating, int) or rating < -2 or rating > 2:
                raise ValueError(
                    f"Invalid rating {rating} for {item}. Must be integer between -2 and 2"
                )

        return v


class LegacyVoteResponse(BaseModel):
    """Pydantic model for legacy vote submission response."""

    success: bool
    message: str
    vote_id: int | None = None


class VoteResultSummary(BaseModel):
    """Pydantic model for individual vote option summary."""

    average: float = Field(..., description="Average rating for this option")
    total_votes: int = Field(..., description="Number of votes for this option")
    total_score: int = Field(..., description="Sum of all ratings for this option")
    ranking: int = Field(..., description="Ranking position (1-based)")


class VoteResults(BaseModel):
    """Pydantic model for complete voting results."""

    summary: dict[str, VoteResultSummary] = Field(
        ..., description="Per-option voting summary"
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


# Moderation Models


class VoteModerationFlag(Base):
    """SQLAlchemy model for vote moderation flags."""

    __tablename__ = "vote_moderation_flags"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    vote_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("generalized_votes.id", ondelete="CASCADE"),
        nullable=False,
    )
    flagger_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Anonymous flags allowed
    )
    flag_type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    reviewed_by = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    vote: Mapped["Vote"] = relationship("Vote")
    flagger: Mapped["User"] = relationship("User", foreign_keys=[flagger_id])
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by])

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "flag_type IN ('inappropriate_content', 'spam', 'harassment', 'copyright', 'other')",
            name="check_flag_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'resolved')",
            name="check_flag_status",
        ),
        Index("idx_moderation_flags_vote_id", "vote_id"),
        Index("idx_moderation_flags_status", "status"),
        Index("idx_moderation_flags_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<VoteModerationFlag(id={self.id}, vote_id={self.vote_id}, type='{self.flag_type}')>"


class VoteModerationAction(Base):
    """SQLAlchemy model for moderation actions taken on votes."""

    __tablename__ = "vote_moderation_actions"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    vote_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("generalized_votes.id", ondelete="CASCADE"),
        nullable=False,
    )
    moderator_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    previous_status = Column(String(20))
    new_status = Column(String(20))
    additional_data = Column(JSONB)  # For storing action-specific data
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    vote: Mapped["Vote"] = relationship("Vote")
    moderator: Mapped["User"] = relationship("User")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('close_vote', 'disable_vote', 'hide_vote', 'delete_vote', 'restore_vote', 'warning_issued')",
            name="check_action_type",
        ),
        Index("idx_moderation_actions_vote_id", "vote_id"),
        Index("idx_moderation_actions_moderator_id", "moderator_id"),
        Index("idx_moderation_actions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<VoteModerationAction(id={self.id}, action='{self.action_type}', moderator_id={self.moderator_id})>"


class AccountDeletionLog(Base):
    """SQLAlchemy model for logging account deletions for GDPR compliance."""

    __tablename__ = "account_deletion_logs"

    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    deleted_user_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        nullable=False,  # Store the deleted user's ID for audit purposes
    )
    deleted_user_email = Column(CITEXT, nullable=False)  # Store email for audit
    deleted_user_name = Column(String(200), nullable=False)  # Store full name for audit
    deletion_reason = Column(String(100), default="user_requested", nullable=False)
    deleted_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_by_user_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        nullable=True,  # NULL if user deleted their own account
    )
    ip_address = Column(INET, nullable=True)  # IP address of deletion request
    user_agent = Column(Text, nullable=True)  # User agent of deletion request
    data_summary = Column(JSONB, nullable=True)  # Summary of deleted data for audit

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "deletion_reason IN ('user_requested', 'admin_action', 'gdpr_request', 'violation')",
            name="check_deletion_reason",
        ),
        Index("idx_deletion_logs_deleted_user_id", "deleted_user_id"),
        Index("idx_deletion_logs_deleted_at", "deleted_at"),
        Index("idx_deletion_logs_email", "deleted_user_email"),
    )

    def __repr__(self) -> str:
        return f"<AccountDeletionLog(id={self.id}, user_id={self.deleted_user_id}, email='{self.deleted_user_email}')>"


# ============================================================================
# Generalized Platform Pydantic Models
# ============================================================================


class VoteCreate(BaseModel):
    """Pydantic model for creating a new vote."""

    title: str = Field(..., min_length=1, max_length=200, description="Vote title")
    description: str | None = Field(
        None, max_length=2000, description="Vote description"
    )
    slug: str | None = Field(
        None,
        min_length=3,
        max_length=255,
        description="URL slug (auto-generated if not provided)",
    )
    starts_at: datetime | None = Field(None, description="When voting starts")
    ends_at: datetime | None = Field(None, description="When voting ends")
    require_auth: bool = Field(False, description="Require user authentication to vote")
    access_code: str | None = Field(
        None, max_length=50, description="Optional access code protection"
    )
    options: list["VoteOptionCreate"] = Field(
        ..., min_length=2, max_length=20, description="Vote options"
    )

    @validator("title")
    def validate_title(cls, v: str) -> str:
        """Validate and sanitize title."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v

    @validator("slug", pre=True, always=True)
    def validate_slug(cls, v: str | None, values: dict) -> str | None:
        """Validate and generate slug if not provided."""
        if v is not None:
            v = v.strip().lower().replace(" ", "-")
            # Basic slug validation - only alphanumeric and hyphens
            if not all(c.isalnum() or c in "-_" for c in v):
                raise ValueError(
                    "Slug can only contain letters, numbers, hyphens, and underscores"
                )
        return v

    @validator("ends_at")
    def validate_end_date(cls, v: datetime | None, values: dict) -> datetime | None:
        """Validate end date is after start date."""
        if v is not None and values.get("starts_at") is not None:
            if v <= values["starts_at"]:
                raise ValueError("End date must be after start date")
        return v


class VoteUpdate(BaseModel):
    """Pydantic model for updating a vote."""

    title: str | None = Field(
        None, min_length=1, max_length=200, description="Vote title"
    )
    description: str | None = Field(
        None, max_length=2000, description="Vote description"
    )
    starts_at: datetime | None = Field(None, description="When voting starts")
    ends_at: datetime | None = Field(None, description="When voting ends")

    @validator("title")
    def validate_title(cls, v: str | None) -> str | None:
        """Validate and sanitize title."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty")
        return v


class VoteStatusUpdate(BaseModel):
    """Pydantic model for updating vote status."""

    status: str = Field(..., description="New vote status")

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed_statuses = ["draft", "active", "closed"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class VoteOptionCreate(BaseModel):
    """Pydantic model for creating vote options."""

    option_type: str = Field("text", description="Option type: text or image")
    title: str = Field(..., min_length=1, max_length=200, description="Option title")
    content: str | None = Field(None, description="Option content or image filename")
    display_order: int = Field(..., description="Display order (0-based)")

    @validator("option_type")
    def validate_option_type(cls, v: str) -> str:
        """Validate option type."""
        allowed_types = ["text", "image"]
        if v not in allowed_types:
            raise ValueError(f"Option type must be one of: {', '.join(allowed_types)}")
        return v

    @validator("title")
    def validate_title(cls, v: str) -> str:
        """Validate and sanitize title."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v

    @validator("display_order")
    def validate_display_order(cls, v: int) -> int:
        """Validate display order."""
        if v < 0:
            raise ValueError("Display order must be non-negative")
        return v


class VoteOptionUpdate(BaseModel):
    """Pydantic model for updating vote options."""

    title: str | None = Field(
        None, min_length=1, max_length=200, description="Option title"
    )
    content: str | None = Field(None, description="Option content or image filename")
    display_order: int | None = Field(None, description="Display order (0-based)")

    @validator("title")
    def validate_title(cls, v: str | None) -> str | None:
        """Validate and sanitize title."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty")
        return v

    @validator("display_order")
    def validate_display_order(cls, v: int | None) -> int | None:
        """Validate display order."""
        if v is not None and v < 0:
            raise ValueError("Display order must be non-negative")
        return v


class VoterResponseCreate(BaseModel):
    """Pydantic model for creating voter responses."""

    voter_first_name: str = Field(
        ..., min_length=1, max_length=100, description="Voter first name"
    )
    voter_last_name: str = Field(
        ..., min_length=1, max_length=100, description="Voter last name"
    )
    responses: dict[str, int] = Field(..., description="Option ID to rating mapping")
    captcha_response: str = Field(
        ..., min_length=1, description="CAPTCHA verification response token"
    )

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

    @validator("responses")
    def validate_responses(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate responses dictionary."""
        if not v:
            raise ValueError("Responses cannot be empty")

        for option_id, rating in v.items():
            # Validate UUID format for option_id
            try:
                UUID(option_id)
            except ValueError:
                raise ValueError(f"Invalid option ID format: {option_id}") from None

            # Validate rating range (configurable, using -2 to +2 as default)
            if not isinstance(rating, int) or rating < -2 or rating > 2:
                raise ValueError(
                    f"Invalid rating {rating} for option {option_id}. Must be integer between -2 and 2"
                )

        return v


# Response Models


class VoteOptionResponse(BaseModel):
    """Pydantic model for vote option response."""

    id: str
    option_type: str
    title: str
    content: str | None
    display_order: int
    created_at: datetime

    class Config:
        from_attributes = True

    @validator("id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class VoteResponse(BaseModel):
    """Pydantic model for vote response."""

    id: str
    title: str
    description: str | None
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime | None
    starts_at: datetime | None
    ends_at: datetime | None
    creator_email: str | None
    options: list[VoteOptionResponse] = []

    class Config:
        from_attributes = True

    @validator("id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class VoteListResponse(BaseModel):
    """Pydantic model for vote list response."""

    votes: list[VoteResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class VoterResponseData(BaseModel):
    """Pydantic model for voter response data."""

    id: str
    voter_first_name: str
    voter_last_name: str
    responses: dict[str, Any]
    submitted_at: datetime
    voter_ip: str | None

    class Config:
        from_attributes = True

    @validator("id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None

    @property
    def voter_full_name(self) -> str:
        """Get the full name of the voter."""
        return f"{self.voter_first_name} {self.voter_last_name}"


class VoteResultsSummary(BaseModel):
    """Pydantic model for vote results summary."""

    option_id: str
    title: str
    average_rating: float
    total_responses: int
    rating_distribution: dict[int, int]  # rating -> count
    total_score: int

    @validator("option_id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class VoteAnalytics(BaseModel):
    """Pydantic model for complete vote analytics."""

    vote_id: str
    title: str
    status: str
    total_responses: int
    created_at: datetime
    starts_at: datetime | None
    ends_at: datetime | None
    option_results: list[VoteResultsSummary]
    responses: list[VoterResponseData] | None = None  # Include for creators/admins

    class Config:
        from_attributes = True

    @validator("vote_id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class GeneralizedVoteSubmissionResponse(BaseModel):
    """Pydantic model for vote submission response."""

    success: bool
    message: str
    response_id: str | None = None
    vote_id: str

    @validator("response_id", "vote_id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class PaginationQuery(BaseModel):
    """Pydantic model for pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    status: str | None = Field(None, description="Filter by status")
    search: str | None = Field(None, description="Search in title/description")

    @validator("status")
    def validate_status(cls, v: str | None) -> str | None:
        """Validate status filter."""
        if v is not None:
            allowed_statuses = ["draft", "active", "closed", "disabled", "hidden"]
            if v not in allowed_statuses:
                raise ValueError(
                    f"Status must be one of: {', '.join(allowed_statuses)}"
                )
        return v


# ============================================================================
# Moderation Pydantic Models
# ============================================================================


class VoteFlagCreate(BaseModel):
    """Pydantic model for creating vote flags."""

    flag_type: str = Field(..., description="Type of flag")
    reason: str = Field(
        ..., min_length=10, max_length=1000, description="Detailed reason for flag"
    )

    @validator("flag_type")
    def validate_flag_type(cls, v: str) -> str:
        """Validate flag type."""
        allowed_types = [
            "inappropriate_content",
            "spam",
            "harassment",
            "copyright",
            "other",
        ]
        if v not in allowed_types:
            raise ValueError(f"Flag type must be one of: {', '.join(allowed_types)}")
        return v

    @validator("reason")
    def validate_reason(cls, v: str) -> str:
        """Validate and sanitize reason."""
        v = v.strip()
        if not v:
            raise ValueError("Reason cannot be empty")
        return v


class VoteFlagResponse(BaseModel):
    """Pydantic model for vote flag response."""

    id: str
    vote_id: str
    flag_type: str
    reason: str
    status: str
    flagger_email: str | None
    reviewer_email: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True

    @validator("id", "vote_id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class VoteFlagReview(BaseModel):
    """Pydantic model for reviewing vote flags."""

    status: str = Field(..., description="Review decision")
    review_notes: str = Field(
        ..., min_length=5, max_length=1000, description="Review notes"
    )

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate review status."""
        allowed_statuses = ["approved", "rejected", "resolved"]
        if v not in allowed_statuses:
            raise ValueError(
                f"Review status must be one of: {', '.join(allowed_statuses)}"
            )
        return v


class VoteModerationActionCreate(BaseModel):
    """Pydantic model for creating moderation actions."""

    action_type: str = Field(..., description="Type of moderation action")
    reason: str = Field(
        ..., min_length=10, max_length=1000, description="Reason for action"
    )
    additional_data: dict[str, Any] | None = Field(
        None, description="Additional action data"
    )

    @validator("action_type")
    def validate_action_type(cls, v: str) -> str:
        """Validate action type."""
        allowed_actions = [
            "close_vote",
            "disable_vote",
            "hide_vote",
            "delete_vote",
            "restore_vote",
            "warning_issued",
        ]
        if v not in allowed_actions:
            raise ValueError(
                f"Action type must be one of: {', '.join(allowed_actions)}"
            )
        return v


class VoteModerationActionResponse(BaseModel):
    """Pydantic model for moderation action response."""

    id: str
    vote_id: str
    action_type: str
    reason: str
    previous_status: str | None
    new_status: str | None
    moderator_email: str
    additional_data: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True

    @validator("id", "vote_id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class VoteModerationSummary(BaseModel):
    """Pydantic model for vote moderation summary."""

    vote_id: str
    vote_title: str
    vote_slug: str
    vote_status: str
    creator_email: str
    total_flags: int
    pending_flags: int
    approved_flags: int
    rejected_flags: int
    recent_actions: list[VoteModerationActionResponse]
    flags: list[VoteFlagResponse]

    @validator("vote_id", pre=True)
    def convert_uuid(cls, v: Any) -> str | None:
        """Convert UUID to string."""
        return str(v) if v else None


class BulkModerationActionCreate(BaseModel):
    """Pydantic model for bulk moderation actions."""

    vote_ids: list[str] = Field(
        description="List of vote IDs", min_length=1, max_length=50
    )
    action_type: str = Field(..., description="Type of moderation action")
    reason: str = Field(
        ..., min_length=10, max_length=1000, description="Reason for bulk action"
    )

    @validator("action_type")
    def validate_action_type(cls, v: str) -> str:
        """Validate action type."""
        allowed_actions = ["close_vote", "disable_vote", "hide_vote", "restore_vote"]
        if v not in allowed_actions:
            raise ValueError(
                f"Bulk action type must be one of: {', '.join(allowed_actions)}"
            )
        return v

    @validator("vote_ids")
    def validate_vote_ids(cls, v: list[str]) -> list[str]:
        """Validate UUID format for vote IDs."""
        for vote_id in v:
            try:
                UUID(vote_id)
            except ValueError:
                raise ValueError(f"Invalid vote ID format: {vote_id}") from None
        return v
