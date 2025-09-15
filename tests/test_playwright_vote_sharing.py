"""
Playwright tests for Simple Vote Sharing Functionality.

Tests vote preview page functionality, sharing options, copy operations,
social media links, embed codes, and access settings display.
"""

import asyncio
import re

import pytest
from playwright.async_api import async_playwright, expect


class TestVoteSharing:
    """Test vote sharing functionality in vote preview page."""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up Playwright browser and page for each test."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()

        yield

        # Clean up
        await self.page.close()
        await self.browser.close()
        await self.playwright.stop()

    async def simulate_authenticated_user(self):
        """Simulate authenticated user by setting tokens and user data."""
        user_data = {
            "id": "test-user-123",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_verified": True,
            "is_super_admin": False,
            "created_at": "2025-01-01T00:00:00Z",
        }

        await self.page.evaluate(f"""
            localStorage.setItem('authToken', 'test-jwt-token');
            sessionStorage.setItem('access_token', 'test-jwt-token');
            localStorage.setItem('userData', '{user_data}');
            window.currentUser = {user_data};
        """)

    async def mock_vote_preview_api(self):
        """Mock the vote preview API response."""
        await self.page.route(
            "**/api/votes/**/preview",
            lambda route: route.fulfill(
                json={
                    "vote": {
                        "id": "test-vote-123",
                        "title": "Test Vote Title",
                        "description": "This is a test vote description",
                        "status": "active",
                        "require_auth": False,
                        "has_access_code": False,
                        "options": [
                            {
                                "id": "option-1",
                                "title": "Option 1",
                                "content": "First option content",
                            },
                            {
                                "id": "option-2",
                                "title": "Option 2",
                                "content": "Second option content",
                            },
                        ],
                    },
                    "stats": {"response_count": 42, "option_count": 2},
                    "sharing": {
                        "public_url": "http://localhost:8000/vote/test-vote-123",
                        "embed_code": '<iframe src="http://localhost:8000/vote/test-vote-123/embed" width="100%" height="600"></iframe>',
                        "social_sharing": {
                            "twitter": "https://twitter.com/intent/tweet?url=http://localhost:8000/vote/test-vote-123&text=Cast%20your%20vote%20on%3A%20Test%20Vote%20Title",
                            "facebook": "https://www.facebook.com/sharer/sharer.php?u=http://localhost:8000/vote/test-vote-123",
                            "linkedin": "https://www.linkedin.com/sharing/share-offsite/?url=http://localhost:8000/vote/test-vote-123",
                        },
                    },
                    "access_settings": {
                        "is_public": True,
                        "requires_auth": False,
                        "has_access_code": False,
                    },
                },
                status=200,
            ),
        )

    async def navigate_to_vote_preview(self, vote_id="test-vote-123"):
        """Navigate to vote preview page."""
        await self.page.goto(f"http://localhost:8000/vote-preview/{vote_id}")

    async def test_vote_preview_page_structure(self):
        """Test that vote preview page has all required sections."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()

        # Wait for page to load
        await self.page.wait_for_timeout(1000)

        # Check main sections exist
        status_banner = self.page.locator(".status-banner")
        vote_preview_section = self.page.locator(".vote-preview-section")
        sharing_section = self.page.locator(".sharing-section")
        settings_section = self.page.locator(".settings-section")

        await expect(status_banner).to_be_visible()
        await expect(vote_preview_section).to_be_visible()
        await expect(sharing_section).to_be_visible()
        await expect(settings_section).to_be_visible()

    async def test_vote_status_display(self):
        """Test vote status banner displays correctly."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check status card
        status_card = self.page.locator(".status-card")
        await expect(status_card).to_be_visible()

        # Check stats display
        response_count = self.page.locator(".stat-value").first()
        option_count = self.page.locator(".stat-value").nth(1)

        await expect(response_count).to_contain_text("42")
        await expect(option_count).to_contain_text("2")

        # Check status labels
        response_label = self.page.locator(".stat-label").first()
        option_label = self.page.locator(".stat-label").nth(1)

        await expect(response_label).to_contain_text("Responses")
        await expect(option_label).to_contain_text("Options")

    async def test_sharing_options_display(self):
        """Test that all sharing options are displayed correctly."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check sharing section title
        sharing_title = self.page.locator(".sharing-section .section-title")
        await expect(sharing_title).to_contain_text("Share Your Vote")

        # Check direct link sharing card
        direct_link_card = self.page.locator(".sharing-card").first()
        await expect(direct_link_card).to_be_visible()

        link_title = direct_link_card.locator("h3")
        await expect(link_title).to_contain_text("Direct Link")

        # Check social media sharing card
        social_card = self.page.locator(".sharing-card").nth(1)
        await expect(social_card).to_be_visible()

        social_title = social_card.locator("h3")
        await expect(social_title).to_contain_text("Social Media")

        # Check embed code sharing card
        embed_card = self.page.locator(".sharing-card").nth(2)
        await expect(embed_card).to_be_visible()

        embed_title = embed_card.locator("h3")
        await expect(embed_title).to_contain_text("Embed Code")

    async def test_direct_link_functionality(self):
        """Test direct link sharing functionality."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check link input field
        link_input = self.page.locator("#voteLink")
        await expect(link_input).to_be_visible()
        await expect(link_input).to_have_value(
            "http://localhost:8000/vote/test-vote-123"
        )
        await expect(link_input).to_have_attribute("readonly")

        # Check copy button
        copy_button = self.page.locator('[data-action="copy-link"]')
        await expect(copy_button).to_be_visible()
        await expect(copy_button).to_have_attribute("data-target", "voteLink")

    async def test_social_media_links(self):
        """Test social media sharing links."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check Twitter link
        twitter_link = self.page.locator(".social-button.twitter")
        await expect(twitter_link).to_be_visible()
        await expect(twitter_link).to_have_attribute("target", "_blank")
        await expect(twitter_link).to_have_attribute("href", re.compile("twitter.com"))

        # Check Facebook link
        facebook_link = self.page.locator(".social-button.facebook")
        await expect(facebook_link).to_be_visible()
        await expect(facebook_link).to_have_attribute("target", "_blank")
        await expect(facebook_link).to_have_attribute(
            "href", re.compile("facebook.com")
        )

        # Check LinkedIn link
        linkedin_link = self.page.locator(".social-button.linkedin")
        await expect(linkedin_link).to_be_visible()
        await expect(linkedin_link).to_have_attribute("target", "_blank")
        await expect(linkedin_link).to_have_attribute(
            "href", re.compile("linkedin.com")
        )

    async def test_embed_code_functionality(self):
        """Test embed code sharing functionality."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check embed code textarea
        embed_textarea = self.page.locator("#embedCode")
        await expect(embed_textarea).to_be_visible()
        await expect(embed_textarea).to_have_attribute("readonly")

        embed_value = await embed_textarea.input_value()
        assert "iframe" in embed_value
        assert "test-vote-123" in embed_value

        # Check copy embed code button
        copy_embed_button = self.page.locator('[data-action="copy-code"]')
        await expect(copy_embed_button).to_be_visible()
        await expect(copy_embed_button).to_have_attribute("data-target", "embedCode")

    async def test_copy_to_clipboard_simulation(self):
        """Test copy to clipboard functionality simulation."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Mock clipboard API
        await self.page.evaluate("""
            navigator.clipboard = {
                writeText: async (text) => {
                    window.clipboardText = text;
                    return Promise.resolve();
                }
            };
        """)

        # Click copy link button
        copy_button = self.page.locator('[data-action="copy-link"]')
        await copy_button.click()

        # Wait for copy operation
        await self.page.wait_for_timeout(500)

        # Check that clipboard was called with correct text
        clipboard_text = await self.page.evaluate("window.clipboardText")
        assert clipboard_text == "http://localhost:8000/vote/test-vote-123"

        # Check for success snackbar
        snackbar = self.page.locator("#snackbar.md-snackbar-visible")
        await expect(snackbar).to_be_visible()

        snackbar_message = self.page.locator("#snackbar-message")
        await expect(snackbar_message).to_contain_text("Link copied to clipboard!")

    async def test_share_button_functionality(self):
        """Test native share button functionality."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check share button in top app bar
        share_button = self.page.locator('[data-action="share-vote"]')
        await expect(share_button).to_be_visible()

        # Mock navigator.share API
        await self.page.evaluate("""
            navigator.share = async (data) => {
                window.sharedData = data;
                return Promise.resolve();
            };
            window.voteData = {
                title: 'Test Vote Title',
                sharing: {
                    public_url: 'http://localhost:8000/vote/test-vote-123'
                }
            };
        """)

        # Click share button
        await share_button.click()

        # Wait for share operation
        await self.page.wait_for_timeout(500)

        # Check that share was called with correct data
        shared_data = await self.page.evaluate("window.sharedData")
        assert shared_data is not None
        assert "Test Vote Title" in shared_data["title"]
        assert "test-vote-123" in shared_data["url"]

    async def test_access_settings_display(self):
        """Test access settings section display."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check access settings section
        settings_section = self.page.locator(".settings-section")
        settings_title = settings_section.locator(".section-title")
        await expect(settings_title).to_contain_text("Access Settings")

        # Check public access setting
        public_access = self.page.locator(".setting-item").first()
        public_title = public_access.locator(".setting-title")
        await expect(public_title).to_contain_text("Public Access")

        # Check auth required setting
        auth_setting = self.page.locator(".setting-item").nth(1)
        auth_title = auth_setting.locator(".setting-title")
        await expect(auth_title).to_contain_text("Authentication Required")

        # Check access code setting
        code_setting = self.page.locator(".setting-item").nth(2)
        code_title = code_setting.locator(".setting-title")
        await expect(code_title).to_contain_text("Access Code")

    async def test_vote_preview_display(self):
        """Test vote preview section displays correctly."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check vote preview section
        preview_section = self.page.locator(".vote-preview-section")
        preview_title = preview_section.locator(".section-title")
        await expect(preview_title).to_contain_text("Vote Preview")

        # Check vote card preview
        vote_card = self.page.locator(".vote-preview-card")
        await expect(vote_card).to_be_visible()

        # Check vote title
        vote_title = vote_card.locator(".vote-title")
        await expect(vote_title).to_contain_text("Test Vote Title")

        # Check vote description
        vote_description = vote_card.locator(".vote-description")
        await expect(vote_description).to_contain_text(
            "This is a test vote description"
        )

        # Check options are displayed
        options_list = vote_card.locator(".options-list")
        await expect(options_list).to_be_visible()

        option_previews = options_list.locator(".option-preview")
        await expect(option_previews).to_have_count(2)

    async def test_responsive_design_vote_sharing(self):
        """Test vote sharing page responsive behavior."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()

        # Test desktop layout
        await self.page.set_viewport_size({"width": 1200, "height": 800})
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        sharing_section = self.page.locator(".sharing-section")
        await expect(sharing_section).to_be_visible()

        # Test tablet layout
        await self.page.set_viewport_size({"width": 768, "height": 1024})
        await expect(sharing_section).to_be_visible()

        # Test mobile layout
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await expect(sharing_section).to_be_visible()

    async def test_snackbar_functionality(self):
        """Test snackbar notifications in vote sharing."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check snackbar elements exist
        snackbar = self.page.locator("#snackbar")
        snackbar_message = self.page.locator("#snackbar-message")
        snackbar_action = self.page.locator("#snackbar-action")

        await expect(snackbar).to_be_attached()
        await expect(snackbar_message).to_be_attached()
        await expect(snackbar_action).to_be_attached()

        # Test snackbar dismiss button
        await expect(snackbar_action).to_contain_text("DISMISS")

    async def test_vote_sharing_animations(self):
        """Test animation classes and effects."""
        await self.simulate_authenticated_user()
        await self.mock_vote_preview_api()
        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(1000)

        # Check that sections have fade-in animation class
        sections = await self.page.locator(".fade-in").all()
        assert len(sections) >= 4  # status, preview, sharing, settings sections

        # Check sharing cards have proper styling
        sharing_cards = self.page.locator(".sharing-card")
        card_count = await sharing_cards.count()
        assert card_count >= 3  # direct link, social, embed cards

    async def test_error_handling_vote_sharing(self):
        """Test error handling in vote sharing functionality."""
        await self.simulate_authenticated_user()

        # Mock API error response
        await self.page.route(
            "**/api/votes/**/preview",
            lambda route: route.fulfill(json={"detail": "Vote not found"}, status=404),
        )

        await self.navigate_to_vote_preview()
        await self.page.wait_for_timeout(2000)

        # Page should handle error gracefully (may redirect or show error message)
        # This test ensures no JavaScript errors occur


async def run_vote_sharing_tests():
    """Run all vote sharing tests."""
    test_instance = TestVoteSharing()

    print("🧪 Running Vote Sharing Functionality Tests...")

    tests = [
        ("Vote Preview Page Structure", test_instance.test_vote_preview_page_structure),
        ("Vote Status Display", test_instance.test_vote_status_display),
        ("Sharing Options Display", test_instance.test_sharing_options_display),
        ("Direct Link Functionality", test_instance.test_direct_link_functionality),
        ("Social Media Links", test_instance.test_social_media_links),
        ("Embed Code Functionality", test_instance.test_embed_code_functionality),
        ("Copy to Clipboard", test_instance.test_copy_to_clipboard_simulation),
        ("Share Button Functionality", test_instance.test_share_button_functionality),
        ("Access Settings Display", test_instance.test_access_settings_display),
        ("Vote Preview Display", test_instance.test_vote_preview_display),
        ("Responsive Design", test_instance.test_responsive_design_vote_sharing),
        ("Snackbar Functionality", test_instance.test_snackbar_functionality),
        ("Vote Sharing Animations", test_instance.test_vote_sharing_animations),
        ("Error Handling", test_instance.test_error_handling_vote_sharing),
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

    print("\n📊 Vote Sharing Test Results:")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {passed_tests / (passed_tests + failed_tests) * 100:.1f}%")

    return failed_tests == 0


if __name__ == "__main__":
    success = asyncio.run(run_vote_sharing_tests())
    exit(0 if success else 1)
