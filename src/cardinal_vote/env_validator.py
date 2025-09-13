"""
Comprehensive Environment Validation Module
Validates all environment variables at startup to ensure proper configuration
"""

import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Validation severity levels"""

    CRITICAL = "critical"  # Application cannot start
    ERROR = "error"  # Feature will not work
    WARNING = "warning"  # Suboptimal but functional
    INFO = "info"  # Informational


@dataclass
class ValidationRule:
    """Validation rule for an environment variable"""

    name: str
    required: bool
    level: ValidationLevel
    description: str
    validator: Callable[..., bool] | None = None
    default: str | None = None
    example: str | None = None


class EnvValidator:
    """Comprehensive environment validator"""

    def __init__(self) -> None:
        self.errors: list[tuple[ValidationLevel, str]] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def validate_all(self) -> bool:
        """Run all validations and return True if system can start"""
        self._validate_database()
        self._validate_security()
        self._validate_email()
        self._validate_application()
        self._validate_optional_features()

        return not any(level == ValidationLevel.CRITICAL for level, _ in self.errors)

    def _validate_database(self) -> None:
        """Validate database configuration"""
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            self.errors.append(
                (
                    ValidationLevel.CRITICAL,
                    "DATABASE_URL is not set. Application cannot start without database configuration.",
                )
            )
            return

        # Validate PostgreSQL URL format
        if not db_url.startswith(("postgresql://", "postgresql+asyncpg://")):
            self.errors.append(
                (
                    ValidationLevel.CRITICAL,
                    f"DATABASE_URL must be a PostgreSQL URL (got: {db_url[:30]}...)",
                )
            )
            return

        # Check for common mistakes
        if "localhost" in db_url or "127.0.0.1" in db_url:
            if os.getenv("CARDINAL_ENV") == "production":
                self.warnings.append(
                    "DATABASE_URL contains localhost in production environment. "
                    "Ensure this is intentional."
                )

        # Parse and validate components
        try:
            from urllib.parse import urlparse

            parsed = urlparse(db_url)

            if not parsed.hostname:
                self.errors.append(
                    (ValidationLevel.ERROR, "DATABASE_URL missing hostname")
                )

            if not parsed.username:
                self.warnings.append("DATABASE_URL missing username")

            if not parsed.password:
                self.errors.append(
                    (
                        ValidationLevel.ERROR,
                        "DATABASE_URL missing password - database authentication will fail",
                    )
                )

        except Exception as e:
            self.errors.append(
                (ValidationLevel.CRITICAL, f"Invalid DATABASE_URL format: {e}")
            )

    def _validate_security(self) -> None:
        """Validate security-critical environment variables"""

        # JWT Secret Key
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            self.errors.append(
                (
                    ValidationLevel.CRITICAL,
                    "JWT_SECRET_KEY is not set. Required for authentication.",
                )
            )
        elif len(jwt_secret) < 32:
            self.errors.append(
                (
                    ValidationLevel.ERROR,
                    f"JWT_SECRET_KEY too short ({len(jwt_secret)} chars). Minimum 32 characters required for security.",
                )
            )
        elif "test" in jwt_secret.lower():
            if os.getenv("CARDINAL_ENV") == "production":
                self.errors.append(
                    (
                        ValidationLevel.CRITICAL,
                        "JWT_SECRET_KEY contains 'test' in production. This is a security risk!",
                    )
                )

        # Super Admin Password
        super_admin_pass = os.getenv("SUPER_ADMIN_PASSWORD")
        if not super_admin_pass:
            self.errors.append(
                (
                    ValidationLevel.ERROR,
                    "SUPER_ADMIN_PASSWORD not set. Cannot create super admin account.",
                )
            )
        else:
            self._validate_password_strength(super_admin_pass, "SUPER_ADMIN_PASSWORD")

    def _validate_password_strength(self, password: str, var_name: str) -> None:
        """Validate password strength"""
        if len(password) < 12:
            self.warnings.append(
                f"{var_name} is weak ({len(password)} chars). Recommend 12+ characters."
            )

        # Check for common weak passwords
        weak_passwords = ["password", "admin", "123456", "test", "demo"]
        if any(weak in password.lower() for weak in weak_passwords):
            if os.getenv("CARDINAL_ENV") == "production":
                self.errors.append(
                    (
                        ValidationLevel.ERROR,
                        f"{var_name} contains common weak pattern. High security risk in production!",
                    )
                )
            else:
                self.warnings.append(f"{var_name} contains weak pattern.")

        # Check complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        complexity_score = sum([has_upper, has_lower, has_digit, has_special])
        if complexity_score < 3:
            self.info.append(
                f"{var_name} has low complexity (score: {complexity_score}/4). "
                "Consider using uppercase, lowercase, numbers, and special characters."
            )

    def _validate_email(self) -> None:
        """Validate email configuration"""
        email_backend = os.getenv("EMAIL_BACKEND", "mock")

        if email_backend == "smtp":
            smtp_host = os.getenv("SMTP_HOST")
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")

            if not smtp_host:
                self.errors.append(
                    (
                        ValidationLevel.ERROR,
                        "EMAIL_BACKEND is 'smtp' but SMTP_HOST is not set",
                    )
                )

            if not smtp_user or not smtp_password:
                self.warnings.append(
                    "SMTP authentication not configured. Email sending may fail."
                )

        # Validate FROM_EMAIL format
        from_email = os.getenv("FROM_EMAIL", "")
        if from_email and not self._is_valid_email(from_email):
            self.warnings.append(f"FROM_EMAIL has invalid format: {from_email}")

        # Super admin email
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "")
        if super_admin_email and not self._is_valid_email(super_admin_email):
            self.errors.append(
                (
                    ValidationLevel.ERROR,
                    f"SUPER_ADMIN_EMAIL has invalid format: {super_admin_email}",
                )
            )

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _validate_application(self) -> None:
        """Validate application configuration"""

        # Environment mode
        env_mode = os.getenv("CARDINAL_ENV", "development")
        if env_mode not in ["development", "test", "staging", "production"]:
            self.warnings.append(
                f"CARDINAL_ENV has unexpected value: {env_mode}. "
                "Expected: development, test, staging, or production"
            )

        # Debug mode
        debug = os.getenv("DEBUG", "false").lower()
        if debug == "true" and env_mode == "production":
            self.errors.append(
                (
                    ValidationLevel.ERROR,
                    "DEBUG is enabled in production! This exposes sensitive information.",
                )
            )

        # Port configuration
        port = os.getenv("PORT", "8000")
        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                self.warnings.append(
                    f"PORT {port_num} is outside valid range (1-65535)"
                )
        except ValueError:
            self.errors.append(
                (ValidationLevel.ERROR, f"PORT must be a number, got: {port}")
            )

        # CORS configuration
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        if env_mode == "production" and ("*" in allowed_origins or not allowed_origins):
            self.warnings.append(
                "ALLOWED_ORIGINS is too permissive for production. "
                "Specify exact allowed domains."
            )

    def _validate_optional_features(self) -> None:
        """Validate optional feature configuration"""

        # Rate limiting
        if os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "false":
            if os.getenv("CARDINAL_ENV") == "production":
                self.warnings.append(
                    "Rate limiting is disabled in production. This may allow abuse."
                )

        # File upload limits
        max_file_size = os.getenv("MAX_FILE_SIZE_MB", "10")
        try:
            size_mb = int(max_file_size)
            if size_mb > 100:
                self.warnings.append(
                    f"MAX_FILE_SIZE_MB is very large ({size_mb}MB). "
                    "This may cause memory issues."
                )
        except ValueError:
            self.warnings.append(
                f"MAX_FILE_SIZE_MB must be a number, got: {max_file_size}"
            )

    def print_report(self) -> bool:
        """Print validation report"""
        print("\n" + "=" * 60)
        print("🔍 ENVIRONMENT VALIDATION REPORT")
        print("=" * 60)

        # Critical errors
        critical_errors = [
            msg for level, msg in self.errors if level == ValidationLevel.CRITICAL
        ]
        if critical_errors:
            print("\n❌ CRITICAL ERRORS (Application cannot start):")
            for msg in critical_errors:
                print(f"   • {msg}")

        # Regular errors
        regular_errors = [
            msg for level, msg in self.errors if level == ValidationLevel.ERROR
        ]
        if regular_errors:
            print("\n❌ ERRORS (Features will not work):")
            for msg in regular_errors:
                print(f"   • {msg}")

        # Warnings
        if self.warnings:
            print("\n⚠️  WARNINGS (Suboptimal configuration):")
            for msg in self.warnings:
                print(f"   • {msg}")

        # Info
        if self.info:
            print("\nℹ️  INFO (Recommendations):")
            for msg in self.info:
                print(f"   • {msg}")

        # Summary
        print("\n" + "-" * 60)
        if critical_errors:
            print("🚨 VALIDATION FAILED - Fix critical errors before starting")
            print("-" * 60 + "\n")
            return False
        elif regular_errors:
            print("⚠️  VALIDATION PASSED WITH ERRORS - Some features may not work")
            print("-" * 60 + "\n")
            return True
        elif self.warnings:
            print("✅ VALIDATION PASSED WITH WARNINGS")
            print("-" * 60 + "\n")
            return True
        else:
            print("✅ VALIDATION PASSED - All configurations are optimal")
            print("-" * 60 + "\n")
            return True


def validate_environment(exit_on_critical: bool = True) -> bool:
    """
    Main validation function

    Args:
        exit_on_critical: If True, exit application on critical errors

    Returns:
        True if validation passed (no critical errors)
    """
    validator = EnvValidator()
    can_start = validator.validate_all()
    validator.print_report()

    if not can_start and exit_on_critical:
        sys.exit(1)

    return can_start


if __name__ == "__main__":
    # Allow running as standalone script for testing
    validate_environment(exit_on_critical=False)
