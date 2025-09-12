"""
Tests for InputSanitizer module - comprehensive security testing
"""

import pytest

from cardinal_vote.input_sanitizer import InputSanitizer


class TestInputSanitizer:
    """Test the InputSanitizer class methods"""

    def test_sanitize_text_basic(self):
        """Test basic text sanitization"""
        # Normal text should pass through unchanged
        result = InputSanitizer.sanitize_text("Hello World")
        assert result == "Hello World"

    def test_sanitize_text_xss_prevention(self):
        """Test XSS attack prevention"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "<script src='evil.js'></script>",
            "javascript:alert(1)",
            "<iframe src='evil.com'></iframe>",
            "<object data='evil.swf'></object>",
            "<embed src='evil.swf'></embed>",
            "<applet code='Evil.class'></applet>",
            "<link rel='stylesheet' href='evil.css'>",
            "<meta http-equiv='refresh' content='0;url=evil.com'>",
            "<base href='evil.com'>",
            "<div onclick='alert(1)'>Click me</div>",
            "<img onload='alert(1)' src='x'>",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
        ]

        for malicious in malicious_inputs:
            result = InputSanitizer.sanitize_text(malicious, allow_html=False)
            # Should not contain the dangerous patterns
            assert "<script" not in result.lower()
            assert "javascript:" not in result.lower()
            assert "vbscript:" not in result.lower()
            assert "onload=" not in result.lower()
            assert "onclick=" not in result.lower()

    def test_sanitize_text_html_escaping(self):
        """Test HTML escaping when HTML is not allowed"""
        input_text = "<div>Hello & goodbye</div>"
        result = InputSanitizer.sanitize_text(input_text, allow_html=False)
        assert "&lt;div&gt;" in result
        assert "&amp;" in result

    def test_sanitize_text_unicode_normalization(self):
        """Test Unicode normalization"""
        # Unicode characters that could be used for attacks
        unicode_text = "café"  # Contains composed character
        result = InputSanitizer.sanitize_text(unicode_text)
        # Should normalize to NFC form
        assert result == "café"

    def test_sanitize_text_control_characters(self):
        """Test removal of control characters"""
        text_with_controls = "Hello\x00World\x01Test\x7f"
        result = InputSanitizer.sanitize_text(text_with_controls)
        # Should remove control characters but keep normal chars
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x7f" not in result
        assert "HelloWorldTest" == result

    def test_sanitize_text_length_limits(self):
        """Test length limit enforcement"""
        long_text = "A" * 2000
        result = InputSanitizer.sanitize_text(long_text, max_length=100)
        assert len(result) == 100

        # Test with field_name lookup
        result = InputSanitizer.sanitize_text(long_text, field_name="username")
        assert len(result) <= InputSanitizer.MAX_LENGTHS["username"]

    def test_sanitize_text_utf8_safe_truncation(self):
        """Test UTF-8 safe truncation doesn't break multi-byte characters"""
        # Create a string with multi-byte characters near the truncation point
        unicode_text = "Hello 世界 " * 20  # Contains multi-byte Chinese characters

        # Truncate at a length that might split a multi-byte character
        result = InputSanitizer.sanitize_text(unicode_text, max_length=50)

        # Result should be valid UTF-8 without broken characters
        assert isinstance(result, str)

        # Should be able to encode/decode without errors
        try:
            result.encode("utf-8").decode("utf-8")
        except UnicodeDecodeError:
            pytest.fail("UTF-8 truncation broke multi-byte characters")

        # Should not be longer than max_length in characters (default behavior)
        assert len(result) <= 50

        # Test with various multi-byte characters
        test_strings = [
            "café" * 100,  # Contains accented characters
            "🚀" * 100,  # Contains emoji (4-byte UTF-8)
            "中文测试" * 50,  # Contains Chinese characters (3-byte UTF-8)
            "العربية" * 50,  # Contains Arabic (variable byte UTF-8)
        ]

        for test_string in test_strings:
            result = InputSanitizer.sanitize_text(test_string, max_length=30)
            # Should not raise encoding errors
            try:
                result.encode("utf-8").decode("utf-8")
                assert len(result) <= 30  # Character-based truncation by default
            except (UnicodeDecodeError, UnicodeEncodeError):
                pytest.fail(f"UTF-8 truncation failed for: {test_string[:20]}...")

    def test_sanitize_email_valid(self):
        """Test valid email sanitization"""
        # Test case normalization - preserves local part, normalizes domain
        assert InputSanitizer.sanitize_email("User@Example.COM") == "User@example.com"
        assert (
            InputSanitizer.sanitize_email("test.user+tag@Domain.CO.UK")
            == "test.user+tag@domain.co.uk"
        )
        assert (
            InputSanitizer.sanitize_email("user123@Test-Domain.com")
            == "user123@test-domain.com"
        )

    def test_sanitize_email_invalid(self):
        """Test invalid email rejection"""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user..double@domain.com",
            ".user@domain.com",
            "user@domain.com.",
            "user@domain",
            "",
            None,
            "x" * 300,  # Too long
        ]

        for email in invalid_emails:
            result = InputSanitizer.sanitize_email(email)
            assert result == ""

    def test_sanitize_email_security(self):
        """Test email security measures"""
        # Test control character removal
        result = InputSanitizer.sanitize_email("user\x00@example.com")
        assert "\x00" not in result

        # Test case normalization - preserves local part, normalizes domain
        result = InputSanitizer.sanitize_email("USER@EXAMPLE.COM")
        assert result == "USER@example.com"

    def test_sanitize_username_valid(self):
        """Test valid username sanitization"""
        valid_usernames = [
            "user123",
            "test_user",
            "user-name",
            "ValidUser",
        ]

        for username in valid_usernames:
            result = InputSanitizer.sanitize_username(username)
            assert result == username

    def test_sanitize_username_invalid(self):
        """Test invalid username handling"""
        invalid_usernames = [
            "ab",  # Too short
            "user@domain",  # Invalid character
            "user space",  # Space not allowed
            "<script>",  # Dangerous content
            "",
            None,
        ]

        for username in invalid_usernames:
            result = InputSanitizer.sanitize_username(username)
            # Should either be cleaned or rejected
            if result:
                assert len(result) >= 3
                assert all(c.isalnum() or c in "_-" for c in result)

    def test_sanitize_password_validation(self):
        """Test password validation"""
        # Valid passwords
        assert (
            InputSanitizer.sanitize_password("validpassword123") == "validpassword123"
        )
        assert (
            InputSanitizer.sanitize_password("Complex!Pass@2024") == "Complex!Pass@2024"
        )

        # Invalid passwords - length
        assert InputSanitizer.sanitize_password("short") == ""  # Too short
        assert InputSanitizer.sanitize_password("x" * 200) == ""  # Too long
        assert InputSanitizer.sanitize_password("") == ""

        # Invalid passwords - dangerous patterns
        assert InputSanitizer.sanitize_password("pass\x00word") == ""  # Null byte
        assert InputSanitizer.sanitize_password("pass\nword") == ""  # Line feed
        assert InputSanitizer.sanitize_password("pass\rword") == ""  # Carriage return
        assert InputSanitizer.sanitize_password("pass\tword") == ""  # Tab character
        assert InputSanitizer.sanitize_password("pass\r\nword") == ""  # CRLF injection
        assert (
            InputSanitizer.sanitize_password("pass\x01word") == ""
        )  # Control character
        assert InputSanitizer.sanitize_password("pass\x7fword") == ""  # DEL character

    def test_sanitize_url_valid(self):
        """Test valid URL sanitization"""
        valid_urls = [
            "https://example.com",
            "http://test.com/path?param=value",
            "https://sub.domain.com:8080/path",
        ]

        for url in valid_urls:
            result = InputSanitizer.sanitize_url(url)
            assert result == url

    def test_sanitize_url_invalid(self):
        """Test invalid/dangerous URL rejection"""
        dangerous_urls = [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
            "ftp://example.com",  # Not in allowed schemes
            "file:///etc/passwd",
            "",
            "not-a-url",
            "x" * 3000,  # Too long
        ]

        for url in dangerous_urls:
            result = InputSanitizer.sanitize_url(url)
            assert result == ""

    def test_sanitize_url_custom_schemes(self):
        """Test custom allowed schemes"""
        result = InputSanitizer.sanitize_url(
            "ftp://example.com", allowed_schemes=["ftp"]
        )
        assert result == "ftp://example.com"

        result = InputSanitizer.sanitize_url(
            "ftp://example.com", allowed_schemes=["http"]
        )
        assert result == ""

    def test_sanitize_slug(self):
        """Test URL slug sanitization"""
        test_cases = [
            ("Hello World", "hello-world"),
            ("Test--Multiple---Dashes", "test-multiple-dashes"),
            ("--leading-trailing--", "leading-trailing"),
            ("Special!@#$%Characters", "special-characters"),
            ("Already-Valid-Slug", "already-valid-slug"),
        ]

        for input_slug, expected in test_cases:
            result = InputSanitizer.sanitize_slug(input_slug)
            assert result == expected

    def test_sanitize_integer(self):
        """Test integer sanitization"""
        # Valid integers
        assert InputSanitizer.sanitize_integer("123") == 123
        assert InputSanitizer.sanitize_integer(456) == 456

        # Invalid inputs with default
        assert InputSanitizer.sanitize_integer("not-a-number", default=0) == 0
        assert InputSanitizer.sanitize_integer(None, default=42) == 42

        # Range validation
        assert InputSanitizer.sanitize_integer(150, min_val=0, max_val=100) == 100
        assert InputSanitizer.sanitize_integer(-10, min_val=0, max_val=100) == 0

    def test_sanitize_float(self):
        """Test float sanitization"""
        # Valid floats
        assert InputSanitizer.sanitize_float("123.45") == 123.45
        assert InputSanitizer.sanitize_float(67.89) == 67.89

        # Invalid inputs with default
        assert InputSanitizer.sanitize_float("not-a-number", default=0.0) == 0.0
        assert InputSanitizer.sanitize_float(None, default=3.14) == 3.14

        # Range validation
        assert InputSanitizer.sanitize_float(150.5, min_val=0.0, max_val=100.0) == 100.0
        assert InputSanitizer.sanitize_float(-10.5, min_val=0.0, max_val=100.0) == 0.0

    def test_sanitize_vote_data(self):
        """Test vote data sanitization"""
        vote_data = {
            "session_slug": "test-vote-session",
            "option_id": "123",
            "rating": "-1",
            "comment": "This is my vote comment",
            "voter_id": "voter123",
        }

        result = InputSanitizer.sanitize_vote_data(vote_data)

        assert result["session_slug"] == "test-vote-session"
        assert result["option_id"] == 123
        assert result["rating"] == -1
        assert result["comment"] == "This is my vote comment"
        assert result["voter_id"] == "voter123"

        # Test invalid rating bounds
        vote_data["rating"] = "10"  # Outside bounds
        result = InputSanitizer.sanitize_vote_data(vote_data)
        assert result["rating"] == InputSanitizer.MAX_RATING

    def test_sanitize_form_data(self):
        """Test general form data sanitization"""
        form_data = {
            "email": "USER@EXAMPLE.COM",
            "username": "test_user",
            "password": "validpassword123",
            "first_name": "John",
            "last_name": "Doe",
            "website_url": "https://example.com",
            "profile_slug": "john-doe",
            "age": 25,
            "active": True,
            "tags": ["python", "security", "testing"],
            "nested": {"key": "value"},
        }

        result = InputSanitizer.sanitize_form_data(form_data)

        assert result["email"] == "USER@example.com"
        assert result["username"] == "test_user"
        assert result["password"] == "validpassword123"
        assert result["first_name"] == "John"
        assert result["website_url"] == "https://example.com"
        assert result["age"] == 25
        assert result["active"] is True
        assert isinstance(result["tags"], list)
        assert isinstance(result["nested"], dict)

    def test_dangerous_pattern_detection(self):
        """Test that dangerous patterns are properly detected and removed"""
        dangerous_inputs = [
            "<script>alert('xss')</script>Normal text",
            "Click <a href='javascript:alert(1)'>here</a>",
            "Load <iframe src='evil.com'></iframe>",
            "<object data='malware.swf'></object>",
            "onload='malicious()' onclick='bad()'",
        ]

        for dangerous in dangerous_inputs:
            result = InputSanitizer.sanitize_text(dangerous, allow_html=False)
            # Check that dangerous patterns are removed/neutralized
            assert not any(
                pattern.search(result.lower())
                for pattern in InputSanitizer.DANGEROUS_PATTERNS
            )

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Empty inputs
        assert InputSanitizer.sanitize_text("") == ""
        assert InputSanitizer.sanitize_text(None) == ""

        # Whitespace handling
        assert InputSanitizer.sanitize_text("  \t\n  ") == ""
        assert InputSanitizer.sanitize_text("  text  ") == "text"

        # Very long inputs
        very_long = "A" * 100000
        result = InputSanitizer.sanitize_text(very_long, max_length=1000)
        assert len(result) == 1000

        # Unicode edge cases
        unicode_text = "🚀 Test 中文 العربية"
        result = InputSanitizer.sanitize_text(unicode_text)
        assert "🚀" in result  # Emoji should be preserved
        assert "Test" in result
        assert "中文" in result
        assert "العربية" in result

    def test_performance_with_large_inputs(self):
        """Test performance with large inputs"""
        # This isn't a performance test per se, but ensures large inputs don't crash
        large_text = "A" * 50000
        result = InputSanitizer.sanitize_text(large_text)
        assert isinstance(result, str)

        # Large form data
        large_form = {f"field_{i}": f"value_{i}" * 100 for i in range(100)}
        result = InputSanitizer.sanitize_form_data(large_form)
        assert isinstance(result, dict)
        assert len(result) <= len(large_form)


class TestConvenienceFunctions:
    """Test the convenience functions"""

    def test_sanitize_user_input_function(self):
        """Test the standalone sanitize_user_input function"""
        from cardinal_vote.input_sanitizer import sanitize_user_input

        result = sanitize_user_input("Hello World")
        assert result == "Hello World"

        result = sanitize_user_input("<script>alert('xss')</script>")
        assert "<script>" not in result

    def test_sanitize_email_function(self):
        """Test the standalone sanitize_email function"""
        from cardinal_vote.input_sanitizer import sanitize_email

        result = sanitize_email("USER@EXAMPLE.COM")
        assert result == "USER@example.com"

        result = sanitize_email("invalid-email")
        assert result == ""

    def test_sanitize_form_function(self):
        """Test the standalone sanitize_form function"""
        from cardinal_vote.input_sanitizer import sanitize_form

        form_data = {"email": "USER@EXAMPLE.COM", "text": "Hello"}
        result = sanitize_form(form_data)

        assert result["email"] == "USER@example.com"
        assert result["text"] == "Hello"
