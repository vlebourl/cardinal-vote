#!/usr/bin/env python3
"""
Environment Validation Script for Cardinal Vote Platform
Validates that all required security environment variables are properly configured
"""

import os
import secrets
import sys


class SecurityValidator:
    """Validates environment variables for production security requirements"""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passed: list[str] = []

    def validate_required_env(self, var_name: str, description: str) -> str | None:
        """Validate that a required environment variable is set"""
        value = os.getenv(var_name)
        if not value:
            self.errors.append(f"❌ {var_name}: {description} (REQUIRED)")
            return None
        else:
            self.passed.append(f"✅ {var_name}: Set")
            return value

    def validate_password_strength(
        self, password: str, var_name: str, min_length: int = 12
    ) -> bool:
        """Validate password strength requirements"""
        if len(password) < min_length:
            self.errors.append(
                f"❌ {var_name}: Password too short (minimum {min_length} characters)"
            )
            return False

        # Check for common weak passwords
        weak_patterns = [
            "password",
            "admin",
            "test",
            "123",
            "change_in_production",
            "default",
            "secret",
            "key",
            "cardinal",
        ]

        password_lower = password.lower()
        for pattern in weak_patterns:
            if pattern in password_lower:
                self.errors.append(f"❌ {var_name}: Contains weak pattern '{pattern}'")
                return False

        # Check for complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        complexity_score = sum([has_upper, has_lower, has_digit, has_special])

        if complexity_score < 3:
            self.warnings.append(
                f"⚠️  {var_name}: Password should contain uppercase, lowercase, numbers, and special characters"
            )

        self.passed.append(f"✅ {var_name}: Strong password")
        return True

    def validate_jwt_secret(self, secret: str) -> bool:
        """Validate JWT secret key requirements"""
        if len(secret) < 32:
            self.errors.append("❌ JWT_SECRET_KEY: Must be at least 32 characters long")
            return False

        # Check entropy - should be random
        if secret.lower() in [
            "jwt_secret_key_change_in_production_extremely_long_and_secure"
        ]:
            self.errors.append(
                "❌ JWT_SECRET_KEY: Using default/example value - generate a random secret"
            )
            return False

        self.passed.append("✅ JWT_SECRET_KEY: Appears to be secure")
        return True

    def validate_database_config(self) -> bool:
        """Validate database configuration security"""
        db_password = self.validate_required_env(
            "POSTGRES_PASSWORD", "Database password"
        )
        db_user = os.getenv("POSTGRES_USER", "voting_user")
        db_name = os.getenv("POSTGRES_DB", "voting_platform")

        if db_password:
            self.validate_password_strength(
                db_password, "POSTGRES_PASSWORD", min_length=16
            )

        # Warn about default database names/users in production
        if os.getenv("CARDINAL_ENV") == "production":
            if db_user == "voting_user":
                self.warnings.append(
                    "⚠️  POSTGRES_USER: Consider using a non-default username in production"
                )
            if db_name == "voting_platform":
                self.warnings.append(
                    "⚠️  POSTGRES_DB: Consider using a non-default database name in production"
                )

        return db_password is not None

    def validate_admin_config(self) -> bool:
        """Validate admin account configuration"""
        super_admin_password = self.validate_required_env(
            "SUPER_ADMIN_PASSWORD", "Super admin password"
        )
        admin_password = self.validate_required_env(
            "ADMIN_PASSWORD", "Legacy admin password"
        )

        valid_super = True
        valid_admin = True

        if super_admin_password:
            valid_super = self.validate_password_strength(
                super_admin_password, "SUPER_ADMIN_PASSWORD", min_length=16
            )

        if admin_password:
            valid_admin = self.validate_password_strength(
                admin_password, "ADMIN_PASSWORD", min_length=12
            )

        return valid_super and valid_admin

    def validate_jwt_config(self) -> bool:
        """Validate JWT configuration"""
        jwt_secret = self.validate_required_env("JWT_SECRET_KEY", "JWT signing secret")

        if jwt_secret:
            return self.validate_jwt_secret(jwt_secret)

        return False

    def validate_environment_type(self) -> None:
        """Validate environment type configuration"""
        env_type = os.getenv("CARDINAL_ENV", "development")
        debug = os.getenv("DEBUG", "false").lower()

        if env_type == "production":
            if debug == "true":
                self.errors.append(
                    "❌ DEBUG: Must be 'false' in production environment"
                )
            else:
                self.passed.append("✅ DEBUG: Properly disabled for production")

        self.passed.append(f"✅ CARDINAL_ENV: Set to '{env_type}'")

    def validate_session_config(self) -> bool:
        """Validate session configuration (legacy compatibility)"""
        session_secret = os.getenv("SESSION_SECRET_KEY")

        if session_secret:
            if len(session_secret) < 32:
                self.warnings.append(
                    "⚠️  SESSION_SECRET_KEY: Should be at least 32 characters for security"
                )
                return False
            elif "session_secret_key_change_in_production" in session_secret:
                self.errors.append("❌ SESSION_SECRET_KEY: Using default/example value")
                return False
            else:
                self.passed.append("✅ SESSION_SECRET_KEY: Appears secure")
        else:
            self.warnings.append(
                "⚠️  SESSION_SECRET_KEY: Not set (legacy compatibility)"
            )

        return True

    def generate_secure_examples(self) -> None:
        """Generate example secure values for missing variables"""
        print("\n🔐 SECURE VALUE EXAMPLES (generate your own!):")
        print("=" * 50)

        if not os.getenv("POSTGRES_PASSWORD"):
            print(f"POSTGRES_PASSWORD='{secrets.token_urlsafe(24)}'")

        if not os.getenv("JWT_SECRET_KEY"):
            print(f"JWT_SECRET_KEY='{secrets.token_urlsafe(48)}'")

        if not os.getenv("SUPER_ADMIN_PASSWORD"):
            # Generate a pronounceable but secure password
            words = ["Cardinal", "Vote", "Secure", "Platform"]
            numbers = secrets.randbelow(10000)
            symbols = "!@#$%"
            symbol = secrets.choice(symbols)
            print(
                f"SUPER_ADMIN_PASSWORD='{secrets.choice(words)}{numbers}{symbol}{secrets.token_urlsafe(8)}'"
            )

        if not os.getenv("ADMIN_PASSWORD"):
            print(f"ADMIN_PASSWORD='{secrets.token_urlsafe(16)}'")

    def run_validation(self) -> bool:
        """Run complete security validation"""
        print("🔍 Cardinal Vote Platform - Security Environment Validation")
        print("=" * 60)

        # Validate each component
        self.validate_environment_type()
        self.validate_database_config()
        self.validate_jwt_config()
        self.validate_admin_config()
        self.validate_session_config()

        # Additional security checks
        if os.getenv("CARDINAL_ENV") == "production":
            cors_origins = os.getenv("ALLOWED_ORIGINS", "")
            if "localhost" in cors_origins:
                self.warnings.append(
                    "⚠️  ALLOWED_ORIGINS: Contains localhost - ensure this is intended for production"
                )

        # Print results
        print(f"\n✅ PASSED CHECKS ({len(self.passed)}):")
        for item in self.passed:
            print(f"   {item}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"   {item}")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for item in self.errors:
                print(f"   {item}")

        # Generate examples for missing values
        if self.errors:
            self.generate_secure_examples()

        # Summary
        print("\n📊 VALIDATION SUMMARY:")
        print(f"   ✅ Passed: {len(self.passed)}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        print(f"   ❌ Errors: {len(self.errors)}")

        if self.errors:
            print("\n🚨 SECURITY VALIDATION FAILED")
            print("   Fix all errors before deploying to production!")
            return False
        elif self.warnings:
            print("\n⚠️  SECURITY VALIDATION PASSED WITH WARNINGS")
            print("   Consider addressing warnings for enhanced security")
            return True
        else:
            print("\n🎉 SECURITY VALIDATION PASSED")
            print("   All security requirements met!")
            return True


def main():
    """Main entry point"""
    validator = SecurityValidator()

    # Check if we're running in Docker or local environment
    if os.path.exists("/.dockerenv"):
        print("🐳 Running inside Docker container")
    else:
        print("💻 Running in local environment")

    # Run validation
    success = validator.run_validation()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
