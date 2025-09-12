"""
Input Sanitization Module
Provides comprehensive input validation and sanitization for all user inputs
"""

import re
import html
import unicodedata
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Comprehensive input sanitizer for security"""

    # Maximum lengths for different input types
    MAX_LENGTHS = {
        "email": 254,           # RFC 5321
        "username": 50,
        "password": 128,        # Should be hashed anyway
        "first_name": 100,
        "last_name": 100,
        "vote_title": 200,
        "vote_description": 5000,
        "option_text": 500,
        "comment": 2000,
        "url": 2048,
        "session_slug": 50,
        "flag_reason": 500,
    }

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",                 # JavaScript protocol
        r"on\w+\s*=",                  # Event handlers
        r"data:text/html",             # Data URLs with HTML
        r"vbscript:",                  # VBScript protocol
        r"<iframe[^>]*>",              # Iframes
        r"<object[^>]*>",              # Object tags
        r"<embed[^>]*>",               # Embed tags
        r"<applet[^>]*>",              # Applet tags
        r"<link[^>]*>",                # Link tags (can load CSS)
        r"<meta[^>]*>",                # Meta tags
        r"<base[^>]*>",                # Base tags
    ]

    @classmethod
    def sanitize_text(cls, text: str, max_length: Optional[int] = None,
                     allow_html: bool = False, field_name: str = "text") -> str:
        """
        Sanitize general text input

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (will be escaped if False)
            field_name: Name of field for max length lookup

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Convert to string if not already
        text = str(text)

        # Normalize unicode
        text = unicodedata.normalize("NFKC", text)

        # Remove null bytes
        text = text.replace("\x00", "")

        # Strip control characters except newlines and tabs
        text = "".join(
            char for char in text
            if char in "\n\r\t" or not unicodedata.category(char).startswith("C")
        )

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Dangerous pattern detected in {field_name}: {pattern}")
                text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

        # Escape HTML if not allowed
        if not allow_html:
            text = html.escape(text)

        # Trim whitespace
        text = text.strip()

        # Apply max length
        if max_length is None:
            max_length = cls.MAX_LENGTHS.get(field_name, 1000)

        if len(text) > max_length:
            text = text[:max_length]
            logger.info(f"Text truncated for {field_name}: was {len(text)} chars")

        return text

    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """
        Sanitize and validate email address

        Args:
            email: Email address to sanitize

        Returns:
            Sanitized email or empty string if invalid
        """
        if not email:
            return ""

        email = str(email).strip().lower()

        # Remove any HTML/script attempts
        email = cls.sanitize_text(email, field_name="email", allow_html=False)

        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            logger.warning(f"Invalid email format: {email[:50]}")
            return ""

        # Check for suspicious patterns
        if ".." in email or email.startswith(".") or email.endswith("."):
            logger.warning(f"Suspicious email pattern: {email[:50]}")
            return ""

        # Limit length
        if len(email) > cls.MAX_LENGTHS["email"]:
            return ""

        return email

    @classmethod
    def sanitize_username(cls, username: str) -> str:
        """
        Sanitize username

        Args:
            username: Username to sanitize

        Returns:
            Sanitized username
        """
        if not username:
            return ""

        username = str(username).strip()

        # Remove any HTML/script attempts
        username = cls.sanitize_text(username, field_name="username", allow_html=False)

        # Allow only alphanumeric, underscore, dash
        username = re.sub(r"[^a-zA-Z0-9_-]", "", username)

        # Ensure minimum length
        if len(username) < 3:
            return ""

        # Apply max length
        if len(username) > cls.MAX_LENGTHS["username"]:
            username = username[:cls.MAX_LENGTHS["username"]]

        return username

    @classmethod
    def sanitize_password(cls, password: str) -> str:
        """
        Validate password (don't actually sanitize, just validate)

        Args:
            password: Password to validate

        Returns:
            Original password if valid, empty string otherwise
        """
        if not password:
            return ""

        password = str(password)

        # Check length
        if len(password) < 8 or len(password) > cls.MAX_LENGTHS["password"]:
            return ""

        # Don't allow null bytes
        if "\x00" in password:
            return ""

        # Password should be hashed anyway, so return as-is if valid
        return password

    @classmethod
    def sanitize_url(cls, url: str, allowed_schemes: List[str] = None) -> str:
        """
        Sanitize and validate URL

        Args:
            url: URL to sanitize
            allowed_schemes: List of allowed URL schemes

        Returns:
            Sanitized URL or empty string if invalid
        """
        if not url:
            return ""

        url = str(url).strip()

        # Default allowed schemes
        if allowed_schemes is None:
            allowed_schemes = ["http", "https"]

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            logger.warning(f"Invalid URL format: {url[:100]}")
            return ""

        # Check scheme
        if parsed.scheme not in allowed_schemes:
            logger.warning(f"Invalid URL scheme: {parsed.scheme}")
            return ""

        # Check for javascript: or data: URLs
        if url.lower().startswith(("javascript:", "data:", "vbscript:")):
            logger.warning(f"Dangerous URL scheme detected: {url[:50]}")
            return ""

        # Limit length
        if len(url) > cls.MAX_LENGTHS["url"]:
            return ""

        return url

    @classmethod
    def sanitize_slug(cls, slug: str) -> str:
        """
        Sanitize URL slug

        Args:
            slug: Slug to sanitize

        Returns:
            Sanitized slug
        """
        if not slug:
            return ""

        slug = str(slug).strip().lower()

        # Allow only alphanumeric and dash
        slug = re.sub(r"[^a-z0-9-]", "", slug)

        # Remove multiple dashes
        slug = re.sub(r"-+", "-", slug)

        # Remove leading/trailing dashes
        slug = slug.strip("-")

        # Apply max length
        if len(slug) > cls.MAX_LENGTHS["session_slug"]:
            slug = slug[:cls.MAX_LENGTHS["session_slug"]]

        return slug

    @classmethod
    def sanitize_integer(cls, value: Any, min_val: int = None,
                        max_val: int = None, default: int = 0) -> int:
        """
        Sanitize integer input

        Args:
            value: Value to sanitize
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            default: Default value if invalid

        Returns:
            Sanitized integer
        """
        try:
            result = int(value)
        except (ValueError, TypeError):
            return default

        if min_val is not None and result < min_val:
            return min_val

        if max_val is not None and result > max_val:
            return max_val

        return result

    @classmethod
    def sanitize_float(cls, value: Any, min_val: float = None,
                      max_val: float = None, default: float = 0.0) -> float:
        """
        Sanitize float input

        Args:
            value: Value to sanitize
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            default: Default value if invalid

        Returns:
            Sanitized float
        """
        try:
            result = float(value)
        except (ValueError, TypeError):
            return default

        # Check for special values
        if not (-1e308 <= result <= 1e308):  # Reasonable range
            return default

        if min_val is not None and result < min_val:
            return min_val

        if max_val is not None and result > max_val:
            return max_val

        return result

    @classmethod
    def sanitize_vote_data(cls, vote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize complete vote submission data

        Args:
            vote_data: Vote data dictionary

        Returns:
            Sanitized vote data
        """
        sanitized = {}

        # Session slug
        if "session_slug" in vote_data:
            sanitized["session_slug"] = cls.sanitize_slug(vote_data["session_slug"])

        # Option ID
        if "option_id" in vote_data:
            sanitized["option_id"] = cls.sanitize_integer(
                vote_data["option_id"], min_val=1
            )

        # Rating (for cardinal voting)
        if "rating" in vote_data:
            sanitized["rating"] = cls.sanitize_integer(
                vote_data["rating"], min_val=-2, max_val=2
            )

        # Comment
        if "comment" in vote_data:
            sanitized["comment"] = cls.sanitize_text(
                vote_data["comment"], field_name="comment"
            )

        # Voter identifier
        if "voter_id" in vote_data:
            sanitized["voter_id"] = cls.sanitize_text(
                vote_data["voter_id"], max_length=100
            )

        return sanitized

    @classmethod
    def sanitize_form_data(cls, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize general form submission data

        Args:
            form_data: Form data dictionary

        Returns:
            Sanitized form data
        """
        sanitized = {}

        for key, value in form_data.items():
            # Skip empty values
            if value is None or value == "":
                continue

            # Sanitize based on field name
            if "email" in key.lower():
                sanitized[key] = cls.sanitize_email(value)
            elif "username" in key.lower():
                sanitized[key] = cls.sanitize_username(value)
            elif "password" in key.lower():
                # Don't sanitize passwords, just validate
                sanitized[key] = cls.sanitize_password(value)
            elif "url" in key.lower() or "link" in key.lower():
                sanitized[key] = cls.sanitize_url(value)
            elif "slug" in key.lower():
                sanitized[key] = cls.sanitize_slug(value)
            elif key in ["first_name", "last_name", "title", "description", "comment"]:
                sanitized[key] = cls.sanitize_text(value, field_name=key)
            elif isinstance(value, (int, float)):
                sanitized[key] = value  # Numbers are generally safe
            elif isinstance(value, bool):
                sanitized[key] = value  # Booleans are safe
            elif isinstance(value, list):
                # Recursively sanitize list items
                sanitized[key] = [
                    cls.sanitize_text(str(item), max_length=500)
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = cls.sanitize_form_data(value)
            else:
                # Default text sanitization
                sanitized[key] = cls.sanitize_text(str(value), max_length=1000)

        return sanitized


# Convenience functions for common use cases
def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """Quick sanitization for general user input"""
    return InputSanitizer.sanitize_text(text, max_length=max_length)


def sanitize_email(email: str) -> str:
    """Quick email sanitization"""
    return InputSanitizer.sanitize_email(email)


def sanitize_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick form data sanitization"""
    return InputSanitizer.sanitize_form_data(form_data)
