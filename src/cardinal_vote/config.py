"""Configuration settings for the Generalized Voting Platform."""

import os
from pathlib import Path


class Settings:
    """Application settings and configuration."""

    # Application settings
    APP_NAME: str = "Generalized Voting Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://voting_user:voting_password_change_in_production@localhost:5432/voting_platform",
    )

    # Legacy SQLite support (backward compatibility)
    @property
    def DATABASE_PATH(self) -> str:
        """Get database path from environment or default (legacy support)."""
        return os.getenv("DATABASE_PATH", "votes.db")

    # File paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    LOGOS_DIR: Path = BASE_DIR / "logos"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"

    # Logo settings
    LOGO_PREFIX: str = "cardinal_vote"
    LOGO_EXTENSION: str = ".png"
    EXPECTED_LOGO_COUNT: int = 11

    # Vote settings
    MIN_RATING: int = -2
    MAX_RATING: int = 2
    MAX_VOTER_NAME_LENGTH: int = 100

    # CORS settings
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # JWT Authentication settings
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "jwt_secret_key_change_in_production_extremely_long_and_secure",
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # Email service configuration
    EMAIL_BACKEND: str = os.getenv("EMAIL_BACKEND", "mock")  # 'mock' or 'smtp'
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@voting-platform.local")

    # File storage configuration
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH", "/app/uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

    # Super Admin configuration (for platform management)
    SUPER_ADMIN_EMAIL: str = os.getenv(
        "SUPER_ADMIN_EMAIL", "admin@voting-platform.local"
    )
    SUPER_ADMIN_PASSWORD: str = os.getenv(
        "SUPER_ADMIN_PASSWORD", "super_admin_password_change_in_production"
    )

    # Security settings
    MAX_VOTES_PER_IP_PER_HOUR: int = 5  # Rate limiting

    # Content moderation rate limiting
    FLAG_RATE_LIMIT: int = int(os.getenv("FLAG_RATE_LIMIT", "5"))  # flags per minute
    FLAG_RATE_WINDOW_MINUTES: int = int(
        os.getenv("FLAG_RATE_WINDOW_MINUTES", "1")
    )  # window in minutes

    # Legacy Admin settings (backward compatibility)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "")
    SESSION_LIFETIME_HOURS: int = int(os.getenv("SESSION_LIFETIME_HOURS", "8"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_ATTEMPT_WINDOW_MINUTES: int = int(
        os.getenv("LOGIN_ATTEMPT_WINDOW_MINUTES", "15")
    )

    # File upload settings (updated for generalized platform)
    ALLOWED_UPLOAD_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    UPLOAD_TEMP_DIR: Path = BASE_DIR / "temp_uploads"

    @property
    def UPLOAD_DIR(self) -> Path:
        """Get upload directory path."""
        return Path(self.UPLOAD_PATH)

    @classmethod
    def validate_directories(cls) -> None:
        """Validate that required directories exist."""
        directories = [
            ("LOGOS_DIR", cls.LOGOS_DIR),
            ("TEMPLATES_DIR", cls.TEMPLATES_DIR),
            ("STATIC_DIR", cls.STATIC_DIR),
        ]

        missing_dirs = []
        for name, path in directories:
            if not path.exists():
                missing_dirs.append(f"{name}: {path}")

        if missing_dirs:
            raise ValueError(f"Missing required directories: {', '.join(missing_dirs)}")

        # Create upload temp directory if it doesn't exist
        if not cls.UPLOAD_TEMP_DIR.exists():
            cls.UPLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_security(cls) -> None:
        """Validate that required security settings are properly configured."""
        missing_settings = []

        # JWT authentication requirements
        jwt_default = "jwt_secret_key_change_in_production_extremely_long_and_secure"
        if not cls.JWT_SECRET_KEY or cls.JWT_SECRET_KEY == jwt_default:
            missing_settings.append("JWT_SECRET_KEY (must be changed from default)")

        # Super admin requirements
        if not cls.SUPER_ADMIN_EMAIL:
            missing_settings.append("SUPER_ADMIN_EMAIL")
        admin_default = "super_admin_" + "password_change_in_production"
        if not cls.SUPER_ADMIN_PASSWORD or cls.SUPER_ADMIN_PASSWORD == admin_default:
            missing_settings.append(
                "SUPER_ADMIN_PASSWORD (must be changed from default)"
            )

        # Legacy admin settings (if using legacy mode)
        if cls.ADMIN_USERNAME and not cls.ADMIN_PASSWORD:
            missing_settings.append(
                "ADMIN_PASSWORD (required when ADMIN_USERNAME is set)"
            )
        if cls.ADMIN_PASSWORD and not cls.ADMIN_USERNAME:
            missing_settings.append(
                "ADMIN_USERNAME (required when ADMIN_PASSWORD is set)"
            )
        if (cls.ADMIN_USERNAME or cls.ADMIN_PASSWORD) and not cls.SESSION_SECRET_KEY:
            missing_settings.append(
                "SESSION_SECRET_KEY (required for legacy admin sessions)"
            )

        if missing_settings:
            raise ValueError(
                f"Missing or insecure security settings: {', '.join(missing_settings)}. "
                "Please set these environment variables with secure values before running the application."
            )

    @classmethod
    def validate_database(cls) -> None:
        """Validate database configuration."""
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required for PostgreSQL connection")

        if "postgresql" not in cls.DATABASE_URL:
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")

    @classmethod
    def validate_email(cls) -> None:
        """Validate email configuration."""
        if cls.EMAIL_BACKEND == "smtp":
            missing_settings = []
            if not cls.SMTP_HOST:
                missing_settings.append("SMTP_HOST")
            if not cls.SMTP_USER:
                missing_settings.append("SMTP_USER")
            if not cls.SMTP_PASSWORD:
                missing_settings.append("SMTP_PASSWORD")
            if not cls.FROM_EMAIL:
                missing_settings.append("FROM_EMAIL")

            if missing_settings:
                raise ValueError(
                    f"SMTP email backend requires: {', '.join(missing_settings)}. "
                    "Set EMAIL_BACKEND=mock for development."
                )

    @classmethod
    def get_logo_files(cls) -> list[str]:
        """Get list of available logo files."""
        if not cls.LOGOS_DIR.exists():
            return []

        logo_files = []
        for file_path in cls.LOGOS_DIR.glob(f"{cls.LOGO_PREFIX}*{cls.LOGO_EXTENSION}"):
            logo_files.append(file_path.name)

        return sorted(logo_files)

    @classmethod
    def validate_all(cls) -> None:
        """Validate all configuration settings."""
        cls.validate_directories()
        cls.validate_database()
        cls.validate_security()
        cls.validate_email()

        # Create upload directory if it doesn't exist
        upload_dir = Path(cls.UPLOAD_PATH)
        if not upload_dir.exists():
            upload_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_config_info(cls) -> dict:
        """Get configuration information for debugging/status."""
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "database_type": "PostgreSQL"
            if "postgresql" in cls.DATABASE_URL
            else "Unknown",
            "email_backend": cls.EMAIL_BACKEND,
            "jwt_algorithm": cls.JWT_ALGORITHM,
            "upload_path": cls.UPLOAD_PATH,
            "max_file_size_mb": cls.MAX_FILE_SIZE_MB,
            "allowed_extensions": sorted(cls.ALLOWED_UPLOAD_EXTENSIONS),
        }


settings = Settings()
