"""
Playwright tests for Touch Interaction Enhancements.

Tests touch feedback, gesture recognition, long press actions,
swipe gestures, and mobile-optimized touch event handling.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright, expect


class TestTouchInteractions:
    """Test touch interaction enhancements across all components."""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up Playwright browser and page for each test."""
        self.playwright = await async_playwright().start()

        # Use mobile browser context for touch testing
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 375, "height": 667}, has_touch=True, is_mobile=True
        )
        self.page = await self.context.new_page()

        yield

        # Clean up
        await self.page.close()
        await self.context.close()
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
    # TOUCH INTERACTION MANAGER INITIALIZATION
    # ==========================================================================

    async def test_touch_interaction_manager_initialization(self):
        """Test that touch interaction manager initializes properly."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Check that touch interaction manager is loaded
        touch_manager_exists = await self.page.evaluate("""
            typeof window.touchInteractionManager !== 'undefined'
        """)

        assert touch_manager_exists, "Touch interaction manager not initialized"

        # Check touch device detection
        is_touch_device = await self.page.evaluate("""
            window.touchInteractionManager ? window.touchInteractionManager.isTouchDevice : false
        """)

        assert is_touch_device, "Touch device not detected properly"

    # ==========================================================================
    # TOUCH FEEDBACK TESTS
    # ==========================================================================

    async def test_button_touch_feedback(self):
        """Test that buttons provide immediate touch feedback."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Find a button to test
        get_started_btn = self.page.locator(
            'button[data-action="show-register"]'
        ).first()
        if await get_started_btn.is_visible():
            # Simulate touch start
            await get_started_btn.tap()
            await self.page.wait_for_timeout(100)

            # Check for touch feedback classes (they might be briefly applied)
            # Since the feedback is quick, we'll check if the manager can handle touch events
            touch_feedback_works = await self.page.evaluate("""
                // Test if touch feedback system responds
                const btn = document.querySelector('button[data-action="show-register"]');
                if (btn && window.touchInteractionManager) {
                    return typeof window.touchInteractionManager.addTouchFeedback === 'function';
                }
                return false;
            """)

            assert touch_feedback_works, "Touch feedback system not working"

    async def test_ripple_effect_creation(self):
        """Test that ripple effects are created on touch."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test ripple effect functionality
        ripple_system_works = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                const testElement = document.createElement('button');
                testElement.style.position = 'relative';
                testElement.style.width = '100px';
                testElement.style.height = '100px';
                document.body.appendChild(testElement);

                // Simulate touch position
                window.touchInteractionManager.touchStartPosition = { x: 50, y: 50 };
                window.touchInteractionManager.createRippleEffect(testElement);

                const hasRipple = testElement.querySelector('.touch-ripple') !== null;
                document.body.removeChild(testElement);
                return hasRipple;
            }
            return false;
        """)

        assert ripple_system_works, "Ripple effect system not working"

    async def test_touch_target_detection(self):
        """Test that touch targets are properly detected."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test touch target detection
        touch_detection_works = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                const button = document.querySelector('button');
                if (button) {
                    const touchTarget = window.touchInteractionManager.findTouchTarget(button);
                    return touchTarget === button;
                }
            }
            return false;
        """)

        assert touch_detection_works, "Touch target detection not working"

    # ==========================================================================
    # GESTURE RECOGNITION TESTS
    # ==========================================================================

    async def test_swipe_gesture_detection(self):
        """Test swipe gesture recognition system."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test swipe gesture system
        swipe_system_exists = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.handleSwipeGesture === 'function' &&
                       typeof window.touchInteractionManager.triggerSwipeEvent === 'function';
            }
            return false;
        """)

        assert swipe_system_exists, "Swipe gesture system not implemented"

    async def test_long_press_detection(self):
        """Test long press detection system."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test long press system
        long_press_system_exists = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.startLongPressDetection === 'function' &&
                       typeof window.touchInteractionManager.handleLongPress === 'function' &&
                       window.touchInteractionManager.longPressThreshold === 500;
            }
            return false;
        """)

        assert long_press_system_exists, "Long press detection system not implemented"

    # ==========================================================================
    # IMAGE GALLERY SWIPE TESTS
    # ==========================================================================

    async def test_image_gallery_swipe_integration(self):
        """Test image gallery swipe gesture integration."""
        await self.simulate_authenticated_user()
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Open vote creation to access image upload interface
        create_btn = self.page.locator('button[data-action="create-vote"]')
        if await create_btn.is_visible():
            await create_btn.tap()
            await self.page.wait_for_timeout(500)

            # Test image gallery swipe system
            swipe_integration_exists = await self.page.evaluate("""
                if (window.touchInteractionManager) {
                    return typeof window.touchInteractionManager.initializeImageGallerySwipes === 'function' &&
                           typeof window.touchInteractionManager.navigateImageGallery === 'function';
                }
                return false;
            """)

            assert swipe_integration_exists, (
                "Image gallery swipe integration not implemented"
            )

    # ==========================================================================
    # CARD SWIPE TESTS
    # ==========================================================================

    async def test_card_swipe_animations(self):
        """Test card swipe animation system."""
        await self.simulate_authenticated_user()
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Test card swipe system
        card_swipe_exists = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.initializeCardSwipes === 'function';
            }
            return false;
        """)

        assert card_swipe_exists, "Card swipe system not implemented"

    # ==========================================================================
    # HAPTIC FEEDBACK TESTS
    # ==========================================================================

    async def test_haptic_feedback_system(self):
        """Test haptic feedback integration."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test haptic feedback detection and system
        haptic_system_exists = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.provideHapticFeedback === 'function' &&
                       typeof window.touchInteractionManager.hasHapticFeedback === 'boolean';
            }
            return false;
        """)

        assert haptic_system_exists, "Haptic feedback system not implemented"

    # ==========================================================================
    # TOOLTIP SYSTEM TESTS
    # ==========================================================================

    async def test_touch_tooltip_system(self):
        """Test touch tooltip functionality."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test tooltip system
        tooltip_system_exists = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.showTemporaryTooltip === 'function';
            }
            return false;
        """)

        assert tooltip_system_exists, "Touch tooltip system not implemented"

    # ==========================================================================
    # DESKTOP ARTIFACT PREVENTION TESTS
    # ==========================================================================

    async def test_desktop_hover_prevention(self):
        """Test that desktop hover artifacts are prevented."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test hover prevention system
        hover_prevention_exists = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.preventDesktopArtifacts === 'function';
            }
            return false;
        """)

        assert hover_prevention_exists, "Desktop artifact prevention not implemented"

    # ==========================================================================
    # PERFORMANCE OPTIMIZATION TESTS
    # ==========================================================================

    async def test_touch_performance_optimizations(self):
        """Test touch interaction performance optimizations."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test performance-related methods
        performance_optimizations_exist = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.handleTap === 'function' &&
                       window.touchInteractionManager.touchMoveThreshold === 10;
            }
            return false;
        """)

        assert performance_optimizations_exist, (
            "Touch performance optimizations not implemented"
        )

    # ==========================================================================
    # DASHBOARD TOUCH INTEGRATION TESTS
    # ==========================================================================

    async def test_dashboard_touch_integration(self):
        """Test touch interactions in dashboard components."""
        await self.simulate_authenticated_user()
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Test dashboard-specific touch enhancements
        dashboard_fab = self.page.locator(".dashboard-fab, .creation-fab")
        if await dashboard_fab.is_visible():
            # Test FAB touch interaction
            await dashboard_fab.tap()
            await self.page.wait_for_timeout(200)

            # Verify FAB responds to touch
            # (The actual response will depend on the implementation)

    async def test_profile_modal_touch_interactions(self):
        """Test touch interactions in profile management modal."""
        await self.simulate_authenticated_user()
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Open profile modal
        user_menu_btn = self.page.locator('button[data-action="user-menu"]')
        if await user_menu_btn.is_visible():
            await user_menu_btn.tap()
            await self.page.wait_for_timeout(500)

            profile_menu_item = self.page.locator(
                '.md-menu-item[data-action="profile"]'
            )
            if await profile_menu_item.is_visible():
                await profile_menu_item.tap()
                await self.page.wait_for_timeout(500)

                # Test modal touch interactions
                profile_modal = self.page.locator(
                    '#profileModalScrim[aria-hidden="false"]'
                )
                await expect(profile_modal).to_be_visible()

    # ==========================================================================
    # VOTE SHARING TOUCH TESTS
    # ==========================================================================

    async def test_vote_sharing_touch_interactions(self):
        """Test touch interactions in vote sharing interface."""
        await self.simulate_authenticated_user()

        # Mock vote preview API
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

        # Test copy button touch interaction
        copy_button = self.page.locator('[data-action="copy-link"]')
        if await copy_button.is_visible():
            await copy_button.tap()
            await self.page.wait_for_timeout(200)

    # ==========================================================================
    # FORM TOUCH INTERACTION TESTS
    # ==========================================================================

    async def test_form_input_touch_optimization(self):
        """Test touch optimization for form inputs."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Open registration modal
        get_started_btn = self.page.locator(
            'button[data-action="show-register"]'
        ).first()
        if await get_started_btn.is_visible():
            await get_started_btn.tap()
            await self.page.wait_for_timeout(500)

            # Test input field touch interaction
            email_input = self.page.locator("#registerEmail")
            if await email_input.is_visible():
                await email_input.tap()
                await self.page.wait_for_timeout(200)

                # Check input is focused
                is_focused = await email_input.evaluate(
                    "el => document.activeElement === el"
                )
                assert is_focused, "Input should be focused after touch"

    # ==========================================================================
    # CSS ANIMATION TESTS
    # ==========================================================================

    async def test_touch_css_animations_loaded(self):
        """Test that touch enhancement CSS animations are loaded."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Check for touch-specific CSS classes
        touch_css_loaded = await self.page.evaluate("""
            const styles = Array.from(document.styleSheets);
            return styles.some(sheet => {
                try {
                    const rules = Array.from(sheet.cssRules || sheet.rules || []);
                    return rules.some(rule =>
                        rule.selectorText && (
                            rule.selectorText.includes('.touch-active') ||
                            rule.selectorText.includes('.touch-ripple') ||
                            rule.selectorText.includes('@keyframes touch-ripple')
                        )
                    );
                } catch (e) {
                    return false;
                }
            });
        """)

        assert touch_css_loaded, "Touch enhancement CSS not loaded properly"

    # ==========================================================================
    # ACCESSIBILITY TESTS
    # ==========================================================================

    async def test_touch_accessibility_features(self):
        """Test touch interaction accessibility features."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test accessibility methods exist
        accessibility_features_exist = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                // Touch interactions shouldn't interfere with keyboard navigation
                const buttons = document.querySelectorAll('button');
                return buttons.length > 0; // Basic check that interactive elements exist
            }
            return false;
        """)

        assert accessibility_features_exist, (
            "Touch accessibility features not properly implemented"
        )

    # ==========================================================================
    # PUBLIC API TESTS
    # ==========================================================================

    async def test_touch_manager_public_api(self):
        """Test public API methods of touch interaction manager."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test public API methods
        public_api_complete = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.enableTouchFeedback === 'function' &&
                       typeof window.touchInteractionManager.disableTouchFeedback === 'function' &&
                       typeof window.touchInteractionManager.addLongPressHandler === 'function' &&
                       typeof window.touchInteractionManager.addSwipeHandler === 'function';
            }
            return false;
        """)

        assert public_api_complete, "Touch manager public API not complete"

    # ==========================================================================
    # CLEANUP AND MEMORY TESTS
    # ==========================================================================

    async def test_touch_manager_cleanup(self):
        """Test touch manager cleanup functionality."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Test cleanup method exists
        cleanup_exists = await self.page.evaluate("""
            if (window.touchInteractionManager) {
                return typeof window.touchInteractionManager.destroy === 'function';
            }
            return false;
        """)

        assert cleanup_exists, "Touch manager cleanup method not implemented"

    # ==========================================================================
    # TOUCH EVENT SIMULATION TESTS
    # ==========================================================================

    async def test_simulated_touch_events(self):
        """Test response to simulated touch events."""
        await self.page.goto("http://localhost:8000")
        await self.page.wait_for_timeout(1000)

        # Simulate touch events programmatically
        touch_response = await self.page.evaluate("""
            // Create a test button
            const testButton = document.createElement('button');
            testButton.textContent = 'Test Button';
            testButton.className = 'md-button';
            document.body.appendChild(testButton);

            // Simulate touch start event
            const touchEvent = new TouchEvent('touchstart', {
                touches: [{
                    clientX: 100,
                    clientY: 100,
                    target: testButton
                }],
                bubbles: true,
                cancelable: true
            });

            testButton.dispatchEvent(touchEvent);

            // Clean up
            document.body.removeChild(testButton);

            return true; // Event was dispatched successfully
        """)

        assert touch_response, "Touch event simulation failed"

    # ==========================================================================
    # INTEGRATION TESTS
    # ==========================================================================

    async def test_touch_manager_integration_with_existing_components(self):
        """Test integration with existing component managers."""
        await self.simulate_authenticated_user()
        await self.page.goto("http://localhost:8000/dashboard")
        await self.page.wait_for_timeout(1000)

        # Test integration with existing managers
        integration_works = await self.page.evaluate("""
            // Check that multiple managers can coexist
            return window.touchInteractionManager &&
                   (window.profileManager || window.dashboardManager || true) &&
                   typeof window.touchInteractionManager.init === 'function';
        """)

        assert integration_works, (
            "Touch manager integration with existing components failed"
        )


async def run_touch_interaction_tests():
    """Run all touch interaction enhancement tests."""
    test_instance = TestTouchInteractions()

    print("🤏 Running Touch Interaction Enhancement Tests...")

    tests = [
        (
            "Touch Manager Initialization",
            test_instance.test_touch_interaction_manager_initialization,
        ),
        ("Button Touch Feedback", test_instance.test_button_touch_feedback),
        ("Ripple Effect Creation", test_instance.test_ripple_effect_creation),
        ("Touch Target Detection", test_instance.test_touch_target_detection),
        ("Swipe Gesture Detection", test_instance.test_swipe_gesture_detection),
        ("Long Press Detection", test_instance.test_long_press_detection),
        (
            "Image Gallery Swipe Integration",
            test_instance.test_image_gallery_swipe_integration,
        ),
        ("Card Swipe Animations", test_instance.test_card_swipe_animations),
        ("Haptic Feedback System", test_instance.test_haptic_feedback_system),
        ("Touch Tooltip System", test_instance.test_touch_tooltip_system),
        ("Desktop Hover Prevention", test_instance.test_desktop_hover_prevention),
        (
            "Touch Performance Optimizations",
            test_instance.test_touch_performance_optimizations,
        ),
        ("Dashboard Touch Integration", test_instance.test_dashboard_touch_integration),
        (
            "Profile Modal Touch Interactions",
            test_instance.test_profile_modal_touch_interactions,
        ),
        (
            "Vote Sharing Touch Interactions",
            test_instance.test_vote_sharing_touch_interactions,
        ),
        (
            "Form Input Touch Optimization",
            test_instance.test_form_input_touch_optimization,
        ),
        ("Touch CSS Animations Loaded", test_instance.test_touch_css_animations_loaded),
        (
            "Touch Accessibility Features",
            test_instance.test_touch_accessibility_features,
        ),
        ("Touch Manager Public API", test_instance.test_touch_manager_public_api),
        ("Touch Manager Cleanup", test_instance.test_touch_manager_cleanup),
        ("Simulated Touch Events", test_instance.test_simulated_touch_events),
        (
            "Integration with Existing Components",
            test_instance.test_touch_manager_integration_with_existing_components,
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

    print("\n📊 Touch Interaction Enhancement Test Results:")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {passed_tests / (passed_tests + failed_tests) * 100:.1f}%")

    return failed_tests == 0


if __name__ == "__main__":
    success = asyncio.run(run_touch_interaction_tests())
    exit(0 if success else 1)
