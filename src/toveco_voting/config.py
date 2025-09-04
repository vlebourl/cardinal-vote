"""Configuration settings for the ToV'éCo voting platform."""

import os
from pathlib import Path


class Settings:
    """Application settings and configuration."""

    # Application settings
    APP_NAME: str = "ToV'éCo Logo Voting Platform"
    APP_VERSION: str = "1.1.1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database settings
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "votes.db")

    # File paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    LOGOS_DIR: Path = BASE_DIR / "logos"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"

    # Logo settings
    LOGO_PREFIX: str = "toveco"
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

    # Security settings
    MAX_VOTES_PER_IP_PER_HOUR: int = 5  # Rate limiting
    
    # Admin settings
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")  # Change in production!
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "")
    SESSION_LIFETIME_HOURS: int = int(os.getenv("SESSION_LIFETIME_HOURS", "8"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_ATTEMPT_WINDOW_MINUTES: int = int(os.getenv("LOGIN_ATTEMPT_WINDOW_MINUTES", "15"))
    
    # File upload settings
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
    ALLOWED_UPLOAD_EXTENSIONS: set[str] = {".png"}
    UPLOAD_TEMP_DIR: Path = BASE_DIR / "temp_uploads"

    @classmethod
    def validate_directories(cls) -> None:
        """Validate that required directories exist."""
        directories = [
            ("LOGOS_DIR", cls.LOGOS_DIR),
            ("TEMPLATES_DIR", cls.TEMPLATES_DIR),
            ("STATIC_DIR", cls.STATIC_DIR)
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
    def get_logo_files(cls) -> list[str]:
        """Get list of available logo files."""
        if not cls.LOGOS_DIR.exists():
            return []

        logo_files = []
        for file_path in cls.LOGOS_DIR.glob(f"{cls.LOGO_PREFIX}*{cls.LOGO_EXTENSION}"):
            logo_files.append(file_path.name)

        return sorted(logo_files)


settings = Settings()

