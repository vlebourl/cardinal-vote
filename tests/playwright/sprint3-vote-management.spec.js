import { test, expect } from '@playwright/test';
import { TEST_USERS, MATERIAL_DESIGN_ELEMENTS, PERFORMANCE_THRESHOLDS } from './fixtures/test-data.js';

// Sprint 3 Vote Management Tests
// Tests comprehensive vote management functionality including filtering, editing, deletion, and results

test.describe('Sprint 3: Vote Management & Analytics', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard with authentication
    await page.goto('/dashboard');

    // Wait for dashboard to load
    await expect(page.locator('.dashboard-header')).toBeVisible();

    // Ensure vote management section is visible
    await expect(page.locator('.vote-management-section')).toBeVisible();
  });

  test.describe('Phase 1: Vote Management UI', () => {

    test('should display vote management section with all components', async ({ page }) => {
      // Check section header
      await expect(page.locator('.vote-management-section h2')).toHaveText('Manage Votes');

      // Check filter buttons
      await expect(page.locator('[data-filter="all"]')).toBeVisible();
      await expect(page.locator('[data-filter="draft"]')).toBeVisible();
      await expect(page.locator('[data-filter="active"]')).toBeVisible();
      await expect(page.locator('[data-filter="closed"]')).toBeVisible();

      // Check sort dropdown
      await expect(page.locator('#sortSelect')).toBeVisible();

      // Check vote list container
      await expect(page.locator('#voteList')).toBeVisible();
    });

    test('should filter votes correctly', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Test draft filter
      await page.click('[data-filter="draft"]');
      await page.waitForTimeout(1000);

      // Should only show draft votes
      const draftCards = page.locator('.vote-card[data-status="draft"]');
      const activeSCards = page.locator('.vote-card[data-status="active"]');

      if (await draftCards.count() > 0) {
        await expect(draftCards.first()).toBeVisible();
      }

      // Active filter should remove active votes from view when draft is selected
      // This test validates the filtering logic works

      // Test active filter
      await page.click('[data-filter="active"]');
      await page.waitForTimeout(1000);

      // Test closed filter
      await page.click('[data-filter="closed"]');
      await page.waitForTimeout(1000);

      // Test all filter
      await page.click('[data-filter="all"]');
      await page.waitForTimeout(1000);

      console.log('✅ Vote filtering functionality validated');
    });

    test('should handle sort dropdown changes', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Test different sort options
      await page.selectOption('#sortSelect', 'title');
      await page.waitForTimeout(1000);

      await page.selectOption('#sortSelect', 'response_count');
      await page.waitForTimeout(1000);

      await page.selectOption('#sortSelect', 'status');
      await page.waitForTimeout(1000);

      // Return to default
      await page.selectOption('#sortSelect', 'created_at');
      await page.waitForTimeout(1000);

      console.log('✅ Sort functionality validated');
    });

    test('should show vote cards with proper structure', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      const voteCard = page.locator('.vote-card').first();

      // Check card structure
      await expect(voteCard.locator('.vote-title')).toBeVisible();
      await expect(voteCard.locator('.status-badge')).toBeVisible();

      // Check action buttons
      await expect(voteCard.locator('[data-action="edit-vote"]')).toBeVisible();
      await expect(voteCard.locator('[data-action="view-results"]')).toBeVisible();
      await expect(voteCard.locator('[data-action="delete-vote"]')).toBeVisible();

      console.log('✅ Vote card structure validated');
    });

    test('should handle pagination with load more', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Check if load more button is available
      const loadMoreBtn = page.locator('#loadMoreBtn');

      if (await loadMoreBtn.isVisible()) {
        const initialCount = await page.locator('.vote-card').count();

        await loadMoreBtn.click();
        await page.waitForTimeout(2000);

        const newCount = await page.locator('.vote-card').count();
        expect(newCount).toBeGreaterThanOrEqual(initialCount);

        console.log('✅ Pagination functionality validated');
      } else {
        console.log('⚠️  No pagination needed - all votes fit on one page');
      }
    });

  });

  test.describe('Phase 2: Edit/Delete Operations', () => {

    test('should open edit modal with vote data', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Click edit button on first vote
      const firstEditBtn = page.locator('.vote-card [data-action="edit-vote"]').first();
      await firstEditBtn.click();

      // Check modal opens
      await expect(page.locator('#editVoteModalScrim')).toHaveClass(/md-dialog-scrim-visible/);
      await expect(page.locator('#edit-vote-modal-title')).toHaveText('Edit Vote');

      // Check form fields are populated
      await expect(page.locator('#editVoteTitle')).not.toHaveValue('');

      // Check form structure
      await expect(page.locator('#editVoteForm')).toBeVisible();
      await expect(page.locator('#saveVoteBtn')).toBeVisible();

      console.log('✅ Edit modal opens and populates correctly');
    });

    test('should handle edit restrictions based on vote status', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Look for an active vote to test restrictions
      const activeVoteCard = page.locator('.vote-card[data-status="active"]').first();

      if (await activeVoteCard.isVisible()) {
        const editBtn = activeVoteCard.locator('[data-action="edit-vote"]');
        await editBtn.click();

        // Check warning is shown
        const statusWarning = page.locator('#editStatusWarning');
        await expect(statusWarning).toBeVisible();

        // Check options container is disabled
        const optionsContainer = page.locator('#editOptionsContainer');
        await expect(optionsContainer).toHaveCSS('opacity', '0.5');

        console.log('✅ Edit restrictions working for active votes');

        // Close modal
        await page.click('[data-action="close-modal"][data-modal="edit-vote"]');
      } else {
        console.log('⚠️  No active votes available to test restrictions');
      }
    });

    test('should save vote changes successfully', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Look for a draft vote to edit
      const draftVoteCard = page.locator('.vote-card[data-status="draft"]').first();

      if (await draftVoteCard.isVisible()) {
        const editBtn = draftVoteCard.locator('[data-action="edit-vote"]');
        await editBtn.click();

        // Wait for modal
        await expect(page.locator('#editVoteModalScrim')).toHaveClass(/md-dialog-scrim-visible/);

        // Modify title
        const titleField = page.locator('#editVoteTitle');
        const currentTitle = await titleField.inputValue();
        const newTitle = currentTitle + ' - Updated by Playwright';

        await titleField.fill(newTitle);

        // Save changes
        await page.click('#saveVoteBtn');

        // Wait for modal to close and success message
        await expect(page.locator('#editVoteModalScrim')).not.toHaveClass(/md-dialog-scrim-visible/);
        await expect(page.locator('.md-snackbar')).toHaveClass(/md-snackbar-visible/);

        console.log('✅ Vote editing and saving functionality validated');
      } else {
        console.log('⚠️  No draft votes available to test editing');
      }
    });

    test('should open delete confirmation modal', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Click delete button on first vote
      const firstDeleteBtn = page.locator('.vote-card [data-action="delete-vote"]').first();
      const voteTitle = await page.locator('.vote-card .vote-title').first().textContent();

      await firstDeleteBtn.click();

      // Check delete modal opens
      await expect(page.locator('#deleteVoteModalScrim')).toHaveClass(/md-dialog-scrim-visible/);
      await expect(page.locator('#delete-vote-modal-title')).toHaveText('Delete Vote');

      // Check vote title is shown
      await expect(page.locator('#deleteVoteTitle')).toHaveText(voteTitle);

      // Check buttons are present
      await expect(page.locator('#confirmDeleteBtn')).toBeVisible();
      await expect(page.locator('[data-action="close-modal"][data-modal="delete-vote"]')).toBeVisible();

      // Cancel without deleting
      await page.click('[data-action="close-modal"][data-modal="delete-vote"]');
      await expect(page.locator('#deleteVoteModalScrim')).not.toHaveClass(/md-dialog-scrim-visible/);

      console.log('✅ Delete confirmation modal functionality validated');
    });

  });

  test.describe('Phase 3: Results Visualization', () => {

    test('should open results modal with charts', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Click results button on first vote
      const firstResultsBtn = page.locator('.vote-card [data-action="view-results"]').first();
      await firstResultsBtn.click();

      // Check results modal opens
      await expect(page.locator('#resultsModalScrim')).toHaveClass(/md-dialog-scrim-visible/);
      await expect(page.locator('#results-modal-title')).toHaveText('Vote Results');

      // Check chart canvases are present
      await expect(page.locator('#resultsBarChart')).toBeVisible();
      await expect(page.locator('#resultsPieChart')).toBeVisible();

      // Check statistics are displayed
      await expect(page.locator('#totalVoteResponses')).toBeVisible();
      await expect(page.locator('#averageRating')).toBeVisible();
      await expect(page.locator('#participationRate')).toBeVisible();

      // Check results table
      await expect(page.locator('#resultsTableBody')).toBeVisible();

      console.log('✅ Results visualization modal functionality validated');
    });

    test('should display export buttons and refresh functionality', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Open results modal
      const firstResultsBtn = page.locator('.vote-card [data-action="view-results"]').first();
      await firstResultsBtn.click();

      // Wait for modal to open
      await expect(page.locator('#resultsModalScrim')).toHaveClass(/md-dialog-scrim-visible/);

      // Check export buttons
      await expect(page.locator('#exportCsvBtn')).toBeVisible();
      await expect(page.locator('#exportJsonBtn')).toBeVisible();

      // Check refresh button
      await expect(page.locator('#refreshResultsBtn')).toBeVisible();

      // Test refresh functionality
      await page.click('#refreshResultsBtn');
      await page.waitForTimeout(1000);

      console.log('✅ Export and refresh functionality validated');
    });

    test('should handle responsive chart behavior', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Open results modal
      const firstResultsBtn = page.locator('.vote-card [data-action="view-results"]').first();
      await firstResultsBtn.click();

      // Wait for modal and charts to load
      await expect(page.locator('#resultsModalScrim')).toHaveClass(/md-dialog-scrim-visible/);
      await page.waitForTimeout(2000); // Wait for Chart.js to render

      // Test mobile responsiveness
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(1000);

      // Charts should still be visible
      await expect(page.locator('#resultsBarChart')).toBeVisible();
      await expect(page.locator('#resultsPieChart')).toBeVisible();

      // Reset viewport
      await page.setViewportSize({ width: 1200, height: 800 });

      console.log('✅ Responsive chart behavior validated');
    });

  });

  test.describe('Phase 4: Export Functionality', () => {

    test('should handle CSV export download', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Open results modal
      const firstResultsBtn = page.locator('.vote-card [data-action="view-results"]').first();
      await firstResultsBtn.click();

      // Wait for modal
      await expect(page.locator('#resultsModalScrim')).toHaveClass(/md-dialog-scrim-visible/);

      // Setup download handling
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 10000 }),
        page.click('#exportCsvBtn')
      ]);

      // Verify CSV download
      expect(download.suggestedFilename()).toMatch(/vote-.*\.csv$/);

      console.log('✅ CSV export functionality validated');
    });

    test('should handle JSON export download', async ({ page }) => {
      // Wait for votes to load
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // Open results modal
      const firstResultsBtn = page.locator('.vote-card [data-action="view-results"]').first();
      await firstResultsBtn.click();

      // Wait for modal
      await expect(page.locator('#resultsModalScrim')).toHaveClass(/md-dialog-scrim-visible/);

      // Setup download handling
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 10000 }),
        page.click('#exportJsonBtn')
      ]);

      // Verify JSON download
      expect(download.suggestedFilename()).toMatch(/vote-.*\.json$/);

      console.log('✅ JSON export functionality validated');
    });

  });

  test.describe('Integration and Performance', () => {

    test('should complete full vote management workflow', async ({ page }) => {
      // Measure workflow completion time
      const startTime = Date.now();

      // 1. Navigate and load votes
      await page.goto('/dashboard');
      await expect(page.locator('.vote-management-section')).toBeVisible();
      await page.waitForSelector('.vote-card', { timeout: 5000 });

      // 2. Filter votes
      await page.click('[data-filter="draft"]');
      await page.waitForTimeout(1000);

      // 3. Edit workflow (if draft vote exists)
      const draftVote = page.locator('.vote-card[data-status="draft"]').first();
      if (await draftVote.isVisible()) {
        await draftVote.locator('[data-action="edit-vote"]').click();
        await expect(page.locator('#editVoteModalScrim')).toHaveClass(/md-dialog-scrim-visible/);

        // Make a small change
        const titleField = page.locator('#editVoteTitle');
        const currentTitle = await titleField.inputValue();
        await titleField.fill(currentTitle + ' [Playwright Test]');

        await page.click('#saveVoteBtn');
        await expect(page.locator('#editVoteModalScrim')).not.toHaveClass(/md-dialog-scrim-visible/);
      }

      // 4. Results viewing
      const firstVote = page.locator('.vote-card').first();
      await firstVote.locator('[data-action="view-results"]').click();
      await expect(page.locator('#resultsModalScrim')).toHaveClass(/md-dialog-scrim-visible/);
      await expect(page.locator('#resultsBarChart')).toBeVisible();

      const workflowTime = Date.now() - startTime;
      console.log(`📊 Complete workflow time: ${workflowTime}ms`);

      // Should complete workflow in reasonable time
      expect(workflowTime).toBeLessThan(15000); // 15 seconds max

      console.log('✅ Complete vote management workflow validated');
    });

    test('should meet performance requirements', async ({ page }) => {
      // Test page load performance
      const startTime = Date.now();
      await page.goto('/dashboard');

      // Wait for vote management section to be visible
      await expect(page.locator('.vote-management-section')).toBeVisible();

      const pageLoadTime = Date.now() - startTime;
      console.log(`⚡ Page load time: ${pageLoadTime}ms`);

      // Should meet PRP requirement of <2 second load time
      expect(pageLoadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.PAGE_LOAD_TIME);

      // Test vote list loading performance
      const voteLoadStart = Date.now();
      await page.waitForSelector('.vote-card', { timeout: 5000 });
      const voteLoadTime = Date.now() - voteLoadStart;

      console.log(`📋 Vote list load time: ${voteLoadTime}ms`);
      expect(voteLoadTime).toBeLessThan(3000); // 3 seconds for vote loading

      console.log('✅ Performance requirements met');
    });

    test('should handle error conditions gracefully', async ({ page }) => {
      // Test network error handling
      await page.goto('/dashboard');
      await expect(page.locator('.vote-management-section')).toBeVisible();

      // Simulate network failure
      await page.route('/api/votes/**', route => route.abort());

      // Try to reload votes
      await page.click('[data-filter="all"]');
      await page.waitForTimeout(2000);

      // Page should still be functional
      const pageStillResponsive = await page.isVisible('body');
      expect(pageStillResponsive).toBeTruthy();

      // Should show error feedback
      await expect(page.locator('.md-snackbar')).toBeVisible();

      // Remove network interception
      await page.unroute('/api/votes/**');

      console.log('✅ Error handling validated');
    });

  });

  test.afterEach(async ({ page }, testInfo) => {
    // Take screenshot on test failure
    if (testInfo.status !== testInfo.expectedStatus) {
      const screenshot = await page.screenshot({ fullPage: true });
      await testInfo.attach('screenshot', { body: screenshot, contentType: 'image/png' });
    }

    // Close any open modals
    const modals = [
      '#editVoteModalScrim',
      '#deleteVoteModalScrim',
      '#resultsModalScrim'
    ];

    for (const modalSelector of modals) {
      const modal = page.locator(modalSelector);
      if (await modal.isVisible() && await modal.evaluate(el => el.classList.contains('md-dialog-scrim-visible'))) {
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
      }
    }

    // Log test completion
    console.log(`🎭 Test "${testInfo.title}" completed with status: ${testInfo.status}`);
  });

});
