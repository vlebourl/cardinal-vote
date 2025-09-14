"""
Playwright tests for Email Verification Status UI.

Tests email verification status indicators, resend functionality,
and user interactions in the profile management modal.
"""

import asyncio
import os
from playwright.async_api import async_playwright, Page, expect
import pytest


class TestEmailVerificationStatusUI:
    """Test email verification status UI in user dashboard."""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up Playwright browser and page for each test."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()

        # Navigate to the landing page and simulate login
        await self.page.goto("http://localhost:8000")

        yield

        # Clean up
        await self.page.close()
        await self.browser.close()
        await self.playwright.stop()

    async def simulate_user_login(self, is_verified: bool = False):
        """Simulate user login by setting auth token and user data in localStorage."""
        # Simulate authentication by setting localStorage values
        user_data = {
            "id": "test-user-id",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_verified": is_verified,
            "is_super_admin": False,
            "created_at": "2025-01-01T00:00:00Z"
        }

        await self.page.evaluate(f"""
            localStorage.setItem('authToken', 'test-jwt-token');
            localStorage.setItem('userData', '{user_data}');
            window.currentUser = {user_data};
        """)

    async def open_profile_modal(self):
        """Helper method to open the profile management modal."""
        # Click user menu button
        user_menu_btn = self.page.locator('button[data-action="user-menu"]')
        await user_menu_btn.click()

        # Wait for menu to appear and click profile option
        profile_menu_item = self.page.locator('.md-menu-item[data-action="profile"]')
        await profile_menu_item.wait_for(state="visible")
        await profile_menu_item.click()

        # Wait for modal to be visible
        profile_modal = self.page.locator('#profileModalScrim[aria-hidden="false"]')
        await profile_modal.wait_for(state="visible")

    async def test_email_verification_status_verified_user(self):
        """Test email verification status display for verified users."""
        # Navigate to dashboard with verified user
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=True)

        # Refresh page to load user data
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        # Open profile modal
        await self.open_profile_modal()

        # Check verification status elements
        verification_status = self.page.locator('#emailVerificationStatus')
        await expect(verification_status).to_be_visible()

        # Check verified state
        verification_icon = self.page.locator('#verificationIcon')
        verification_text = self.page.locator('#verificationText')
        verification_details = self.page.locator('#verificationDetails')
        verification_actions = self.page.locator('#verificationActions')

        await expect(verification_icon).to_have_text('verified')
        await expect(verification_icon).to_have_class(re.compile('verified'))
        await expect(verification_text).to_have_text('Email verified')
        await expect(verification_details).to_contain_text('Your email address is verified and active')
        await expect(verification_actions).to_be_hidden()

    async def test_email_verification_status_unverified_user(self):
        """Test email verification status display for unverified users."""
        # Navigate to dashboard with unverified user
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)

        # Refresh page to load user data
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        # Open profile modal
        await self.open_profile_modal()

        # Check verification status elements
        verification_status = self.page.locator('#emailVerificationStatus')
        await expect(verification_status).to_be_visible()

        # Check unverified state
        verification_icon = self.page.locator('#verificationIcon')
        verification_text = self.page.locator('#verificationText')
        verification_details = self.page.locator('#verificationDetails')
        verification_actions = self.page.locator('#verificationActions')

        await expect(verification_icon).to_have_text('warning')
        await expect(verification_icon).to_have_class(re.compile('unverified'))
        await expect(verification_text).to_have_text('Email not verified')
        await expect(verification_details).to_contain_text('Please check your email for a verification link')
        await expect(verification_actions).to_be_visible()

    async def test_resend_verification_button_presence(self):
        """Test that resend verification button is present for unverified users."""
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        await self.open_profile_modal()

        # Check resend button
        resend_btn = self.page.locator('#resendVerificationBtn')
        await expect(resend_btn).to_be_visible()
        await expect(resend_btn).to_contain_text('Resend Verification Email')

        # Check button has proper structure for loading states
        btn_text = resend_btn.locator('.btn-text')
        btn_loading = resend_btn.locator('.btn-loading')
        await expect(btn_text).to_be_visible()
        await expect(btn_loading).to_be_hidden()

    async def test_resend_verification_button_click(self):
        """Test clicking the resend verification button."""
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        # Mock the API response for resend verification
        await self.page.route('**/api/auth/resend-verification', lambda route: route.fulfill(
            json={"success": True, "message": "Verification email sent"},
            status=200
        ))

        await self.open_profile_modal()

        # Click resend button
        resend_btn = self.page.locator('#resendVerificationBtn')
        await resend_btn.click()

        # Wait for loading state
        await self.page.wait_for_timeout(500)

        # Check that verification details are updated
        verification_details = self.page.locator('#verificationDetails')
        await expect(verification_details).to_contain_text('Verification email sent')

    async def test_email_verification_status_styling(self):
        """Test CSS styling of email verification status components."""
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        await self.open_profile_modal()

        # Check main container styling
        verification_status = self.page.locator('#emailVerificationStatus')
        await expect(verification_status).to_have_css('background-color', re.compile(r'.*'))
        await expect(verification_status).to_have_css('border-radius', '12px')
        await expect(verification_status).to_have_css('padding', '16px')

        # Check verification indicator styling
        verification_indicator = verification_status.locator('.verification-indicator')
        await expect(verification_indicator).to_have_css('display', 'flex')
        await expect(verification_indicator).to_have_css('align-items', 'center')

        # Check verification actions styling
        verification_actions = self.page.locator('#verificationActions')
        if await verification_actions.is_visible():
            await expect(verification_actions).to_have_css('display', 'flex')

    async def test_verification_status_accessibility(self):
        """Test accessibility features of verification status UI."""
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        await self.open_profile_modal()

        # Check ARIA attributes and accessibility
        resend_btn = self.page.locator('#resendVerificationBtn')
        await expect(resend_btn).to_have_attribute('type', 'button')

        # Check that text elements are properly structured for screen readers
        verification_text = self.page.locator('#verificationText')
        verification_details = self.page.locator('#verificationDetails')

        await expect(verification_text).to_be_visible()
        await expect(verification_details).to_be_visible()

    async def test_verification_status_responsive_design(self):
        """Test verification status UI responsive behavior."""
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        # Test desktop layout
        await self.page.set_viewport_size({"width": 1200, "height": 800})
        await self.open_profile_modal()

        verification_status = self.page.locator('#emailVerificationStatus')
        await expect(verification_status).to_be_visible()

        # Close modal for next test
        close_btn = self.page.locator('button[data-action="close-modal"][data-modal="profile"]')
        await close_btn.click()

        # Test tablet layout
        await self.page.set_viewport_size({"width": 768, "height": 1024})
        await self.open_profile_modal()
        await expect(verification_status).to_be_visible()

        # Close modal for next test
        await close_btn.click()

        # Test mobile layout
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.open_profile_modal()
        await expect(verification_status).to_be_visible()

    async def test_verification_status_error_handling(self):
        """Test error handling for resend verification functionality."""
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        # Mock API error response
        await self.page.route('**/api/auth/resend-verification', lambda route: route.fulfill(
            json={"success": False, "detail": "Failed to send verification email"},
            status=400
        ))

        await self.open_profile_modal()

        # Click resend button
        resend_btn = self.page.locator('#resendVerificationBtn')
        await resend_btn.click()

        # Wait for error handling
        await self.page.wait_for_timeout(1000)

        # Check for error message display
        error_element = self.page.locator('#profileInfoError')
        await expect(error_element).to_be_visible()

    async def test_verification_status_modal_interaction(self):
        """Test verification status behavior when modal is closed and reopened."""
        await self.page.goto("http://localhost:8000/dashboard")
        await self.simulate_user_login(is_verified=False)
        await self.page.reload()
        await self.page.wait_for_timeout(1000)

        # Open modal
        await self.open_profile_modal()

        # Verify elements are visible
        verification_status = self.page.locator('#emailVerificationStatus')
        await expect(verification_status).to_be_visible()

        # Close modal
        close_btn = self.page.locator('button[data-action="close-modal"][data-modal="profile"]')
        await close_btn.click()

        # Wait for modal to close
        profile_modal = self.page.locator('#profileModalScrim[aria-hidden="true"]')
        await profile_modal.wait_for(state="attached")

        # Reopen modal
        await self.open_profile_modal()

        # Verify elements are still functional
        await expect(verification_status).to_be_visible()
        resend_btn = self.page.locator('#resendVerificationBtn')
        await expect(resend_btn).to_be_visible()


async def run_email_verification_ui_tests():
    """Run all email verification UI tests."""
    test_instance = TestEmailVerificationStatusUI()

    print("🧪 Running Email Verification Status UI Tests...")

    tests = [
        ("Verified User Status", test_instance.test_email_verification_status_verified_user),
        ("Unverified User Status", test_instance.test_email_verification_status_unverified_user),
        ("Resend Button Presence", test_instance.test_resend_verification_button_presence),
        ("Resend Button Click", test_instance.test_resend_verification_button_click),
        ("Status Styling", test_instance.test_email_verification_status_styling),
        ("Accessibility Features", test_instance.test_verification_status_accessibility),
        ("Responsive Design", test_instance.test_verification_status_responsive_design),
        ("Error Handling", test_instance.test_verification_status_error_handling),
        ("Modal Interaction", test_instance.test_verification_status_modal_interaction),
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

    print(f"\n📊 Email Verification UI Test Results:")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {passed_tests/(passed_tests + failed_tests)*100:.1f}%")

    return failed_tests == 0


if __name__ == "__main__":
    success = asyncio.run(run_email_verification_ui_tests())
    exit(0 if success else 1)
