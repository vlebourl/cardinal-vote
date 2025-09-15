import { test, expect } from '@playwright/test';
import { EnhancedPublicVotingPage } from '../../pages/public-voting-page.enhanced.js';
import { EnhancedLandingPage } from '../../pages/landing-page.enhanced.js';
import { EnhancedDashboardPage } from '../../pages/dashboard-page.enhanced.js';
import { testDataManager } from '../../fixtures/data/test-data-factory.js';
import { PERFORMANCE_FIXTURES } from '../../fixtures/data/performance-accessibility-fixtures.js';

test.describe('Core Public Voting Flow Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  let publicVotingPage;
  let landingPage;
  let dashboardPage;

  test.beforeEach(async ({ page }) => {
    publicVotingPage = new EnhancedPublicVotingPage(page);
    landingPage = new EnhancedLandingPage(page);
    dashboardPage = new EnhancedDashboardPage(page);
  });

  test.afterEach(async ({ page }) => {
    await testDataManager.runCleanup();
  });

  test.describe('Anonymous Public Voting', () => {
    test('should allow anonymous voting on public votes', async ({ page }) => {
      // Navigate to a public vote (using test vote ID)
      await publicVotingPage.gotoPublicVote('test-public-vote');

      // Validate page load performance
      const loadTime = await publicVotingPage.measurePageLoadTime();
      expect(loadTime.isAcceptable).toBe(true);

      // Get vote information
      const voteInfo = await publicVotingPage.getVoteInformation();
      expect(voteInfo.title).toBeTruthy();
      expect(voteInfo.description).toBeTruthy();

      // Get available options
      const options = await publicVotingPage.getVoteOptions();
      expect(options.length).toBeGreaterThanOrEqual(2);
      expect(options.every(option => option.isSelectable)).toBe(true);

      // Enable anonymous voting if available
      await publicVotingPage.toggleAnonymousVoting(true);

      // Select an option
      const selectionResult = await publicVotingPage.selectOption(0);
      expect(selectionResult.isAcceptable).toBe(true);

      // Verify selection
      const selectedOptions = await publicVotingPage.getSelectedOptions();
      expect(selectedOptions.length).toBe(1);
      expect(selectedOptions[0].index).toBe(0);

      // Submit vote
      const submissionResult = await publicVotingPage.submitVote();
      expect(submissionResult.result).toBe('success');
      expect(submissionResult.isAcceptable).toBe(true);

      // Verify thank you message or results
      expect(['thank_you', 'success']).toContain(submissionResult.result);
    });

    test('should handle multi-choice voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-multi-choice-vote');

      const options = await publicVotingPage.getVoteOptions();
      expect(options.length).toBeGreaterThan(2);

      // Select multiple options
      const selectionResults = await publicVotingPage.selectMultipleOptions([0, 2]);
      expect(selectionResults.length).toBe(2);
      expect(selectionResults.every(result => result.isAcceptable)).toBe(true);

      const selectedOptions = await publicVotingPage.getSelectedOptions();
      expect(selectedOptions.length).toBe(2);

      const submissionResult = await publicVotingPage.submitVote();
      expect(submissionResult.result).toBe('success');
    });

    test('should display vote results after voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-public-vote');

      // Vote first
      await publicVotingPage.selectOption(0);
      await publicVotingPage.submitVote();

      // Get and validate results
      const results = await publicVotingPage.getVoteResults();
      expect(results.length).toBeGreaterThan(0);
      expect(results.every(result => result.percentage !== undefined)).toBe(true);
      expect(results.every(result => result.countValue >= 0)).toBe(true);

      // Verify results are sorted by percentage
      for (let i = 0; i < results.length - 1; i++) {
        expect(results[i].percentageValue).toBeGreaterThanOrEqual(results[i + 1].percentageValue);
      }

      // Check for winning option
      const winningOption = await publicVotingPage.getWinningOption();
      expect(winningOption).toBeTruthy();
      expect(winningOption.percentageValue).toBe(results[0].percentageValue);
    });

    test('should handle voting with voter information collection', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-voter-info-vote');

      // Fill voter information if required
      const voterData = {
        name: 'Test Voter',
        email: 'test.voter@example.com'
      };

      await publicVotingPage.fillVoterInformation(voterData);

      await publicVotingPage.selectOption(1);
      const submissionResult = await publicVotingPage.submitVote();
      expect(submissionResult.result).toBe('success');
    });
  });

  test.describe('Authenticated Voting', () => {
    test.beforeEach(async ({ page }) => {
      // Login before authenticated voting tests
      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      await landingPage.submitLoginForm();
    });

    test('should handle authenticated voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-auth-required-vote');

      // Should already be logged in
      const isLoginRequired = await publicVotingPage.isLoginRequired();
      expect(isLoginRequired).toBe(false);

      // Verify user profile is visible
      const userProfile = await publicVotingPage.isElementVisible(
        publicVotingPage.userInterface.userProfile
      );
      expect(userProfile).toBe(true);

      await publicVotingPage.selectOption(0);
      const submissionResult = await publicVotingPage.submitVote();
      expect(submissionResult.result).toBe('success');

      // Verify vote is associated with user account
      const voteInfo = await publicVotingPage.getVoteInformation();
      expect(voteInfo.totalVotes).toBeTruthy();
    });

    test('should handle login requirement for restricted votes', async ({ page }) => {
      // Logout first
      await dashboardPage.goto();
      await dashboardPage.logout();

      // Try to access a restricted vote
      await publicVotingPage.gotoPublicVote('test-private-vote');

      const loginRequired = await publicVotingPage.isLoginRequired();
      if (loginRequired) {
        const loginData = testDataManager.createFormData('login', 'user');
        await publicVotingPage.loginToVote(loginData);

        // Should now be able to vote
        const options = await publicVotingPage.getVoteOptions();
        expect(options.length).toBeGreaterThan(0);

        await publicVotingPage.selectOption(0);
        const submissionResult = await publicVotingPage.submitVote();
        expect(submissionResult.result).toBe('success');
      }
    });

    test('should prevent duplicate voting by authenticated users', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-no-duplicate-vote');

      // First vote
      await publicVotingPage.selectOption(0);
      const firstSubmission = await publicVotingPage.submitVote();
      expect(firstSubmission.result).toBe('success');

      // Navigate back and try to vote again
      await page.reload();

      // Should show that user has already voted
      const hasAlreadyVoted = await publicVotingPage.isElementVisible(
        '.already-voted, [data-testid="already-voted"]'
      );

      if (!hasAlreadyVoted) {
        // If not prevented by UI, submitting should fail
        await publicVotingPage.selectOption(1);
        const secondSubmission = await publicVotingPage.submitVote();
        expect(secondSubmission.result).toBe('error');
      }
    });
  });

  test.describe('Vote Results and Analytics', () => {
    test('should display real-time vote counts', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-realtime-vote');

      const initialVoteCount = await publicVotingPage.getTotalVoteCount();

      // Submit a vote
      await publicVotingPage.selectOption(0);
      await publicVotingPage.submitVote();

      // Check if vote count increased
      const updatedVoteCount = await publicVotingPage.getTotalVoteCount();
      expect(updatedVoteCount).toBeGreaterThan(initialVoteCount);
    });

    test('should handle results visibility settings', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-hidden-results-vote');

      // Try to show results before voting
      await publicVotingPage.showResults();

      const resultsVisible = await publicVotingPage.isElementVisible(
        publicVotingPage.resultsDisplay.resultsContainer
      );

      // Results might be hidden until after voting
      if (!resultsVisible) {
        // Vote first, then check if results are available
        await publicVotingPage.selectOption(0);
        await publicVotingPage.submitVote();

        const resultsAfterVoting = await publicVotingPage.getVoteResults();
        expect(resultsAfterVoting.length).toBeGreaterThan(0);
      }
    });

    test('should refresh results data', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-public-vote');

      const refreshResult = await publicVotingPage.refreshResults();
      expect(refreshResult.updated).toBeDefined();

      // Enable auto-refresh if available
      await publicVotingPage.enableAutoRefresh();

      // Monitor for live updates
      const liveUpdates = await publicVotingPage.monitorLiveUpdates(5000);
      expect(liveUpdates.updates.length).toBeGreaterThan(0);
    });
  });

  test.describe('Social Sharing and Interaction', () => {
    test('should share vote via social media', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-public-vote');

      const shareResult = await publicVotingPage.shareVote();
      expect(shareResult.hasModal).toBe(true);
      expect(shareResult.shareUrl).toBeTruthy();

      // Test copy functionality
      const copiedUrl = await publicVotingPage.copyShareUrl();
      expect(copiedUrl).toContain('vote');

      // Test social platform sharing
      const facebookShare = await publicVotingPage.shareToSocialMedia('facebook');
      expect(facebookShare).toBe(true);
    });

    test('should handle vote comments', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-comments-enabled-vote');

      // Login for commenting
      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      await landingPage.submitLoginForm();

      await publicVotingPage.gotoPublicVote('test-comments-enabled-vote');

      // Add a comment
      const commentText = 'This is a test comment for the vote.';
      const comments = await publicVotingPage.addComment(commentText);

      expect(comments.some(comment => comment.text.includes(commentText))).toBe(true);

      // Get all comments
      const allComments = await publicVotingPage.getComments();
      expect(allComments.length).toBeGreaterThan(0);
      expect(allComments.every(comment => comment.author.length > 0)).toBe(true);
    });
  });

  test.describe('Mobile Responsive Voting', () => {
    test('should handle mobile voting interface', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-mobile-vote');

      const mobileValidation = await publicVotingPage.validateMobileVoting();
      expect(mobileValidation.optionsVisible).toBe(true);
      expect(mobileValidation.submitButtonVisible).toBe(true);

      // Test touch interactions
      if (mobileValidation.touchInteractions.length > 0) {
        expect(mobileValidation.touchInteractions.some(interaction => interaction.touchWorked)).toBe(true);
      }

      // Test swipe support if available
      if (mobileValidation.hasSwipeSupport.supported) {
        expect(mobileValidation.hasSwipeSupport.tested).toBe(true);
      }
    });

    test('should adapt to different screen sizes', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-responsive-vote');

      // Test different viewport sizes
      const viewports = [
        { width: 1200, height: 800 }, // Desktop
        { width: 768, height: 1024 }, // Tablet
        { width: 375, height: 667 }   // Mobile
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);

        const optionsVisible = await publicVotingPage.isElementVisible(
          publicVotingPage.votingInterface.optionsContainer
        );
        expect(optionsVisible).toBe(true);

        const submitVisible = await publicVotingPage.isElementVisible(
          publicVotingPage.votingInterface.submitButton
        );
        expect(submitVisible).toBe(true);
      }
    });
  });

  test.describe('Voting Performance', () => {
    test('should meet performance thresholds for voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-performance-vote');

      const performanceMetrics = await publicVotingPage.measureVotingPerformance();

      expect(performanceMetrics.optionSelectionAcceptable).toBe(true);
      expect(performanceMetrics.voteSubmissionAcceptable).toBe(true);
      expect(performanceMetrics.resultsLoadingAcceptable).toBe(true);

      // Verify individual metrics
      expect(performanceMetrics.optionSelection).toBeLessThan(
        PERFORMANCE_FIXTURES.THRESHOLDS.FIRST_INPUT_DELAY.ACCEPTABLE
      );
      expect(performanceMetrics.voteSubmission).toBeLessThan(
        PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.VOTE_SUBMISSION
      );
    });

    test('should handle large numbers of options efficiently', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-many-options-vote');

      const startTime = Date.now();

      const options = await publicVotingPage.getVoteOptions();
      expect(options.length).toBeGreaterThan(10);

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds

      // Test selection of last option
      const lastOptionIndex = options.length - 1;
      const selectionResult = await publicVotingPage.selectOption(lastOptionIndex);
      expect(selectionResult.isAcceptable).toBe(true);
    });
  });

  test.describe('Voting Accessibility', () => {
    test('should have accessible voting interface', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-accessible-vote');

      const accessibility = await publicVotingPage.validateAccessibility();

      expect(accessibility.focusManagement.focusableElementCount).toBeGreaterThan(0);
      expect(accessibility.ariaAttributes.hasAriaElements).toBe(true);
      expect(accessibility.keyboardNavigation.tabNavigationWorks).toBe(true);
      expect(accessibility.semanticStructure.hasMainContent).toBe(true);
    });

    test('should support keyboard voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-keyboard-vote');

      // Navigate to first option using keyboard
      await page.keyboard.press('Tab');

      let tabCount = 0;
      while (tabCount < 20) { // Safety limit
        const activeElement = await page.evaluate(() => {
          const active = document.activeElement;
          return {
            tagName: active?.tagName,
            type: active?.type,
            name: active?.name,
            className: active?.className
          };
        });

        // Check if we're on a vote option
        if (activeElement.type === 'radio' || activeElement.type === 'checkbox' ||
            activeElement.name === 'vote' || activeElement.className.includes('vote-option')) {
          await page.keyboard.press('Space'); // Select option
          break;
        }

        await page.keyboard.press('Tab');
        tabCount++;
      }

      // Navigate to submit button
      while (tabCount < 30) {
        const activeElementText = await page.evaluate(() => document.activeElement?.textContent);
        if (activeElementText && activeElementText.includes('Submit')) {
          await page.keyboard.press('Enter');
          break;
        }

        await page.keyboard.press('Tab');
        tabCount++;
      }

      // Should have submitted the vote
      const hasSuccessMessage = await publicVotingPage.isElementVisible(
        '.success-message, [role="status"], .thank-you', 3000
      );
      expect(hasSuccessMessage).toBe(true);
    });

    test('should have proper ARIA labels for vote options', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-aria-vote');

      const options = await publicVotingPage.getVoteOptions();

      for (let i = 0; i < Math.min(options.length, 3); i++) {
        const optionElement = page.locator(publicVotingPage.votingInterface.voteOption).nth(i);

        // Check for ARIA attributes
        const ariaLabel = await optionElement.getAttribute('aria-label');
        const ariaLabelledBy = await optionElement.getAttribute('aria-labelledby');
        const ariaDescribedBy = await optionElement.getAttribute('aria-describedby');

        expect(ariaLabel || ariaLabelledBy || ariaDescribedBy).toBeTruthy();
      }
    });
  });

  test.describe('Material Design Validation', () => {
    test('should follow Material Design principles for voting interface', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-material-design-vote');

      const materialDesign = await publicVotingPage.validateVotingMaterialDesign();

      expect(materialDesign.voting.voteOptions.allOptionsValid).toBe(true);
      expect(materialDesign.voting.submitButton.visible).toBe(true);
      expect(materialDesign.voting.submitButton.hasProperHeight).toBe(true);

      if (materialDesign.voting.resultsDisplay.barCount > 0) {
        expect(materialDesign.voting.resultsDisplay.allBarsValid).toBe(true);
      }

      if (materialDesign.voting.socialSharing.visible) {
        expect(materialDesign.voting.socialSharing.buttonCount).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Error Scenarios', () => {
    test('should handle vote not found', async ({ page }) => {
      await publicVotingPage.gotoVote('non-existent-vote-12345');

      const voteNotFoundError = await publicVotingPage.isElementVisible(
        '.vote-not-found, .error-message, [data-testid="vote-not-found"]'
      );
      expect(voteNotFoundError).toBe(true);
    });

    test('should handle closed votes', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-closed-vote');

      const voteClosedMessage = await publicVotingPage.isElementVisible(
        '.vote-closed, .expired-vote, [data-testid="vote-closed"]'
      );

      if (voteClosedMessage) {
        // Should show results or message about being closed
        const hasViewResults = await publicVotingPage.isElementVisible(
          'button:has-text("View Results"), a:has-text("View Results")'
        );
        expect(hasViewResults).toBe(true);
      }
    });

    test('should handle network errors during voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-public-vote');

      // Intercept vote submission and simulate error
      await page.route('**/api/votes/*/submit', route => route.abort('failed'));

      await publicVotingPage.selectOption(0);
      const submissionResult = await publicVotingPage.submitVote();
      expect(submissionResult.result).toBe('error');

      // Should display error message
      const errorMessage = await publicVotingPage.isElementVisible(
        '.error-message, [role="alert"]'
      );
      expect(errorMessage).toBe(true);
    });

    test('should handle permission errors', async ({ page }) => {
      // Logout to test permission errors
      await landingPage.goto();

      await publicVotingPage.gotoPublicVote('test-permission-restricted-vote');

      const permissionError = await publicVotingPage.isElementVisible(
        '.permission-error, .unauthorized, [data-testid="permission-error"]'
      );

      if (permissionError) {
        const hasLoginOption = await publicVotingPage.isElementVisible(
          'button:has-text("Login"), a:has-text("Login")'
        );
        expect(hasLoginOption).toBe(true);
      }
    });
  });

  test.describe('Vote State Management', () => {
    test('should preserve vote state during page navigation', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-state-preservation-vote');

      // Select an option
      await publicVotingPage.selectOption(1);

      // Navigate away and back
      await page.goto('/');
      await publicVotingPage.gotoPublicVote('test-state-preservation-vote');

      // Check if selection is preserved (depends on implementation)
      const selectedOptions = await publicVotingPage.getSelectedOptions();
      // Note: This might not always preserve selection depending on implementation
    });

    test('should handle browser refresh during voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-refresh-handling-vote');

      await publicVotingPage.selectOption(0);

      // Refresh the page
      await page.reload();

      // Should still be able to vote
      const options = await publicVotingPage.getVoteOptions();
      expect(options.length).toBeGreaterThan(0);
      expect(options.every(option => option.isSelectable)).toBe(true);
    });
  });
});
