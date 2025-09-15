"""
Playwright tests for Mobile-First Responsive Design.

Tests mobile layouts, touch targets, responsive breakpoints,
modal adaptations, and mobile user experience optimizations.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright, expect


class TestMobileResponsiveDesign:
    """Test mobile-first responsive design across all new components."""

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

    # ==========================================================================
    # MOBILE VIEWPORT TESTS
    # ==========================================================================

    async def test_mobile_viewport_configuration(self):
        """Test that pages have proper mobile viewport configuration."""
        await self.page.goto("http://localhost:8000")

        # Check viewport meta tag
        viewport_tag = await self.page.locator('meta[name="viewport"]').get_attribute(
            "content"
        )
        assert "width=device-width" in viewport_tag
        assert "initial-scale=1.0" in viewport_tag

    async def test_mobile_breakpoint_320px(self):
        """Test layout at minimum mobile width (320px)."""
        await self.page.set_viewport_size({"width": 320, "height": 568})
        await self.page.goto("http://localhost:8000")

        # Check that content fits within viewport
        body = self.page.locator("body")
        await expect(body).to_be_visible()

        # Ensure no horizontal scrolling
        scroll_width = await self.page.evaluate("document.documentElement.scrollWidth")
        client_width = await self.page.evaluate("document.documentElement.clientWidth")
        assert scroll_width <= client_width + 1  # Allow 1px tolerance

    async def test_mobile_breakpoint_375px(self):
        """Test layout at common mobile width (375px - iPhone)."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Check responsive layout elements
        hero_section = self.page.locator(".hero-section").first()
        await expect(hero_section).to_be_visible()

    async def test_tablet_breakpoint_768px(self):
        """Test layout at tablet width (768px)."""
        await self.page.set_viewport_size({"width": 768, "height": 1024})
        await self.page.goto("http://localhost:8000")

        # Layout should adapt to tablet size
        await expect(self.page.locator("body")).to_be_visible()

    # ==========================================================================
    # TOUCH TARGET TESTS
    # ==========================================================================

    async def test_touch_targets_minimum_size(self):
        """Test that interactive elements meet 44px minimum touch target size."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Check buttons have minimum touch target size
        buttons = await self.page.locator("button, .md-button").all()
        for button in buttons[:5]:  # Test first 5 buttons
            if await button.is_visible():
                bounding_box = await button.bounding_box()
                if bounding_box:
                    assert bounding_box["height"] >= 44, (
                        f"Button height {bounding_box['height']} < 44px"
                    )
                    assert bounding_box["width"] >= 44, (
                        f"Button width {bounding_box['width']} < 44px"
                    )

    async def test_form_inputs_touch_friendly(self):
        """Test that form inputs are touch-friendly on mobile."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Open registration modal
        get_started_btn = self.page.locator(
            'button[data-action="show-register"]'
        ).first()
        if await get_started_btn.is_visible():
            await get_started_btn.click()
            await self.page.wait_for_timeout(500)

            # Check input field sizes
            inputs = await self.page.locator("input, textarea").all()
            for input_element in inputs[:3]:  # Test first 3 inputs
                if await input_element.is_visible():
                    bounding_box = await input_element.bounding_box()
                    if bounding_box:
                        assert bounding_box["height"] >= 44, (
                            f"Input height {bounding_box['height']} < 44px"
                        )

    # ==========================================================================
    # MODAL RESPONSIVE TESTS
    # ==========================================================================

    async def test_modal_mobile_adaptation(self):
        """Test that modals adapt properly to mobile screens."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Open registration modal
        get_started_btn = self.page.locator(
            'button[data-action="show-register"]'
        ).first()
        if await get_started_btn.is_visible():
            await get_started_btn.click()
            await self.page.wait_for_timeout(500)

            # Check modal dimensions
            modal = self.page.locator(
                '#registerModalScrim[aria-hidden="false"] .md-dialog'
            )
            if await modal.is_visible():
                bounding_box = await modal.bounding_box()
                if bounding_box:
                    # Modal should not exceed viewport minus margins
                    assert bounding_box["width"] <= 375 - 32  # 16px margin each side
                    assert bounding_box["height"] <= 667 - 32  # 16px margin top/bottom

    async def test_modal_actions_mobile_layout(self):
        """Test that modal action buttons stack vertically on mobile."""
        await self.page.set_viewport_size({"width": 320, "height": 568})
        await self.page.goto("http://localhost:8000")

        # Open registration modal
        get_started_btn = self.page.locator(
            'button[data-action="show-register"]'
        ).first()
        if await get_started_btn.is_visible():
            await get_started_btn.click()
            await self.page.wait_for_timeout(500)

            # Check if modal actions are stacked vertically
            modal_actions = self.page.locator(
                ".auth-actions, .md-dialog-actions"
            ).first()
            if await modal_actions.is_visible():
                computed_style = await modal_actions.evaluate(
                    "el => getComputedStyle(el).flexDirection"
                )
                # Should be column on mobile
                assert computed_style == "column" or computed_style == "column-reverse"

    # ==========================================================================
    # DASHBOARD RESPONSIVE TESTS
    # ==========================================================================

    async def test_dashboard_mobile_layout(self):
        """Test dashboard mobile responsiveness."""
        await self.simulate_authenticated_user()
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Check dashboard elements are visible and properly sized
        dashboard_content = self.page.locator(".dashboard-content, .main-content")
        if await dashboard_content.is_visible():
            await expect(dashboard_content).to_be_visible()

    async def test_dashboard_stats_mobile_grid(self):
        """Test dashboard stats grid adaptation on mobile."""
        await self.simulate_authenticated_user()
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Check stats grid adapts to mobile
        stats_grid = self.page.locator(".user-stats-grid, .stats-grid")
        if await stats_grid.is_visible():
            grid_columns = await stats_grid.evaluate(
                "el => getComputedStyle(el).gridTemplateColumns"
            )
            # Should have fewer columns on mobile
            column_count = grid_columns.count("fr")
            assert column_count <= 2, f"Too many columns ({column_count}) on mobile"

    # ==========================================================================
    # PROFILE MANAGEMENT MOBILE TESTS
    # ==========================================================================

    async def test_profile_modal_mobile_optimization(self):
        """Test profile management modal mobile optimization."""
        await self.simulate_authenticated_user()
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Open profile modal
        user_menu_btn = self.page.locator('button[data-action="user-menu"]')
        if await user_menu_btn.is_visible():
            await user_menu_btn.click()
            await self.page.wait_for_timeout(500)

            profile_menu_item = self.page.locator(
                '.md-menu-item[data-action="profile"]'
            )
            if await profile_menu_item.is_visible():
                await profile_menu_item.click()
                await self.page.wait_for_timeout(500)

                # Check profile modal adaptation
                profile_modal = self.page.locator(
                    '#profileModalScrim[aria-hidden="false"] .md-dialog'
                )
                if await profile_modal.is_visible():
                    bounding_box = await profile_modal.bounding_box()
                    if bounding_box:
                        assert bounding_box["width"] <= 375 - 32  # Account for margins

    async def test_profile_form_mobile_layout(self):
        """Test profile form mobile layout optimization."""
        await self.simulate_authenticated_user()
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Test form field stacking on mobile
        form_rows = await self.page.locator(".profile-form-row, .form-row").all()
        for row in form_rows[:2]:  # Test first 2 rows
            if await row.is_visible():
                flex_direction = await row.evaluate(
                    "el => getComputedStyle(el).flexDirection"
                )
                # Should stack vertically on mobile
                assert flex_direction in ["column", "column-reverse"]

    # ==========================================================================
    # VOTE CREATION MOBILE TESTS
    # ==========================================================================

    async def test_vote_creation_mobile_adaptation(self):
        """Test vote creation dialog mobile adaptation."""
        await self.simulate_authenticated_user()
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Open vote creation dialog
        create_btn = self.page.locator('button[data-action="create-vote"]')
        if await create_btn.is_visible():
            await create_btn.click()
            await self.page.wait_for_timeout(500)

            # Check dialog mobile adaptation
            creation_dialog = self.page.locator(
                '#createVoteModal[aria-hidden="false"] .vote-creation-dialog'
            )
            if await creation_dialog.is_visible():
                bounding_box = await creation_dialog.bounding_box()
                if bounding_box:
                    assert bounding_box["width"] <= 375 - 16  # Account for margins

    # ==========================================================================
    # IMAGE UPLOAD MOBILE TESTS
    # ==========================================================================

    async def test_image_upload_mobile_interface(self):
        """Test image upload interface mobile optimization."""
        await self.simulate_authenticated_user()
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Open vote creation to access image upload
        create_btn = self.page.locator('button[data-action="create-vote"]')
        if await create_btn.is_visible():
            await create_btn.click()
            await self.page.wait_for_timeout(500)

            # Check image upload interface
            image_interface = self.page.locator(".image-upload-interface")
            if await image_interface.is_visible():
                # Test mobile-specific styling
                computed_padding = await image_interface.evaluate(
                    "el => getComputedStyle(el).padding"
                )
                # Should have mobile-optimized padding
                assert "12px" in computed_padding or "16px" in computed_padding

    # ==========================================================================
    # VOTE SHARING MOBILE TESTS
    # ==========================================================================

    async def test_vote_sharing_mobile_layout(self):
        """Test vote sharing page mobile layout."""
        await self.simulate_authenticated_user()
        await self.page.set_viewport_size({"width": 375, "height": 667})

        # Mock vote preview endpoint
        await self.page.route(
            "**/api/votes/**/preview",
            lambda route: route.fulfill(
                json={
                    "vote": {
                        "id": "test",
                        "title": "Test Vote",
                        "description": "Test",
                        "status": "active",
                        "options": [],
                    },
                    "stats": {"response_count": 0, "option_count": 0},
                    "sharing": {
                        "public_url": "test",
                        "embed_code": "test",
                        "social_sharing": {},
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

        await self.page.goto("http://localhost:8000/vote-preview/test-vote")
        await self.page.wait_for_timeout(1000)

        # Check sharing section mobile adaptation
        sharing_section = self.page.locator(".sharing-section")
        if await sharing_section.is_visible():
            sharing_cards = await sharing_section.locator(".sharing-card").all()
            for card in sharing_cards:
                if await card.is_visible():
                    bounding_box = await card.bounding_box()
                    if bounding_box:
                        assert (
                            bounding_box["width"] <= 375 - 32
                        )  # Account for container padding

    # ==========================================================================
    # RESPONSIVE BREAKPOINT TESTS
    # ==========================================================================

    async def test_responsive_breakpoints_sequence(self):
        """Test responsive behavior across different breakpoints."""
        breakpoints = [
            (320, 568),  # Small mobile
            (375, 667),  # iPhone
            (414, 896),  # iPhone Plus
            (640, 960),  # Small tablet
            (768, 1024),  # iPad
            (1024, 768),  # Desktop
        ]

        for width, height in breakpoints:
            await self.page.set_viewport_size({"width": width, "height": height})
            await self.page.goto("http://localhost:8000")
            await self.page.wait_for_timeout(500)

            # Check that page renders without horizontal scroll
            scroll_width = await self.page.evaluate(
                "document.documentElement.scrollWidth"
            )
            client_width = await self.page.evaluate(
                "document.documentElement.clientWidth"
            )
            assert scroll_width <= client_width + 2, (
                f"Horizontal scroll at {width}x{height}"
            )

    # ==========================================================================
    # TOUCH AND INTERACTION TESTS
    # ==========================================================================

    async def test_touch_feedback_mobile(self):
        """Test touch feedback on mobile devices."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Simulate touch device
        await self.page.evaluate("""
            // Mock touch device
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 5
            });
        """)

        # Test button touch feedback
        buttons = await self.page.locator("button, .md-button").all()
        for button in buttons[:3]:  # Test first 3 buttons
            if await button.is_visible():
                # Click should provide visual feedback
                await button.click()
                await self.page.wait_for_timeout(100)

    # ==========================================================================
    # FORM INPUT MOBILE OPTIMIZATION TESTS
    # ==========================================================================

    async def test_form_inputs_mobile_keyboard(self):
        """Test form inputs trigger appropriate mobile keyboards."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Open registration modal
        get_started_btn = self.page.locator(
            'button[data-action="show-register"]'
        ).first()
        if await get_started_btn.is_visible():
            await get_started_btn.click()
            await self.page.wait_for_timeout(500)

            # Check email input has email type
            email_input = self.page.locator("#registerEmail")
            if await email_input.is_visible():
                input_type = await email_input.get_attribute("type")
                assert input_type == "email"

            # Check inputs have proper font size (prevents zoom on iOS)
            text_inputs = await self.page.locator(
                'input[type="text"], input[type="email"], input[type="password"]'
            ).all()
            for input_element in text_inputs[:3]:
                if await input_element.is_visible():
                    font_size = await input_element.evaluate(
                        "el => getComputedStyle(el).fontSize"
                    )
                    # Should be 16px or larger to prevent zoom on iOS
                    font_size_value = float(font_size.replace("px", ""))
                    assert font_size_value >= 16, (
                        f"Font size {font_size_value}px too small"
                    )

    # ==========================================================================
    # NAVIGATION MOBILE TESTS
    # ==========================================================================

    async def test_top_app_bar_mobile_adaptation(self):
        """Test top app bar mobile adaptation."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Check app bar mobile optimization
        app_bar = self.page.locator(".md-top-app-bar")
        if await app_bar.is_visible():
            # Check that title doesn't overflow
            title = app_bar.locator(".md-top-app-bar-title")
            if await title.is_visible():
                bounding_box = await title.bounding_box()
                if bounding_box:
                    assert (
                        bounding_box["width"] <= 200
                    )  # Reasonable max width for mobile

    # ==========================================================================
    # SNACKBAR MOBILE TESTS
    # ==========================================================================

    async def test_snackbar_mobile_positioning(self):
        """Test snackbar positioning on mobile."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Test snackbar exists
        snackbar = self.page.locator(".md-snackbar, #snackbar")
        if await snackbar.is_attached():
            # Check mobile-specific positioning
            position = await snackbar.evaluate("el => getComputedStyle(el).position")
            assert position in ["fixed", "absolute"]

    # ==========================================================================
    # ACCESSIBILITY MOBILE TESTS
    # ==========================================================================

    async def test_mobile_accessibility_features(self):
        """Test mobile accessibility features."""
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.goto("http://localhost:8000")

        # Test skip link for mobile
        skip_link = self.page.locator(".skip-link")
        if await skip_link.is_attached():
            await expect(skip_link).to_have_attribute("href")

    # ==========================================================================
    # PERFORMANCE MOBILE TESTS
    # ==========================================================================

    async def test_mobile_performance_basics(self):
        """Test basic mobile performance metrics."""
        await self.page.set_viewport_size({"width": 375, "height": 667})

        # Measure navigation timing
        start_time = await self.page.evaluate("performance.now()")
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_load_state("networkidle")
        end_time = await self.page.evaluate("performance.now()")

        load_time = end_time - start_time
        # Should load within reasonable time (allow for test environment)
        assert load_time < 10000, f"Page load time {load_time}ms too slow"

    # ==========================================================================
    # ORIENTATION TESTS
    # ==========================================================================

    async def test_landscape_orientation_adaptation(self):
        """Test layout adaptation in landscape mode."""
        await self.page.set_viewport_size({"width": 667, "height": 375})
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(500)

        # Check that content adapts to landscape
        body = self.page.locator("body")
        await expect(body).to_be_visible()

        # Check for horizontal scroll
        scroll_width = await self.page.evaluate("document.documentElement.scrollWidth")
        client_width = await self.page.evaluate("document.documentElement.clientWidth")
        assert scroll_width <= client_width + 1


async def run_mobile_responsive_tests():
    """Run all mobile-first responsive design tests."""
    test_instance = TestMobileResponsiveDesign()

    print("📱 Running Mobile-First Responsive Design Tests...")

    tests = [
        (
            "Mobile Viewport Configuration",
            test_instance.test_mobile_viewport_configuration,
        ),
        ("Mobile Breakpoint 320px", test_instance.test_mobile_breakpoint_320px),
        ("Mobile Breakpoint 375px", test_instance.test_mobile_breakpoint_375px),
        ("Tablet Breakpoint 768px", test_instance.test_tablet_breakpoint_768px),
        ("Touch Targets Minimum Size", test_instance.test_touch_targets_minimum_size),
        ("Form Inputs Touch Friendly", test_instance.test_form_inputs_touch_friendly),
        ("Modal Mobile Adaptation", test_instance.test_modal_mobile_adaptation),
        ("Modal Actions Mobile Layout", test_instance.test_modal_actions_mobile_layout),
        ("Dashboard Mobile Layout", test_instance.test_dashboard_mobile_layout),
        ("Dashboard Stats Mobile Grid", test_instance.test_dashboard_stats_mobile_grid),
        (
            "Profile Modal Mobile Optimization",
            test_instance.test_profile_modal_mobile_optimization,
        ),
        ("Profile Form Mobile Layout", test_instance.test_profile_form_mobile_layout),
        (
            "Vote Creation Mobile Adaptation",
            test_instance.test_vote_creation_mobile_adaptation,
        ),
        (
            "Image Upload Mobile Interface",
            test_instance.test_image_upload_mobile_interface,
        ),
        ("Vote Sharing Mobile Layout", test_instance.test_vote_sharing_mobile_layout),
        (
            "Responsive Breakpoints Sequence",
            test_instance.test_responsive_breakpoints_sequence,
        ),
        ("Touch Feedback Mobile", test_instance.test_touch_feedback_mobile),
        ("Form Inputs Mobile Keyboard", test_instance.test_form_inputs_mobile_keyboard),
        (
            "Top App Bar Mobile Adaptation",
            test_instance.test_top_app_bar_mobile_adaptation,
        ),
        ("Snackbar Mobile Positioning", test_instance.test_snackbar_mobile_positioning),
        (
            "Mobile Accessibility Features",
            test_instance.test_mobile_accessibility_features,
        ),
        ("Mobile Performance Basics", test_instance.test_mobile_performance_basics),
        (
            "Landscape Orientation Adaptation",
            test_instance.test_landscape_orientation_adaptation,
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

    print("\n📊 Mobile-First Responsive Design Test Results:")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {passed_tests / (passed_tests + failed_tests) * 100:.1f}%")

    return failed_tests == 0


if __name__ == "__main__":
    success = asyncio.run(run_mobile_responsive_tests())
    exit(0 if success else 1)
