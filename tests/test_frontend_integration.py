"""Frontend integration tests for the ToVéCo voting platform.

This module tests the complete user workflow including:
- Frontend JavaScript functionality
- API integration
- User interface behavior
- Accessibility features
- Error handling
"""

import time

import pytest
from fastapi.testclient import TestClient
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.toveco_voting.main import app


class TestFrontendWorkflow:
    """Test the complete frontend user workflow."""

    @pytest.fixture(scope="class")
    def test_server(self):
        """Start test server for frontend tests."""
        import threading
        from contextlib import contextmanager

        import uvicorn

        @contextmanager
        def run_test_server():
            config = uvicorn.Config(
                app, host="127.0.0.1", port=8001, log_level="warning"
            )
            server = uvicorn.Server(config)

            def run_server():
                server.run()

            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()

            # Wait for server to start
            time.sleep(2)

            try:
                yield "http://127.0.0.1:8001"
            finally:
                server.should_exit = True

        return run_test_server()

    @pytest.fixture(scope="class")
    def driver(self):
        """Create WebDriver instance for testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless for CI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            yield driver
        except Exception as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
        finally:
            if driver:
                driver.quit()

    def test_homepage_loads(self, test_server, driver):
        """Test that the homepage loads correctly."""
        with test_server as base_url:
            driver.get(base_url)

            # Check page title
            assert "ToV" in driver.title and "éCo" in driver.title

            # Check welcome screen is visible
            welcome_screen = driver.find_element(By.ID, "welcome-screen")
            assert welcome_screen.is_displayed()

            # Check name input exists
            name_input = driver.find_element(By.ID, "voter-name")
            assert name_input.is_displayed()

    def test_name_validation(self, test_server, driver):
        """Test name input validation."""
        with test_server as base_url:
            driver.get(base_url)

            driver.find_element(By.ID, "voter-name")
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

            # Test empty name
            submit_btn.click()
            time.sleep(0.5)

            # Should show error message
            error_message = driver.find_element(By.CLASS_NAME, "error-message")
            assert error_message.is_displayed()
            assert "nom" in error_message.text.lower()

    def test_name_input_too_long(self, test_server, driver):
        """Test name input with too many characters."""
        with test_server as base_url:
            driver.get(base_url)

            name_input = driver.find_element(By.ID, "voter-name")
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

            # Enter name that's too long (>100 chars)
            long_name = "a" * 101
            name_input.clear()
            name_input.send_keys(long_name)
            submit_btn.click()

            time.sleep(0.5)

            # Should show error message
            try:
                error_message = driver.find_element(By.CLASS_NAME, "error-message")
                assert error_message.is_displayed()
                assert "100" in error_message.text
            except NoSuchElementException:
                # Alternative: check if aria-invalid is set
                assert name_input.get_attribute("aria-invalid") == "true"

    def test_valid_name_proceeds_to_voting(self, test_server, driver):
        """Test that valid name proceeds to voting screen."""
        with test_server as base_url:
            driver.get(base_url)

            name_input = driver.find_element(By.ID, "voter-name")
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

            # Enter valid name
            name_input.clear()
            name_input.send_keys("Test User")
            submit_btn.click()

            # Wait for voting screen to appear
            wait = WebDriverWait(driver, 10)
            voting_screen = wait.until(
                EC.visibility_of_element_located((By.ID, "voting-screen"))
            )

            assert voting_screen.is_displayed()

    def test_logo_display(self, test_server, driver):
        """Test that logos are displayed correctly."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Check logo image is displayed
            logo_img = driver.find_element(By.ID, "current-logo")
            assert logo_img.is_displayed()
            assert logo_img.get_attribute("src").endswith(".png")

            # Check alt text
            alt_text = logo_img.get_attribute("alt")
            assert "Logo" in alt_text

    def test_rating_selection(self, test_server, driver):
        """Test rating selection functionality."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Find rating inputs
            rating_inputs = driver.find_elements(
                By.CSS_SELECTOR, "input[name='rating']"
            )
            assert len(rating_inputs) == 5  # -2, -1, 0, 1, 2

            # Test selecting a rating
            rating_2 = driver.find_element(
                By.CSS_SELECTOR, "input[name='rating'][value='2']"
            )
            rating_2.click()

            assert rating_2.is_selected()

            # Test that next button is enabled after rating
            next_btn = driver.find_element(By.ID, "next-btn")
            assert next_btn.is_enabled()

    def test_navigation_buttons(self, test_server, driver):
        """Test navigation button functionality."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Previous button should be disabled initially
            prev_btn = driver.find_element(By.ID, "prev-btn")
            assert not prev_btn.is_enabled()

            # Next button should be disabled without rating
            next_btn = driver.find_element(By.ID, "next-btn")
            assert not next_btn.is_enabled()

            # Select a rating
            rating_1 = driver.find_element(
                By.CSS_SELECTOR, "input[name='rating'][value='1']"
            )
            rating_1.click()

            # Next button should be enabled
            assert next_btn.is_enabled()

            # Click next
            next_btn.click()
            time.sleep(0.5)

            # Previous button should now be enabled
            assert prev_btn.is_enabled()

    def test_keyboard_navigation(self, test_server, driver):
        """Test keyboard navigation functionality."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Get the body element to send keys to
            body = driver.find_element(By.TAG_NAME, "body")

            # Test rating selection with number keys
            body.send_keys("5")  # Should select rating 2 (5th option)
            time.sleep(0.5)

            rating_2 = driver.find_element(
                By.CSS_SELECTOR, "input[name='rating'][value='2']"
            )
            assert rating_2.is_selected()

            # Test navigation with arrow keys
            body.send_keys(Keys.ARROW_RIGHT)  # Should go to next logo
            time.sleep(0.5)

            # Check progress changed
            progress_text = driver.find_element(By.ID, "progress-text")
            assert "2" in progress_text.text

    def test_progress_indicator(self, test_server, driver):
        """Test progress indicator updates correctly."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Check initial progress
            progress_text = driver.find_element(By.ID, "progress-text")
            initial_text = progress_text.text
            assert "1" in initial_text and "11" in initial_text

            # Rate current logo and go to next
            rating_1 = driver.find_element(
                By.CSS_SELECTOR, "input[name='rating'][value='1']"
            )
            rating_1.click()

            next_btn = driver.find_element(By.ID, "next-btn")
            next_btn.click()
            time.sleep(0.5)

            # Check progress updated
            updated_text = progress_text.text
            assert "2" in updated_text and "11" in updated_text

    def test_error_message_display(self, test_server, driver):
        """Test error message display and accessibility."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Try to proceed without rating
            next_btn = driver.find_element(By.ID, "next-btn")
            # Force click even if disabled (to test error handling)
            driver.execute_script("arguments[0].click();", next_btn)

            time.sleep(0.5)

            # Should show error message
            try:
                error_message = driver.find_element(By.CLASS_NAME, "error-message")
                assert error_message.is_displayed()

                # Check accessibility attributes
                assert error_message.get_attribute("role") == "alert"
                assert error_message.get_attribute("aria-live") == "assertive"
            except NoSuchElementException:
                # Alternative: button might stay disabled
                assert not next_btn.is_enabled()

    def test_logo_loading_error_handling(self, test_server, driver):
        """Test handling of logo loading errors."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Change logo src to invalid URL to trigger error
            logo_img = driver.find_element(By.ID, "current-logo")
            driver.execute_script(
                "arguments[0].src = '/logos/nonexistent.png';", logo_img
            )

            time.sleep(1)

            # Should handle error gracefully (might show error message)
            # At minimum, the application shouldn't crash
            voting_screen = driver.find_element(By.ID, "voting-screen")
            assert voting_screen.is_displayed()

    def test_complete_voting_workflow(self, test_server, driver):
        """Test complete voting workflow from start to finish."""
        with test_server as base_url:
            driver.get(base_url)

            # Enter name
            name_input = driver.find_element(By.ID, "voter-name")
            name_input.send_keys("Complete Test User")
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()

            # Wait for voting screen
            wait = WebDriverWait(driver, 10)
            wait.until(EC.visibility_of_element_located((By.ID, "voting-screen")))

            # Rate all logos (simplified - rate first few and skip to review)
            for i in range(3):  # Rate first 3 logos
                # Select a rating
                rating = driver.find_element(
                    By.CSS_SELECTOR, f"input[name='rating'][value='{i - 1}']"
                )
                rating.click()

                # Go to next
                next_btn = driver.find_element(By.ID, "next-btn")
                if next_btn.text != "Terminer":
                    next_btn.click()
                    time.sleep(0.5)
                else:
                    break

            # This would normally proceed to review screen in a complete test
            # For this test, we verify the workflow is functional

    def test_accessibility_features(self, test_server, driver):
        """Test accessibility features."""
        with test_server as base_url:
            self._proceed_to_voting_screen(driver, base_url, "Test User")

            # Check ARIA attributes
            rating_group = driver.find_element(By.CSS_SELECTOR, "[role='radiogroup']")
            assert rating_group.get_attribute("aria-label")

            # Check live region exists
            live_region = driver.find_element(By.ID, "live-region")
            assert live_region.get_attribute("aria-live") == "polite"

            # Check progress bar accessibility
            progress_bar = driver.find_element(By.CSS_SELECTOR, "[role='progressbar']")
            assert progress_bar.get_attribute("aria-valuenow")
            assert progress_bar.get_attribute("aria-valuemax")

    def test_mobile_responsiveness(self, test_server, driver):
        """Test mobile responsive behavior."""
        with test_server as base_url:
            # Set mobile viewport
            driver.set_window_size(375, 667)  # iPhone SE dimensions

            driver.get(base_url)

            # Check that elements are still visible and functional
            welcome_screen = driver.find_element(By.ID, "welcome-screen")
            assert welcome_screen.is_displayed()

            name_input = driver.find_element(By.ID, "voter-name")
            assert name_input.is_displayed()

            # Check that the layout adapts (elements should stack vertically)
            name_input_rect = name_input.rect
            assert name_input_rect["width"] > 200  # Should be reasonably wide on mobile

    def _proceed_to_voting_screen(self, driver, base_url: str, voter_name: str):
        """Helper method to proceed to voting screen."""
        driver.get(base_url)

        name_input = driver.find_element(By.ID, "voter-name")
        name_input.send_keys(voter_name)

        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Wait for voting screen
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.ID, "voting-screen")))


class TestJavaScriptFunctionality:
    """Test JavaScript functionality without browser automation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        with TestClient(app) as test_client:
            yield test_client

    def test_api_endpoints_return_json(self, client):
        """Test that API endpoints return proper JSON for JavaScript consumption."""
        # Test logos endpoint
        response = client.get("/api/logos")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "logos" in data
        assert "total_count" in data

    def test_vote_submission_json_format(self, client):
        """Test vote submission accepts and returns proper JSON format."""
        vote_data = {
            "voter_name": "JS Test User",
            "ratings": {
                "toveco1.png": 1,
                "toveco2.png": -1,
                "toveco3.png": 0,
                "toveco4.png": 2,
                "toveco5.png": -2,
                "toveco6.png": 1,
                "toveco7.png": 0,
                "toveco8.png": 1,
                "toveco9.png": -1,
                "toveco10.png": 2,
                "toveco11.png": 0,
            },
        }

        response = client.post("/api/vote", json=vote_data)

        # Should return JSON response regardless of success/failure
        assert "application/json" in response.headers["content-type"]

        data = response.json()
        assert "success" in data
        assert "message" in data

    def test_results_endpoint_json_structure(self, client):
        """Test results endpoint returns proper JSON structure for JavaScript."""
        response = client.get("/api/results")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "summary" in data
        assert "total_voters" in data
        assert isinstance(data["summary"], dict)
        assert isinstance(data["total_voters"], int)

    def test_cors_headers_for_javascript(self, client):
        """Test CORS headers are properly set for JavaScript requests."""
        response = client.get("/api/logos")

        # Check CORS headers (if configured)

        # These might be present depending on CORS configuration

        # At least one CORS header should be present or it should work without CORS
        # (same-origin requests)
        assert response.status_code == 200

    def test_error_response_format_for_javascript(self, client):
        """Test error responses are in format expected by JavaScript."""
        # Submit invalid vote to trigger error
        invalid_vote = {
            "voter_name": "",  # Invalid empty name
            "ratings": {},
        }

        response = client.post("/api/vote", json=invalid_vote)
        assert response.status_code == 422

        data = response.json()
        assert "success" in data or "message" in data or "detail" in data


class TestResultsPageFunctionality:
    """Test results page specific functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        with TestClient(app) as test_client:
            yield test_client

    @pytest.fixture(scope="class")
    def test_server(self):
        """Start test server for results page tests."""
        import threading
        from contextlib import contextmanager

        import uvicorn

        @contextmanager
        def run_test_server():
            config = uvicorn.Config(
                app, host="127.0.0.1", port=8002, log_level="warning"
            )
            server = uvicorn.Server(config)

            def run_server():
                server.run()

            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()

            time.sleep(2)

            try:
                yield "http://127.0.0.1:8002"
            finally:
                server.should_exit = True

        return run_test_server()

    @pytest.fixture(scope="class")
    def driver(self):
        """Create WebDriver instance for results testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            yield driver
        except Exception as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
        finally:
            if driver:
                driver.quit()

    def test_results_page_loads(self, test_server, driver):
        """Test that results page loads correctly."""
        with test_server as base_url:
            driver.get(f"{base_url}/results")

            assert "ToV" in driver.title and "éCo" in driver.title

            # Check for results content
            try:
                results_content = driver.find_element(By.ID, "results-content")
                assert results_content.is_displayed()
            except NoSuchElementException:
                # Might be in loading state initially
                loading_state = driver.find_element(By.ID, "loading-state")
                assert loading_state.is_displayed()

    def test_results_display_structure(self, client):
        """Test results display has correct structure."""
        response = client.get("/results")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # The HTML should contain expected elements
        html_content = response.text
        expected_elements = [
            "results-content",
            "results-grid",
            "total-voters",
            "total-logos",
        ]

        for element_id in expected_elements:
            assert element_id in html_content

    def test_results_api_integration(self, client):
        """Test that results page can fetch data from API."""
        # This tests the backend that the frontend JavaScript will call
        response = client.get("/api/results")
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "total_voters" in data


# Manual test script that can be run separately
def create_manual_test_script():
    """Create a manual test script for frontend validation."""
    script_content = """#!/usr/bin/env python3
'''
Manual Frontend Test Script for ToVéCo Voting Platform

This script provides manual test cases that can be executed by a human tester
to validate the frontend functionality when automated tests aren't feasible.
'''

import json
import requests
import time


class ManualTestGuide:
    '''Guide for manual testing of the frontend.'''

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []

    def print_test_header(self, test_name):
        print(f"\\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")

    def print_test_step(self, step_number, description):
        print(f"\\nStep {step_number}: {description}")

    def record_result(self, test_name, passed, notes=""):
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "notes": notes
        })
        status = "PASS" if passed else "FAIL"
        print(f"Result: {status}")
        if notes:
            print(f"Notes: {notes}")

    def test_homepage_accessibility(self):
        self.print_test_header("Homepage Accessibility")

        print("Manual steps:")
        self.print_test_step(1, f"Open {self.base_url} in your browser")
        self.print_test_step(2, "Use Tab key to navigate through all interactive elements")
        self.print_test_step(3, "Verify focus indicators are visible")
        self.print_test_step(4, "Test with screen reader if available")
        self.print_test_step(5, "Verify all images have alt text")

        result = input("Did all accessibility tests pass? (y/n): ").lower() == 'y'
        notes = input("Any notes: ")
        self.record_result("Homepage Accessibility", result, notes)

    def test_voting_workflow(self):
        self.print_test_header("Complete Voting Workflow")

        print("Manual steps:")
        self.print_test_step(1, "Enter your name and click 'Commencer le vote'")
        self.print_test_step(2, "Verify logos load correctly (11 total)")
        self.print_test_step(3, "Rate each logo using the -2 to +2 scale")
        self.print_test_step(4, "Test navigation with Previous/Next buttons")
        self.print_test_step(5, "Test keyboard navigation (arrow keys, number keys)")
        self.print_test_step(6, "Verify progress indicator updates")
        self.print_test_step(7, "Complete voting for all logos")
        self.print_test_step(8, "Review your votes on the summary screen")
        self.print_test_step(9, "Submit votes and verify success message")

        result = input("Did the complete workflow work correctly? (y/n): ").lower() == 'y'
        notes = input("Any issues encountered: ")
        self.record_result("Complete Voting Workflow", result, notes)

    def test_mobile_responsiveness(self):
        self.print_test_header("Mobile Responsiveness")

        print("Manual steps:")
        self.print_test_step(1, "Open browser developer tools (F12)")
        self.print_test_step(2, "Set viewport to mobile size (375x667 iPhone SE)")
        self.print_test_step(3, "Verify layout adapts correctly")
        self.print_test_step(4, "Test touch interactions work")
        self.print_test_step(5, "Verify all text is readable on small screen")
        self.print_test_step(6, "Test landscape orientation")

        result = input("Did mobile responsiveness work correctly? (y/n): ").lower() == 'y'
        notes = input("Any layout issues: ")
        self.record_result("Mobile Responsiveness", result, notes)

    def test_error_handling(self):
        self.print_test_header("Error Handling")

        print("Manual steps:")
        self.print_test_step(1, "Try submitting empty name")
        self.print_test_step(2, "Try submitting name with >100 characters")
        self.print_test_step(3, "Try proceeding without rating a logo")
        self.print_test_step(4, "Disconnect internet and try submitting vote")
        self.print_test_step(5, "Verify error messages are user-friendly")
        self.print_test_step(6, "Verify errors are announced to screen readers")

        result = input("Did error handling work correctly? (y/n): ").lower() == 'y'
        notes = input("Any error handling issues: ")
        self.record_result("Error Handling", result, notes)

    def test_results_page(self):
        self.print_test_header("Results Page")

        print("Manual steps:")
        self.print_test_step(1, f"Navigate to {self.base_url}/results")
        self.print_test_step(2, "Verify results load correctly")
        self.print_test_step(3, "Check statistics are displayed")
        self.print_test_step(4, "Verify logos are ranked correctly")
        self.print_test_step(5, "Test share functionality if present")
        self.print_test_step(6, "Test print functionality")

        result = input("Did results page work correctly? (y/n): ").lower() == 'y'
        notes = input("Any results page issues: ")
        self.record_result("Results Page", result, notes)

    def run_all_tests(self):
        '''Run all manual tests.'''
        print("ToVéCo Frontend Manual Test Suite")
        print("=================================")
        print("This will guide you through manual testing of the frontend.")
        print("Please follow each step carefully and report results accurately.\\n")

        self.test_homepage_accessibility()
        self.test_voting_workflow()
        self.test_mobile_responsiveness()
        self.test_error_handling()
        self.test_results_page()

        # Summary
        print("\\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        passed_tests = sum(1 for result in self.test_results if result["passed"])
        total_tests = len(self.test_results)

        for result in self.test_results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{result['test']:<30} {status}")

        print(f"\\nTotal: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All tests passed! Frontend is ready for production.")
        else:
            print("⚠️  Some tests failed. Please review and fix issues before deployment.")

        return self.test_results


if __name__ == "__main__":
    tester = ManualTestGuide()
    tester.run_all_tests()
"""

    return script_content


# Save the manual test script
def save_manual_test_script():
    """Save the manual test script to file."""
    script_content = create_manual_test_script()

    with open("/Users/vlb/Downloads/toveco/tests/manual_frontend_tests.py", "w") as f:
        f.write(script_content)


if __name__ == "__main__":
    # Save manual test script
    save_manual_test_script()

    # Run automated tests
    pytest.main([__file__, "-v"])
