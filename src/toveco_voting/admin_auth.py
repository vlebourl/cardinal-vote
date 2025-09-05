"""Admin authentication system for the ToVéCo voting platform."""

import logging
import secrets
from datetime import datetime, timedelta

import bcrypt
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .database import DatabaseManager
from .models import AdminSession, AdminUser, DatabaseError

logger = logging.getLogger(__name__)


class AdminAuthManager:
    """Manages admin authentication and session handling."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize admin authentication manager."""
        self.db_manager = db_manager
        self.serializer = URLSafeTimedSerializer(settings.SESSION_SECRET_KEY)
        self._login_attempts: dict[str, list[datetime]] = {}

        # Ensure admin user exists
        self._ensure_admin_user()

    def _ensure_admin_user(self) -> None:
        """Ensure the default admin user exists in the database."""
        try:
            with self.db_manager.get_session() as session:
                # Check if admin user exists
                admin_user = (
                    session.query(AdminUser)
                    .filter_by(username=settings.ADMIN_USERNAME)
                    .first()
                )

                if not admin_user:
                    # Create default admin user
                    hashed_password = self.hash_password(settings.ADMIN_PASSWORD)
                    admin_user = AdminUser(
                        username=settings.ADMIN_USERNAME,
                        password_hash=hashed_password,
                        is_active=True,
                    )
                    session.add(admin_user)
                    session.commit()
                    logger.info(
                        f"Created default admin user: {settings.ADMIN_USERNAME}"
                    )
                else:
                    logger.info(f"Admin user exists: {settings.ADMIN_USERNAME}")

        except SQLAlchemyError as e:
            logger.error(f"Failed to ensure admin user: {e}")
            raise DatabaseError(f"Failed to initialize admin user: {e}") from e

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check if the IP address has exceeded login attempt rate limit."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=settings.LOGIN_ATTEMPT_WINDOW_MINUTES)

        if ip_address not in self._login_attempts:
            self._login_attempts[ip_address] = []

        # Remove old attempts
        self._login_attempts[ip_address] = [
            attempt for attempt in self._login_attempts[ip_address] if attempt > cutoff
        ]

        # Check if under limit
        return len(self._login_attempts[ip_address]) < settings.MAX_LOGIN_ATTEMPTS

    def _record_login_attempt(self, ip_address: str) -> None:
        """Record a failed login attempt."""
        if ip_address not in self._login_attempts:
            self._login_attempts[ip_address] = []

        self._login_attempts[ip_address].append(datetime.utcnow())

    def authenticate_user(
        self, username: str, password: str, ip_address: str, user_agent: str
    ) -> str | None:
        """
        Authenticate a user and create a session.
        Returns session token if successful, None otherwise.
        """
        try:
            # Check rate limiting
            if not self._check_rate_limit(ip_address):
                logger.warning(f"Rate limit exceeded for IP: {ip_address}")
                return None

            with self.db_manager.get_session() as session:
                # Find user
                user = (
                    session.query(AdminUser)
                    .filter_by(username=username.lower().strip(), is_active=True)
                    .first()
                )

                if not user or not self.verify_password(password, user.password_hash):
                    self._record_login_attempt(ip_address)
                    logger.warning(
                        f"Failed login attempt for {username} from {ip_address}"
                    )
                    return None

                # Generate session token
                session_token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(
                    hours=settings.SESSION_LIFETIME_HOURS
                )

                # Create session record
                admin_session = AdminSession(
                    id=session_token,
                    user_id=user.id,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    is_active=True,
                )
                session.add(admin_session)

                # Update user's last login
                user.last_login = datetime.utcnow()
                session.commit()

                logger.info(f"Successful login for {username} from {ip_address}")
                return session_token

        except SQLAlchemyError as e:
            logger.error(f"Authentication error: {e}")
            return None

    def validate_session(self, session_token: str, ip_address: str) -> dict | None:
        """
        Validate a session token and return user info if valid.
        Returns user data dict if valid, None otherwise.
        """
        if not session_token:
            return None

        try:
            with self.db_manager.get_session() as session:
                # Find active session
                admin_session = (
                    session.query(AdminSession)
                    .filter_by(id=session_token, is_active=True)
                    .first()
                )

                if not admin_session:
                    return None

                # Check if session is expired
                if admin_session.expires_at < datetime.utcnow():
                    admin_session.is_active = False
                    session.commit()
                    logger.info(f"Session expired: {session_token[:8]}...")
                    return None

                # Get user data
                user = (
                    session.query(AdminUser)
                    .filter_by(id=admin_session.user_id, is_active=True)
                    .first()
                )

                if not user:
                    admin_session.is_active = False
                    session.commit()
                    return None

                # Optionally check IP consistency (security measure)
                if admin_session.ip_address != ip_address:
                    logger.warning(f"IP mismatch for session {session_token[:8]}...")
                    # Could invalidate session or just log for monitoring

                return {
                    "user_id": user.id,
                    "username": user.username,
                    "session_id": admin_session.id,
                    "created_at": admin_session.created_at,
                    "expires_at": admin_session.expires_at,
                }

        except SQLAlchemyError as e:
            logger.error(f"Session validation error: {e}")
            return None

    def logout_user(self, session_token: str) -> bool:
        """
        Logout a user by invalidating their session.
        Returns True if successful, False otherwise.
        """
        if not session_token:
            return False

        try:
            with self.db_manager.get_session() as session:
                admin_session = (
                    session.query(AdminSession).filter_by(id=session_token).first()
                )

                if admin_session:
                    admin_session.is_active = False
                    session.commit()
                    logger.info(f"Session logged out: {session_token[:8]}...")
                    return True

                return False

        except SQLAlchemyError as e:
            logger.error(f"Logout error: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from the database.
        Returns the number of sessions cleaned up.
        """
        try:
            with self.db_manager.get_session() as session:
                expired_sessions = (
                    session.query(AdminSession)
                    .filter(AdminSession.expires_at < datetime.utcnow())
                    .all()
                )

                count = len(expired_sessions)

                for expired_session in expired_sessions:
                    expired_session.is_active = False

                session.commit()

                if count > 0:
                    logger.info(f"Cleaned up {count} expired sessions")

                return count

        except SQLAlchemyError as e:
            logger.error(f"Session cleanup error: {e}")
            return 0

    def get_active_sessions_count(self) -> int:
        """Get the count of currently active sessions."""
        try:
            with self.db_manager.get_session() as session:
                count = (
                    session.query(AdminSession)
                    .filter_by(is_active=True)
                    .filter(AdminSession.expires_at > datetime.utcnow())
                    .count()
                )
                return count

        except SQLAlchemyError as e:
            logger.error(f"Active sessions count error: {e}")
            return 0

    def revoke_all_sessions(self) -> int:
        """
        Revoke all active sessions (emergency logout).
        Returns the number of sessions revoked.
        """
        try:
            with self.db_manager.get_session() as session:
                active_sessions = (
                    session.query(AdminSession).filter_by(is_active=True).all()
                )

                count = len(active_sessions)

                for active_session in active_sessions:
                    active_session.is_active = False

                session.commit()

                logger.warning(f"Revoked all {count} active sessions")
                return count

        except SQLAlchemyError as e:
            logger.error(f"Session revocation error: {e}")
            return 0
