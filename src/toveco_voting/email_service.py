"""Email service for the generalized voting platform."""

import logging
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from .config import settings

logger = logging.getLogger(__name__)


class EmailServiceBase(ABC):
    """Abstract base class for email services."""

    @abstractmethod
    async def send_verification_email(
        self, email: str, user_name: str, verification_token: str
    ) -> bool:
        """Send email verification email."""
        pass

    @abstractmethod
    async def send_password_reset_email(
        self, email: str, user_name: str, reset_token: str
    ) -> bool:
        """Send password reset email."""
        pass

    @abstractmethod
    async def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email after verification."""
        pass


class MockEmailService(EmailServiceBase):
    """Mock email service for development - logs emails to console."""

    def __init__(self):
        """Initialize mock email service."""
        self.from_email = getattr(
            settings, "FROM_EMAIL", "noreply@voting-platform.local"
        )
        logger.info("Initialized Mock Email Service (Development Mode)")

    async def send_verification_email(
        self, email: str, user_name: str, verification_token: str
    ) -> bool:
        """Send email verification email (mock - logs to console)."""
        try:
            # In development, we'll create a mock verification URL
            verification_url = (
                f"http://localhost:8000/api/auth/verify?token={verification_token}"
            )

            # Create email content
            subject = "Verify your Voting Platform account"
            html_content = f"""
            <html>
                <body>
                    <h2>Welcome to the Voting Platform, {user_name}!</h2>
                    <p>Please click the link below to verify your email address:</p>
                    <p><a href="{verification_url}">Verify Email Address</a></p>
                    <p>Or copy and paste this URL in your browser:</p>
                    <p>{verification_url}</p>
                    <p>This verification link will expire in 24 hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </body>
            </html>
            """

            text_content = f"""
            Welcome to the Voting Platform, {user_name}!

            Please click the link below to verify your email address:
            {verification_url}

            This verification link will expire in 24 hours.

            If you didn't create an account, you can safely ignore this email.
            """

            # Log the email to console (development mode)
            logger.info("=" * 60)
            logger.info("📧 MOCK EMAIL - VERIFICATION")
            logger.info("=" * 60)
            logger.info(f"To: {email}")
            logger.info(f"From: {self.from_email}")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 60)
            logger.info("Email Content:")
            logger.info(text_content)
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False

    async def send_password_reset_email(
        self, email: str, user_name: str, reset_token: str
    ) -> bool:
        """Send password reset email (mock - logs to console)."""
        try:
            # In development, we'll create a mock reset URL
            reset_url = f"http://localhost:8000/auth/reset-password?token={reset_token}"

            # Create email content
            subject = "Reset your Voting Platform password"
            html_content = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hello {user_name},</p>
                    <p>You requested a password reset for your Voting Platform account.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{reset_url}">Reset Password</a></p>
                    <p>Or copy and paste this URL in your browser:</p>
                    <p>{reset_url}</p>
                    <p>This reset link will expire in 1 hour.</p>
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                </body>
            </html>
            """

            text_content = f"""
            Password Reset Request

            Hello {user_name},

            You requested a password reset for your Voting Platform account.

            Click the link below to reset your password:
            {reset_url}

            This reset link will expire in 1 hour.

            If you didn't request a password reset, you can safely ignore this email.
            """

            # Log the email to console (development mode)
            logger.info("=" * 60)
            logger.info("📧 MOCK EMAIL - PASSWORD RESET")
            logger.info("=" * 60)
            logger.info(f"To: {email}")
            logger.info(f"From: {self.from_email}")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 60)
            logger.info("Email Content:")
            logger.info(text_content)
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False

    async def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email after verification (mock - logs to console)."""
        try:
            # Create email content
            subject = "Welcome to the Voting Platform!"
            html_content = f"""
            <html>
                <body>
                    <h2>Welcome to the Voting Platform, {user_name}!</h2>
                    <p>Your email has been successfully verified.</p>
                    <p>You can now:</p>
                    <ul>
                        <li>Create voting campaigns</li>
                        <li>Manage your votes</li>
                        <li>View results and analytics</li>
                    </ul>
                    <p>Get started by logging in and creating your first vote!</p>
                    <p><a href="http://localhost:8000">Login to Voting Platform</a></p>
                </body>
            </html>
            """

            text_content = f"""
            Welcome to the Voting Platform, {user_name}!

            Your email has been successfully verified.

            You can now:
            - Create voting campaigns
            - Manage your votes
            - View results and analytics

            Get started by logging in and creating your first vote!

            Visit: http://localhost:8000
            """

            # Log the email to console (development mode)
            logger.info("=" * 60)
            logger.info("📧 MOCK EMAIL - WELCOME")
            logger.info("=" * 60)
            logger.info(f"To: {email}")
            logger.info(f"From: {self.from_email}")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 60)
            logger.info("Email Content:")
            logger.info(text_content)
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
            return False


class SMTPEmailService(EmailServiceBase):
    """SMTP email service for production use."""

    def __init__(self):
        """Initialize SMTP email service."""
        self.smtp_host = getattr(settings, "SMTP_HOST", "localhost")
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", "")
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", "")
        self.from_email = getattr(
            settings, "FROM_EMAIL", "noreply@voting-platform.local"
        )
        self.use_tls = True

        logger.info(
            f"Initialized SMTP Email Service (Host: {self.smtp_host}:{self.smtp_port})"
        )

    async def _send_email(
        self, to_email: str, subject: str, html_content: str, text_content: str
    ) -> bool:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # Create text and HTML parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            # Add parts to message
            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=self.use_tls,
                username=self.smtp_user if self.smtp_user else None,
                password=self.smtp_password if self.smtp_password else None,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_verification_email(
        self, email: str, user_name: str, verification_token: str
    ) -> bool:
        """Send email verification email via SMTP."""
        verification_url = (
            f"http://voting-platform.local/api/auth/verify?token={verification_token}"
        )

        subject = "Verify your Voting Platform account"
        html_content = f"""
        <html>
            <body>
                <h2>Welcome to the Voting Platform, {user_name}!</h2>
                <p>Please click the link below to verify your email address:</p>
                <p><a href="{verification_url}">Verify Email Address</a></p>
                <p>This verification link will expire in 24 hours.</p>
                <p>If you didn't create an account, you can safely ignore this email.</p>
            </body>
        </html>
        """

        text_content = f"""
        Welcome to the Voting Platform, {user_name}!

        Please visit this URL to verify your email address:
        {verification_url}

        This verification link will expire in 24 hours.

        If you didn't create an account, you can safely ignore this email.
        """

        return await self._send_email(email, subject, html_content, text_content)

    async def send_password_reset_email(
        self, email: str, user_name: str, reset_token: str
    ) -> bool:
        """Send password reset email via SMTP."""
        reset_url = (
            f"http://voting-platform.local/auth/reset-password?token={reset_token}"
        )

        subject = "Reset your Voting Platform password"
        html_content = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hello {user_name},</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This reset link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, you can safely ignore this email.</p>
            </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        Hello {user_name},

        Visit this URL to reset your password:
        {reset_url}

        This reset link will expire in 1 hour.

        If you didn't request a password reset, you can safely ignore this email.
        """

        return await self._send_email(email, subject, html_content, text_content)

    async def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email via SMTP."""
        subject = "Welcome to the Voting Platform!"
        html_content = f"""
        <html>
            <body>
                <h2>Welcome to the Voting Platform, {user_name}!</h2>
                <p>Your email has been successfully verified.</p>
                <p>You can now create voting campaigns and manage your votes!</p>
                <p><a href="http://voting-platform.local">Login to Voting Platform</a></p>
            </body>
        </html>
        """

        text_content = f"""
        Welcome to the Voting Platform, {user_name}!

        Your email has been successfully verified.

        You can now create voting campaigns and manage your votes!

        Visit: http://voting-platform.local
        """

        return await self._send_email(email, subject, html_content, text_content)


def get_email_service() -> EmailServiceBase:
    """Get the appropriate email service based on configuration."""
    email_backend = getattr(settings, "EMAIL_BACKEND", "mock")

    if email_backend == "smtp":
        return SMTPEmailService()
    else:
        return MockEmailService()
