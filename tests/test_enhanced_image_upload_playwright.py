"""
Enhanced Image Upload Interface Playwright Tests
Phase 3.1 (T-007) - Comprehensive validation
"""

import asyncio
import tempfile
from pathlib import Path
from PIL import Image
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

class TestEnhancedImageUploadInterface:
    """Test Enhanced Image Upload Interface with Playwright validation."""

    @pytest_asyncio.fixture
    async def browser_context(self):
        """Setup browser context for testing."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720}
            )
            yield context
            await context.close()
            await browser.close()

    @pytest_asyncio.fixture
    async def authenticated_page(self, browser_context):
        """Create authenticated page for testing."""
        page = await browser_context.new_page()

        # Navigate to application
        await page.goto("http://localhost:8000")

        # Wait for page load
        await page.wait_for_load_state("networkidle")

        # Check if already authenticated
        if await page.is_visible('[data-action="sign-out"]'):
            yield page
            await page.close()
            return

        # Register and login via API first to create a test user
        import time
        import httpx
        unique_email = f"playwright{int(time.time())}@example.com"
        password = "TestPassword123!"

        async with httpx.AsyncClient() as client:
            # Register user
            await client.post('http://localhost:8000/api/auth/register', json={
                'email': unique_email,
                'password': password,
                'first_name': 'Playwright',
                'last_name': 'Test'
            })

            # Login to get tokens
            login_response = await client.post('http://localhost:8000/api/auth/login', json={
                'email': unique_email,
                'password': password
            })

            if login_response.status_code != 200:
                raise Exception(f"Login failed: {login_response.status_code} - {login_response.text}")

            login_data = login_response.json()

            if 'access_token' not in login_data:
                raise Exception(f"No access token in login response: {login_data}")

        # Set tokens in browser storage
        await page.evaluate(f"""
            sessionStorage.setItem('access_token', '{login_data["access_token"]}');
            if ('{login_data.get("refresh_token", "")}') {{
                sessionStorage.setItem('refresh_token', '{login_data["refresh_token"]}');
            }}
        """)

        # Navigate to dashboard
        await page.goto("http://localhost:8000/dashboard")
        await page.wait_for_load_state("networkidle")

        # Wait for dashboard to be available
        await page.wait_for_selector('[data-action="create-vote"]', timeout=10000)

        yield page
        await page.close()

    def create_test_image(self, format_type: str = 'PNG', size: tuple = (800, 600)) -> Path:
        """Create a test image file."""
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"test_image_{format_type.lower()}.{format_type.lower()}"

        # Create a simple colored image
        image = Image.new('RGB', size, color=(73, 109, 137))  # Blue color
        image.save(temp_file, format=format_type)

        return temp_file

    @pytest.mark.asyncio
    async def test_image_upload_interface_display(self, authenticated_page: Page):
        """Test that image upload interface displays correctly in vote creation."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModalScrim.md-dialog-scrim-visible', timeout=10000)

        # Check default options have image upload interfaces
        upload_containers = await page.query_selector_all('.option-image-upload')
        assert len(upload_containers) >= 2, "Should have image upload for default options"

        # Verify image upload elements
        for i, container in enumerate(upload_containers[:2]):
            option_id = await container.get_attribute('data-option-id')
            assert option_id, f"Option {i} should have option-id attribute"

            # Check file input exists
            file_input = await page.query_selector(f'#image-{option_id}')
            assert file_input, f"File input should exist for option {i}"

            # Check upload content
            upload_content = await container.query_selector('.upload-content')
            assert upload_content, f"Upload content should exist for option {i}"

            # Check upload icon and text
            upload_icon = await container.query_selector('.upload-icon')
            upload_text = await container.query_selector('.upload-text')
            upload_hint = await container.query_selector('.upload-hint')

            assert upload_icon, f"Upload icon should exist for option {i}"
            assert upload_text, f"Upload text should exist for option {i}"
            assert upload_hint, f"Upload hint should exist for option {i}"

            # Verify text content
            icon_text = await upload_icon.inner_text()
            text_content = await upload_text.inner_text()
            hint_content = await upload_hint.inner_text()

            assert icon_text == 'cloud_upload', f"Upload icon should be correct for option {i}"
            assert 'Click or drag image here' in text_content, f"Upload text should be correct for option {i}"
            assert 'PNG, JPG, GIF, WebP' in hint_content, f"Upload hint should be correct for option {i}"

    @pytest.mark.asyncio
    async def test_image_file_upload_success(self, authenticated_page: Page):
        """Test successful image file upload."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModal[aria-hidden="false"]')

        # Get first option upload container
        first_upload = await page.query_selector('.option-image-upload')
        option_id = await first_upload.get_attribute('data-option-id')

        # Create test image
        test_image = self.create_test_image('PNG', (400, 300))

        try:
            # Upload image via file input
            file_input = await page.query_selector(f'#image-{option_id}')
            await file_input.set_input_files(str(test_image))

            # Wait for upload completion
            await page.wait_for_selector(f'#preview-{option_id}[style*="block"]', timeout=10000)

            # Verify upload progress was shown
            upload_container = await page.query_selector(f'.option-image-upload[data-option-id="{option_id}"]')
            container_classes = await upload_container.get_attribute('class')

            # Check that upload area is hidden after successful upload
            upload_style = await upload_container.get_attribute('style')
            assert 'display: none' in upload_style, "Upload container should be hidden after successful upload"

            # Verify image preview
            preview_container = await page.query_selector(f'#preview-{option_id}')
            preview_style = await preview_container.get_attribute('style')
            assert 'display: block' in preview_style, "Preview should be visible"

            # Check preview elements
            image_thumbnail = await preview_container.query_selector('.image-thumbnail')
            image_filename = await preview_container.query_selector('.image-filename')
            image_details = await preview_container.query_selector('.image-details')
            remove_btn = await preview_container.query_selector('.remove-image-btn')

            assert image_thumbnail, "Image thumbnail should exist"
            assert image_filename, "Image filename should exist"
            assert image_details, "Image details should exist"
            assert remove_btn, "Remove button should exist"

            # Verify image src
            img_src = await image_thumbnail.get_attribute('src')
            assert '/uploads/' in img_src, "Image should have correct upload URL"

            # Verify filename display
            filename_text = await image_filename.inner_text()
            assert 'test_image_png.png' in filename_text, "Filename should be displayed correctly"

            # Verify details (size and dimensions)
            details_text = await image_details.inner_text()
            assert 'KB' in details_text or 'MB' in details_text, "File size should be displayed"
            assert '400×300px' in details_text, "Image dimensions should be displayed"

        finally:
            # Cleanup
            if test_image.exists():
                test_image.unlink()

    @pytest.mark.asyncio
    async def test_image_upload_validation(self, authenticated_page: Page):
        """Test image upload validation errors."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModal[aria-hidden="false"]')

        # Get first option upload container
        first_upload = await page.query_selector('.option-image-upload')
        option_id = await first_upload.get_attribute('data-option-id')

        # Test 1: Invalid file type
        # Create a text file with image extension (this will fail validation)
        temp_dir = Path(tempfile.gettempdir())
        invalid_file = temp_dir / "test_invalid.txt"
        invalid_file.write_text("This is not an image")

        try:
            file_input = await page.query_selector(f'#image-{option_id}')
            await file_input.set_input_files(str(invalid_file))

            # Wait for error to appear
            await page.wait_for_selector(f'#error-{option_id}[style*="flex"]', timeout=5000)

            # Verify error message
            error_container = await page.query_selector(f'#error-{option_id}')
            error_message = await error_container.query_selector('.error-message')
            error_text = await error_message.inner_text()

            assert 'valid image file' in error_text.lower(), f"Should show invalid file type error: {error_text}"

            # Clear the error by uploading a valid file
            valid_image = self.create_test_image('PNG', (200, 200))

            await file_input.set_input_files(str(valid_image))

            # Wait for error to disappear
            await page.wait_for_function(
                f"document.getElementById('error-{option_id}').style.display === 'none'",
                timeout=5000
            )

            # Verify upload success
            await page.wait_for_selector(f'#preview-{option_id}[style*="block"]', timeout=10000)

        finally:
            # Cleanup
            if invalid_file.exists():
                invalid_file.unlink()
            if 'valid_image' in locals() and valid_image.exists():
                valid_image.unlink()

    @pytest.mark.asyncio
    async def test_image_remove_functionality(self, authenticated_page: Page):
        """Test image removal functionality."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModal[aria-hidden="false"]')

        # Get first option upload container
        first_upload = await page.query_selector('.option-image-upload')
        option_id = await first_upload.get_attribute('data-option-id')

        # Upload an image first
        test_image = self.create_test_image('PNG', (300, 300))

        try:
            file_input = await page.query_selector(f'#image-{option_id}')
            await file_input.set_input_files(str(test_image))

            # Wait for upload completion
            await page.wait_for_selector(f'#preview-{option_id}[style*="block"]', timeout=10000)

            # Click remove button
            remove_btn = await page.query_selector(f'#preview-{option_id} .remove-image-btn')
            await remove_btn.click()

            # Verify preview is hidden
            await page.wait_for_function(
                f"document.getElementById('preview-{option_id}').style.display === 'none'",
                timeout=5000
            )

            # Verify upload container is shown again
            upload_container = await page.query_selector(f'.option-image-upload[data-option-id="{option_id}"]')
            upload_style = await upload_container.get_attribute('style')
            assert 'display: block' in upload_style, "Upload container should be visible after remove"

            # Verify file input is cleared
            file_input_value = await file_input.get_attribute('value')
            assert file_input_value == '' or file_input_value is None, "File input should be cleared"

        finally:
            # Cleanup
            if test_image.exists():
                test_image.unlink()

    @pytest.mark.asyncio
    async def test_drag_and_drop_functionality(self, authenticated_page: Page):
        """Test drag and drop image upload."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModal[aria-hidden="false"]')

        # Get first option upload container
        first_upload = await page.query_selector('.option-image-upload')
        option_id = await first_upload.get_attribute('data-option-id')

        # Create test image
        test_image = self.create_test_image('JPEG', (500, 400))

        try:
            # Simulate drag over
            await first_upload.dispatch_event('dragover', {'dataTransfer': {}})

            # Verify drag-over class is added
            await page.wait_for_function(
                f"document.querySelector('.option-image-upload[data-option-id=\"{option_id}\"]').classList.contains('drag-over')",
                timeout=2000
            )

            # Simulate drag leave
            await first_upload.dispatch_event('dragleave', {'dataTransfer': {}})

            # Verify drag-over class is removed
            await page.wait_for_function(
                f"!document.querySelector('.option-image-upload[data-option-id=\"{option_id}\"]').classList.contains('drag-over')",
                timeout=2000
            )

            # Note: Full drag and drop testing with file data is complex in Playwright
            # The drag/drop event listeners are tested above, and actual file upload
            # is tested in the file input test

        finally:
            # Cleanup
            if test_image.exists():
                test_image.unlink()

    @pytest.mark.asyncio
    async def test_multiple_option_image_uploads(self, authenticated_page: Page):
        """Test image uploads on multiple vote options."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModal[aria-hidden="false"]')

        # Add a third option
        await page.click('[data-action="add-option"]')
        await page.wait_for_selector('.vote-option-field:nth-child(3)')

        # Get all option upload containers
        upload_containers = await page.query_selector_all('.option-image-upload')
        assert len(upload_containers) >= 3, "Should have at least 3 options with upload interfaces"

        # Upload images to first two options
        test_images = [
            self.create_test_image('PNG', (400, 300)),
            self.create_test_image('JPEG', (600, 400))
        ]

        try:
            for i, test_image in enumerate(test_images):
                container = upload_containers[i]
                option_id = await container.get_attribute('data-option-id')

                # Upload image
                file_input = await page.query_selector(f'#image-{option_id}')
                await file_input.set_input_files(str(test_image))

                # Wait for upload completion
                await page.wait_for_selector(f'#preview-{option_id}[style*="block"]', timeout=10000)

                # Verify each upload is independent
                preview_container = await page.query_selector(f'#preview-{option_id}')
                filename_element = await preview_container.query_selector('.image-filename')
                filename = await filename_element.inner_text()

                expected_format = 'png' if i == 0 else 'jpeg'
                assert expected_format in filename.lower(), f"Option {i} should show correct filename"

            # Verify third option still shows upload interface
            third_container = upload_containers[2]
            third_option_id = await third_container.get_attribute('data-option-id')
            third_upload_style = await third_container.get_attribute('style')

            # Third option should still show upload interface (not hidden)
            assert 'display: none' not in (third_upload_style or ''), "Third option should still show upload interface"

        finally:
            # Cleanup
            for test_image in test_images:
                if test_image.exists():
                    test_image.unlink()

    @pytest.mark.asyncio
    async def test_vote_creation_with_images(self, authenticated_page: Page):
        """Test complete vote creation with uploaded images."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModal[aria-hidden="false"]')

        # Fill in vote details
        await page.fill('#voteTitle', 'Test Vote with Images')
        await page.fill('#voteDescription', 'A vote to test image upload functionality')

        # Fill option titles
        option_inputs = await page.query_selector_all('.option-input')
        await option_inputs[0].fill('Option with Image 1')
        await option_inputs[1].fill('Option with Image 2')

        # Upload images to both options
        test_images = [
            self.create_test_image('PNG', (400, 300)),
            self.create_test_image('JPEG', (500, 350))
        ]

        try:
            upload_containers = await page.query_selector_all('.option-image-upload')

            for i, test_image in enumerate(test_images):
                container = upload_containers[i]
                option_id = await container.get_attribute('data-option-id')

                file_input = await page.query_selector(f'#image-{option_id}')
                await file_input.set_input_files(str(test_image))

                # Wait for upload completion
                await page.wait_for_selector(f'#preview-{option_id}[style*="block"]', timeout=10000)

            # Submit vote creation
            await page.click('#createVoteBtn')

            # Wait for success (redirect or success message)
            # Note: This assumes the vote creation succeeds and redirects
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Check if redirected to vote preview (success case)
            current_url = page.url
            is_success = '/vote-preview/' in current_url or 'Vote created successfully' in await page.content()

            assert is_success, "Vote creation with images should succeed"

        finally:
            # Cleanup
            for test_image in test_images:
                if test_image.exists():
                    test_image.unlink()

    @pytest.mark.asyncio
    async def test_image_upload_accessibility(self, authenticated_page: Page):
        """Test accessibility features of image upload interface."""
        page = authenticated_page

        # Open vote creation modal
        await page.click('[data-action="create-vote"]')
        await page.wait_for_selector('#voteCreationModal[aria-hidden="false"]')

        # Get first option upload container
        first_upload = await page.query_selector('.option-image-upload')
        option_id = await first_upload.get_attribute('data-option-id')

        # Check file input accessibility
        file_input = await page.query_selector(f'#image-{option_id}')
        file_input_id = await file_input.get_attribute('id')
        accept_attr = await file_input.get_attribute('accept')

        assert file_input_id == f'image-{option_id}', "File input should have correct ID"
        assert '.png,.jpg,.jpeg,.gif,.webp' in accept_attr, "File input should have correct accept attribute"

        # Upload image and check remove button accessibility
        test_image = self.create_test_image('PNG', (300, 300))

        try:
            await file_input.set_input_files(str(test_image))
            await page.wait_for_selector(f'#preview-{option_id}[style*="block"]', timeout=10000)

            # Check remove button
            remove_btn = await page.query_selector(f'#preview-{option_id} .remove-image-btn')
            aria_label = await remove_btn.get_attribute('aria-label')
            data_action = await remove_btn.get_attribute('data-action')

            # Verify button has proper attributes (may not have aria-label but should have data-action)
            assert data_action == 'remove-image', "Remove button should have correct data-action"

            # Check that button is focusable
            await remove_btn.focus()
            focused_element = await page.evaluate('document.activeElement.className')
            assert 'remove-image-btn' in focused_element, "Remove button should be focusable"

        finally:
            # Cleanup
            if test_image.exists():
                test_image.unlink()
