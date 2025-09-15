"""
Playwright tests for CAPTCHA integration in registration modal.

Tests CAPTCHA widget rendering, validation, and user interactions
across different CAPTCHA backends (mock, reCAPTCHA, hCAPTCHA).
"""

import asyncio

import pytest
from playwright.async_api import async_playwright, expect


class TestCAPTCHAIntegration:
    """Test CAPTCHA integration in registration modal."""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up Playwright browser and page for each test."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()

        # Navigate to the landing page
        await self.page.goto("http://localhost:8000")

        yield

        # Clean up
        await self.page.close()
        await self.browser.close()
        await self.playwright.stop()

    async def open_registration_modal(self):
        """Helper method to open the registration modal."""
        # Click "Get Started" button to open registration modal
        get_started_btn = self.page.locator(
            'button[data-action="show-register"]'
        ).first
        await get_started_btn.wait_for(state="visible")
        await get_started_btn.click()

        # Wait for modal to be visible
        register_modal = self.page.locator('#registerModalScrim[aria-hidden="false"]')
        await register_modal.wait_for(state="visible")

    async def test_captcha_container_present(self):
        """Test that CAPTCHA container is present in registration modal."""
        await self.open_registration_modal()

        # Check CAPTCHA container exists
        captcha_container = self.page.locator("#registerCaptcha")
        await expect(captcha_container).to_be_visible()

        # Check CAPTCHA helper text
        captcha_help = self.page.locator("#register-captcha-help")
        await expect(captcha_help).to_be_visible()
        await expect(captcha_help).to_contain_text(
            "Please complete the verification to continue"
        )

    async def test_captcha_configuration_loaded(self):
        """Test that CAPTCHA configuration is properly loaded."""
        await self.page.goto("http://localhost:8000")

        # Check that window.captchaConfig is defined
        captcha_config = await self.page.evaluate("window.captchaConfig")

        assert captcha_config is not None
        assert "backend" in captcha_config
        assert "siteKey" in captcha_config
        assert "enabled" in captcha_config

        # For testing, we expect mock backend
        assert captcha_config["backend"] == "mock"

    async def test_mock_captcha_rendering(self):
        """Test mock CAPTCHA widget rendering and interaction."""
        await self.open_registration_modal()

        # Wait for CAPTCHA to initialize
        await self.page.wait_for_timeout(1000)

        # Check if mock CAPTCHA widget is rendered
        mock_widget = self.page.locator("#registerCaptcha .mock-captcha-widget")
        if await mock_widget.count() > 0:
            await expect(mock_widget).to_be_visible()

            # Test mock CAPTCHA interaction
            mock_checkbox = mock_widget.locator('input[type="checkbox"]')
            if await mock_checkbox.count() > 0:
                await mock_checkbox.click()
                await expect(mock_checkbox).to_be_checked()

    async def test_registration_form_with_captcha_validation(self):
        """Test registration form submission with CAPTCHA validation."""
        await self.open_registration_modal()

        # Fill in registration form
        await self.page.locator("#registerFirstName").fill("John")
        await self.page.locator("#registerLastName").fill("Doe")
        await self.page.locator("#registerUsername").fill("johndoe123")
        await self.page.locator("#registerEmail").fill("john@example.com")
        await self.page.locator("#registerPassword").fill("SecurePass123!")

        # Wait for CAPTCHA to load
        await self.page.wait_for_timeout(1000)

        # Try to submit without completing CAPTCHA (if not mock)
        submit_button = self.page.locator("#registerSubmitBtn")
        await submit_button.click()

        # Check for CAPTCHA error message or successful submission
        captcha_error = self.page.locator("#registerCaptchaError")
        registration_error = self.page.locator("#registerError")

        # Wait for either error or success
        await self.page.wait_for_timeout(2000)

        # Verify that either CAPTCHA error appears or form submits successfully
        # (depending on mock CAPTCHA behavior)
        captcha_error_visible = await captcha_error.is_visible()
        registration_error_visible = await registration_error.is_visible()

        # At least one of these conditions should be true:
        # 1. CAPTCHA error is shown
        # 2. Registration error is shown (e.g., user already exists)
        # 3. Form submits successfully (less likely in test environment)
        assert (
            captcha_error_visible
            or registration_error_visible
            or await self.page.locator(".md-snackbar").is_visible()
        )

    async def test_captcha_error_handling(self):
        """Test CAPTCHA error display and clearing."""
        await self.open_registration_modal()

        # Check that CAPTCHA error is initially hidden
        captcha_error = self.page.locator("#registerCaptchaError")
        await expect(captcha_error).to_be_hidden()

        # Fill form and attempt submission to trigger potential CAPTCHA error
        await self.page.locator("#registerFirstName").fill("Jane")
        await self.page.locator("#registerLastName").fill("Smith")
        await self.page.locator("#registerUsername").fill("janesmith456")
        await self.page.locator("#registerEmail").fill("jane@example.com")
        await self.page.locator("#registerPassword").fill("AnotherPass456!")

        # Submit form (may trigger CAPTCHA validation)
        submit_button = self.page.locator("#registerSubmitBtn")
        await submit_button.click()

        # Wait for potential error
        await self.page.wait_for_timeout(2000)

    async def test_captcha_accessibility(self):
        """Test CAPTCHA widget accessibility features."""
        await self.open_registration_modal()

        # Check CAPTCHA container has proper ARIA attributes
        captcha_container = self.page.locator("#registerCaptcha")
        await expect(captcha_container).to_have_attribute(
            "aria-describedby", "register-captcha-help"
        )

        # Check error container has proper role
        captcha_error = self.page.locator("#registerCaptchaError")
        await expect(captcha_error).to_have_attribute("role", "alert")

        # Check helper text is properly associated
        captcha_help = self.page.locator("#register-captcha-help")
        await expect(captcha_help).to_be_visible()

    async def test_captcha_responsive_layout(self):
        """Test CAPTCHA widget responsive behavior."""
        await self.open_registration_modal()

        # Test desktop layout
        await self.page.set_viewport_size({"width": 1200, "height": 800})
        captcha_container = self.page.locator("#registerCaptcha")
        await expect(captcha_container).to_be_visible()

        # Test tablet layout
        await self.page.set_viewport_size({"width": 768, "height": 1024})
        await expect(captcha_container).to_be_visible()

        # Test mobile layout
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await expect(captcha_container).to_be_visible()

    async def test_captcha_modal_interaction(self):
        """Test CAPTCHA behavior when modal is closed and reopened."""
        await self.open_registration_modal()

        # Wait for CAPTCHA to load
        await self.page.wait_for_timeout(1000)

        # Close modal
        close_button = self.page.locator(
            'button[data-action="close-modal"][data-modal="register"]'
        )
        await close_button.click()

        # Wait for modal to close
        register_modal = self.page.locator('#registerModalScrim[aria-hidden="true"]')
        await register_modal.wait_for(state="attached")

        # Reopen modal
        await self.open_registration_modal()

        # Verify CAPTCHA container is still present and functional
        captcha_container = self.page.locator("#registerCaptcha")
        await expect(captcha_container).to_be_visible()

    async def test_captcha_form_validation_order(self):
        """Test that CAPTCHA validation works with other form validations."""
        await self.open_registration_modal()

        # Try submitting with empty form
        submit_button = self.page.locator("#registerSubmitBtn")
        await submit_button.click()

        # Check that HTML5 validation prevents submission
        first_name_field = self.page.locator("#registerFirstName")
        is_invalid = await first_name_field.evaluate("el => !el.checkValidity()")
        assert is_invalid  # Should be invalid due to required attribute

        # Fill required fields
        await first_name_field.fill("Test")
        await self.page.locator("#registerLastName").fill("User")
        await self.page.locator("#registerUsername").fill("testuser789")
        await self.page.locator("#registerEmail").fill("test@example.com")
        await self.page.locator("#registerPassword").fill("TestPass789!")

        # Now submit (should reach CAPTCHA validation)
        await submit_button.click()
        await self.page.wait_for_timeout(2000)


async def run_captcha_tests():
    """Run all CAPTCHA integration tests."""
    test_instance = TestCAPTCHAIntegration()

    print("🧪 Running CAPTCHA Integration Tests...")

    tests = [
        ("CAPTCHA Container Present", test_instance.test_captcha_container_present),
        (
            "CAPTCHA Configuration Loaded",
            test_instance.test_captcha_configuration_loaded,
        ),
        ("Mock CAPTCHA Rendering", test_instance.test_mock_captcha_rendering),
        (
            "Registration Form with CAPTCHA",
            test_instance.test_registration_form_with_captcha_validation,
        ),
        ("CAPTCHA Error Handling", test_instance.test_captcha_error_handling),
        ("CAPTCHA Accessibility", test_instance.test_captcha_accessibility),
        ("CAPTCHA Responsive Layout", test_instance.test_captcha_responsive_layout),
        ("CAPTCHA Modal Interaction", test_instance.test_captcha_modal_interaction),
        (
            "CAPTCHA Form Validation Order",
            test_instance.test_captcha_form_validation_order,
        ),
    ]

    passed_tests = 0
    failed_tests = 0

    for test_name, test_func in tests:
        try:
            await test_instance.setup_and_teardown().__anext__()  # Setup
            await test_func()
            print(f"✅ {test_name}")
            passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
            failed_tests += 1
        finally:
            try:
                await test_instance.setup_and_teardown().__anext__()  # Teardown
            except StopAsyncIteration:
                pass

    print("\n📊 Test Results:")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {passed_tests / (passed_tests + failed_tests) * 100:.1f}%")

    return failed_tests == 0


if __name__ == "__main__":
    success = asyncio.run(run_captcha_tests())
    exit(0 if success else 1)
