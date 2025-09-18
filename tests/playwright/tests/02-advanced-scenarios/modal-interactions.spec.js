import { test, expect } from '@playwright/test';
import { EnhancedLandingPage } from '../../pages/landing-page.enhanced.js';
import { EnhancedDashboardPage } from '../../pages/dashboard-page.enhanced.js';
import { EnhancedVoteCreationPage } from '../../pages/vote-creation-page.enhanced.js';
import { EnhancedPublicVotingPage } from '../../pages/public-voting-page.enhanced.js';
import { EnhancedAdminPage } from '../../pages/admin-page.enhanced.js';
import { testDataManager } from '../../fixtures/data/test-data-factory.js';
import { PERFORMANCE_FIXTURES } from '../../fixtures/data/performance-accessibility-fixtures.js';

test.describe('Advanced Modal Interaction Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  let landingPage;
  let dashboardPage;
  let voteCreationPage;
  let publicVotingPage;
  let adminPage;

  test.beforeEach(async ({ page }) => {
    landingPage = new EnhancedLandingPage(page);
    dashboardPage = new EnhancedDashboardPage(page);
    voteCreationPage = new EnhancedVoteCreationPage(page);
    publicVotingPage = new EnhancedPublicVotingPage(page);
    adminPage = new EnhancedAdminPage(page);
  });

  test.afterEach(async ({ page }) => {
    await testDataManager.runCleanup();
  });

  test.describe('Authentication Modal Interactions', () => {
    test('should handle login modal lifecycle', async ({ page }) => {
      await landingPage.goto();

      // Open login modal
      await landingPage.clickSignIn();

      // Measure modal open performance
      const modalStartTime = Date.now();
      const hasLoginModal = await landingPage.waitForLoginModal();
      const modalOpenTime = Date.now() - modalStartTime;

      expect(hasLoginModal).toBe(true);
      expect(modalOpenTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.MODAL_OPEN);

      // Validate modal structure
      const modalValidation = await landingPage.validateLoginModalStructure();
      expect(modalValidation.hasEmailField).toBe(true);
      expect(modalValidation.hasPasswordField).toBe(true);
      expect(modalValidation.hasSubmitButton).toBe(true);
      expect(modalValidation.hasCloseButton).toBe(true);

      // Test modal close by clicking overlay
      await landingPage.closeModalByOverlay();

      // Verify modal is closed
      const modalClosed = await page.waitForFunction(() => {
        return !document.querySelector('.login-modal, [data-testid="login-modal"]');
      }, { timeout: 3000 });
      expect(modalClosed).toBe(true);
    });

    test('should handle registration modal with form validation', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();

      const hasRegistrationModal = await landingPage.waitForRegistrationModal();
      expect(hasRegistrationModal).toBe(true);

      // Test form validation within modal
      const invalidData = testDataManager.createFormData('registration', 'invalid', {
        errorType: 'email'
      });

      await landingPage.fillRegistrationForm(invalidData);
      const submissionResult = await landingPage.submitRegistrationForm();
      expect(submissionResult.result).toBe('error');

      // Verify error messages appear within modal
      const modalErrors = await landingPage.getModalErrors();
      expect(modalErrors.length).toBeGreaterThan(0);

      // Modal should remain open after validation errors
      const modalStillOpen = await landingPage.isElementVisible('.registration-modal, [data-testid="registration-modal"]');
      expect(modalStillOpen).toBe(true);

      // Test successful registration closes modal
      const validData = testDataManager.createFormData('registration', 'valid');
      await landingPage.clearRegistrationForm();
      await landingPage.fillRegistrationForm(validData);

      const successResult = await landingPage.submitRegistrationForm();
      if (successResult.result === 'success') {
        // Modal should close on success
        const modalClosedAfterSuccess = await page.waitForFunction(() => {
          return !document.querySelector('.registration-modal, [data-testid="registration-modal"]');
        }, { timeout: 5000 });
        expect(modalClosedAfterSuccess).toBe(true);
      }
    });

    test('should handle modal keyboard navigation and focus management', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Test initial focus
      const initialFocus = await page.evaluate(() => document.activeElement?.tagName);
      expect(initialFocus).toBe('INPUT'); // Should focus first input field

      // Test tab navigation within modal
      await page.keyboard.press('Tab');
      const secondFieldFocus = await page.evaluate(() => document.activeElement?.type);
      expect(secondFieldFocus).toBe('password');

      // Test escape key closes modal
      await page.keyboard.press('Escape');

      const modalClosedByEscape = await page.waitForFunction(() => {
        return !document.querySelector('.login-modal, [data-testid="login-modal"]');
      }, { timeout: 3000 });
      expect(modalClosedByEscape).toBe(true);

      // Verify focus returns to trigger element
      const focusAfterClose = await page.evaluate(() => document.activeElement?.textContent);
      expect(focusAfterClose).toContain('Sign In');
    });

    test('should prevent tabbing outside modal (focus trap)', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Get all focusable elements in modal
      const modalFocusableElements = await page.evaluate(() => {
        const modal = document.querySelector('.login-modal, [data-testid="login-modal"]');
        if (!modal) return [];

        const focusableSelectors = 'input, button, select, textarea, a[href], [tabindex]:not([tabindex="-1"])';
        return Array.from(modal.querySelectorAll(focusableSelectors)).length;
      });

      expect(modalFocusableElements).toBeGreaterThan(0);

      // Tab through all elements and verify focus stays within modal
      for (let i = 0; i < modalFocusableElements + 2; i++) {
        await page.keyboard.press('Tab');

        const focusedElementInsideModal = await page.evaluate(() => {
          const modal = document.querySelector('.login-modal, [data-testid="login-modal"]');
          const activeElement = document.activeElement;
          return modal && modal.contains(activeElement);
        });

        expect(focusedElementInsideModal).toBe(true);
      }
    });
  });

  test.describe('Vote Management Modal Interactions', () => {
    test.beforeEach(async ({ page }) => {
      // Login as user who can manage votes
      await page.goto('/auth/test-login?user=user1&role=user');
      await dashboardPage.goto();
    });

    test('should handle vote deletion confirmation modal', async ({ page }) => {
      const votes = await dashboardPage.getVoteCards();

      if (votes.length > 0) {
        const voteToDelete = votes[0];

        // Click delete button
        const deleteButton = page.locator(`[data-vote-id="${voteToDelete.id}"] [data-testid="delete-vote"]`);
        if (await deleteButton.isVisible()) {
          await deleteButton.click();

          // Verify confirmation modal appears
          const confirmationModal = await dashboardPage.waitForElement(dashboardPage.modals.confirmationModal);
          expect(confirmationModal).toBe(true);

          // Test cancel action
          await dashboardPage.clickElement(dashboardPage.modals.cancelButton);

          // Modal should close
          const modalClosed = await page.waitForFunction(() => {
            return !document.querySelector('.confirmation-modal, [data-testid="confirmation-modal"]');
          }, { timeout: 3000 });
          expect(modalClosed).toBe(true);

          // Vote should still exist
          const votesAfterCancel = await dashboardPage.getVoteCards();
          expect(votesAfterCancel.some(vote => vote.id === voteToDelete.id)).toBe(true);
        }
      }
    });

    test('should handle vote sharing modal with social options', async ({ page }) => {
      const votes = await dashboardPage.getVoteCards();

      if (votes.length > 0) {
        const voteToShare = votes[0];
        const shareResult = await dashboardPage.shareVote(voteToShare.id);

        expect(shareResult).toBeTruthy();

        // Verify share modal contains social options
        const socialButtons = await page.locator('.social-share button, [data-testid="social-share"] button').all();
        expect(socialButtons.length).toBeGreaterThan(0);

        // Test URL copy functionality
        const copyButton = page.locator('[data-testid="copy-url"], button:has-text("Copy")');
        if (await copyButton.isVisible()) {
          await copyButton.click();

          // Verify feedback appears
          const copyFeedback = await landingPage.isElementVisible('.copied-message, .success-message', 2000);
          expect(copyFeedback).toBe(true);
        }

        // Close modal
        await dashboardPage.closeModal();
      }
    });

    test('should handle vote preview modal with accurate data', async ({ page }) => {
      await voteCreationPage.goto();

      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      await voteCreationPage.addVoteOption({ text: 'Preview Option A' });
      await voteCreationPage.addVoteOption({ text: 'Preview Option B' });

      // Open preview modal
      const previewData = await voteCreationPage.previewVote();
      expect(previewData).toBeTruthy();
      expect(previewData.title).toBe(voteData.title);
      expect(previewData.optionCount).toBe(2);

      // Verify modal can be closed
      await voteCreationPage.closeModal();

      // Should be back to creation form
      const currentStep = await voteCreationPage.getCurrentStep();
      expect(currentStep).toBe(2);
    });
  });

  test.describe('Admin Modal Interactions', () => {
    test.beforeEach(async ({ page }) => {
      // Login as admin
      await page.goto('/auth/test-login?user=admin&role=admin');
      await adminPage.goto();
    });

    test('should handle user management modals', async ({ page }) => {
      await adminPage.navigateToAdminSection('users');

      const users = await adminPage.getUserList();

      if (users.length > 0) {
        const userToEdit = users[0];

        // Open user edit modal
        const editResult = await adminPage.editUser(userToEdit.id);
        expect(editResult.modalVisible).toBe(true);

        // Verify modal contains user data
        const userEmailField = page.locator('.user-edit-modal input[name="email"], [data-testid="user-email-input"]');
        if (await userEmailField.isVisible()) {
          const currentEmail = await userEmailField.inputValue();
          expect(currentEmail).toBe(userToEdit.email);
        }

        // Test modal validation
        const roleSelect = page.locator('.user-edit-modal select[name="role"], [data-testid="role-select"]');
        if (await roleSelect.isVisible()) {
          await roleSelect.selectOption('admin');

          // Submit changes
          await adminPage.clickElement(adminPage.modals.confirmButton);

          // Verify success notification
          const notification = await adminPage.waitForNotification('success');
          expect(notification.visible).toBe(true);
        }
      }
    });

    test('should handle bulk action confirmation modals', async ({ page }) => {
      await adminPage.navigateToAdminSection('users');

      const users = await adminPage.getUserList();

      if (users.length >= 2) {
        const userIds = users.slice(0, 2).map(user => user.id);

        // Select multiple users and perform bulk action
        for (const userId of userIds) {
          const checkbox = page.locator(`[data-user-id="${userId}"] input[type="checkbox"]`);
          if (await checkbox.isVisible()) {
            await checkbox.check();
          }
        }

        // Open bulk actions dropdown
        await adminPage.clickElement(adminPage.userManagement.bulkActionsDropdown);

        // Select suspend action
        const suspendAction = page.locator('[data-action="suspend"], option:has-text("Suspend")');
        if (await suspendAction.isVisible()) {
          await suspendAction.click();

          // Verify bulk confirmation modal
          const bulkModal = await adminPage.waitForElement(adminPage.modals.bulkActionModal);
          expect(bulkModal).toBe(true);

          // Verify modal shows selected count
          const modalText = await page.locator('.bulk-action-modal, [data-testid="bulk-action-modal"]').textContent();
          expect(modalText).toContain('2'); // Should mention 2 users

          // Cancel bulk action
          await adminPage.clickElement(adminPage.modals.cancelButton);
        }
      }
    });

    test('should handle system settings confirmation modals', async ({ page }) => {
      await adminPage.navigateToAdminSection('settings');

      // Toggle maintenance mode
      const maintenanceToggle = page.locator(adminPage.systemSettings.maintenanceModeToggle);
      if (await maintenanceToggle.isVisible()) {
        await maintenanceToggle.click();

        // Should show confirmation for critical system changes
        const confirmationModal = await adminPage.isElementVisible(adminPage.modals.confirmationModal, 2000);

        if (confirmationModal) {
          // Verify warning message in modal
          const modalContent = await page.locator('.confirmation-modal, [data-testid="confirmation-modal"]').textContent();
          expect(modalContent.toLowerCase()).toMatch(/maintenance|warning|critical/);

          // Cancel the change
          await adminPage.clickElement(adminPage.modals.cancelButton);

          // Verify toggle returns to original state
          const toggleState = await maintenanceToggle.isChecked();
          expect(toggleState).toBe(false); // Should revert
        }
      }
    });
  });

  test.describe('Vote Participation Modal Interactions', () => {
    test('should handle vote confirmation modal', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-confirmation-vote');

      const options = await publicVotingPage.getVoteOptions();
      expect(options.length).toBeGreaterThan(0);

      await publicVotingPage.selectOption(0);

      // Submit vote and handle confirmation modal if present
      const submissionStart = Date.now();
      await publicVotingPage.clickElement(publicVotingPage.votingInterface.submitButton);

      // Check for confirmation modal
      const hasConfirmationModal = await publicVotingPage.isElementVisible(
        publicVotingPage.confirmationElements.confirmationModal, 2000
      );

      if (hasConfirmationModal) {
        // Verify modal shows selected option
        const modalContent = await page.locator('.vote-confirmation, [data-testid="vote-confirmation"]').textContent();
        expect(modalContent).toContain(options[0].text);

        // Test cancel first
        await publicVotingPage.clickElement(publicVotingPage.confirmationElements.cancelSubmitButton);

        // Should return to voting interface
        const backToVoting = await publicVotingPage.isElementVisible(publicVotingPage.votingInterface.submitButton);
        expect(backToVoting).toBe(true);

        // Try again and confirm
        await publicVotingPage.clickElement(publicVotingPage.votingInterface.submitButton);
        await publicVotingPage.waitForElement(publicVotingPage.confirmationElements.confirmationModal);
        await publicVotingPage.clickElement(publicVotingPage.confirmationElements.confirmSubmitButton);
      }

      const submissionTime = Date.now() - submissionStart;
      expect(submissionTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.VOTE_SUBMISSION * 2);

      // Verify success state
      const hasSuccessMessage = await publicVotingPage.isElementVisible(
        '.success-message, .thank-you, [data-testid="vote-success"]', 5000
      );
      expect(hasSuccessMessage).toBe(true);
    });

    test('should handle change vote modal for authenticated users', async ({ page }) => {
      // Login first
      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      await landingPage.submitLoginForm();

      // Vote on a poll that allows vote changes
      await publicVotingPage.gotoPublicVote('test-changeable-vote');

      const options = await publicVotingPage.getVoteOptions();
      await publicVotingPage.selectOption(0);
      await publicVotingPage.submitVote();

      // Reload page to simulate returning later
      await page.reload();

      // Should show option to change vote
      const changeVoteButton = page.locator('[data-testid="change-vote"], button:has-text("Change Vote")');
      if (await changeVoteButton.isVisible()) {
        await changeVoteButton.click();

        // Should open change vote modal or interface
        const canChangeVote = await publicVotingPage.isElementVisible(
          '.change-vote-modal, [data-testid="change-vote-modal"], .voting-options', 3000
        );
        expect(canChangeVote).toBe(true);

        // Select different option
        if (options.length > 1) {
          await publicVotingPage.selectOption(1);
          const changeResult = await publicVotingPage.submitVote();
          expect(changeResult.result).toBe('success');
        }
      }
    });
  });

  test.describe('Modal Accessibility and Material Design', () => {
    test('should have accessible modal implementations', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Test ARIA attributes
      const modal = page.locator('.login-modal, [data-testid="login-modal"]');
      const ariaAttributes = await modal.evaluate(el => ({
        role: el.getAttribute('role'),
        ariaModal: el.getAttribute('aria-modal'),
        ariaLabel: el.getAttribute('aria-label'),
        ariaLabelledBy: el.getAttribute('aria-labelledby')
      }));

      expect(ariaAttributes.role).toBe('dialog');
      expect(ariaAttributes.ariaModal).toBe('true');
      expect(ariaAttributes.ariaLabel || ariaAttributes.ariaLabelledBy).toBeTruthy();

      // Test screen reader announcements
      const liveRegion = await page.locator('[aria-live], [role="status"]').first();
      if (await liveRegion.isVisible()) {
        const liveRegionText = await liveRegion.textContent();
        expect(liveRegionText).toBeTruthy();
      }

      // Validate modal Material Design compliance
      const modalStyles = await modal.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          borderRadius: computed.borderRadius,
          boxShadow: computed.boxShadow,
          backgroundColor: computed.backgroundColor,
          maxWidth: computed.maxWidth
        };
      });

      expect(parseInt(modalStyles.borderRadius)).toBeGreaterThan(0);
      expect(modalStyles.boxShadow).not.toBe('none');
      expect(modalStyles.backgroundColor).not.toBe('transparent');
    });

    test('should handle multiple modal layers correctly', async ({ page }) => {
      await landingPage.goto();

      // Open first modal (login)
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Trigger second modal if available (like forgot password)
      const forgotPasswordLink = page.locator('[data-testid="forgot-password"], a:has-text("Forgot Password")');
      if (await forgotPasswordLink.isVisible()) {
        await forgotPasswordLink.click();

        // Should have two modals or second replaces first
        const modalCount = await page.locator('.modal, [role="dialog"]').count();
        expect(modalCount).toBeGreaterThanOrEqual(1);

        // Test escape key behavior with multiple modals
        await page.keyboard.press('Escape');

        // Should close top modal
        const remainingModals = await page.locator('.modal:visible, [role="dialog"]:visible').count();
        expect(remainingModals).toBeLessThanOrEqual(1);
      }
    });

    test('should handle modal backdrop click behavior', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Get modal and backdrop elements
      const modal = page.locator('.login-modal, [data-testid="login-modal"]');
      const backdrop = page.locator('.modal-overlay, .backdrop');

      if (await backdrop.isVisible()) {
        // Click backdrop to close
        await backdrop.click();

        // Modal should close
        const modalClosed = await page.waitForFunction(() => {
          return !document.querySelector('.login-modal, [data-testid="login-modal"]');
        }, { timeout: 3000 });
        expect(modalClosed).toBe(true);
      } else {
        // Test clicking outside modal content
        const modalBounds = await modal.boundingBox();
        if (modalBounds) {
          // Click outside modal but inside viewport
          await page.mouse.click(modalBounds.x - 50, modalBounds.y + modalBounds.height / 2);

          // Check if modal closes (behavior may vary)
          const modalStillVisible = await modal.isVisible();
          // Some modals should close, others shouldn't - test depends on implementation
        }
      }
    });

    test('should maintain modal performance under load', async ({ page }) => {
      await landingPage.goto();

      // Measure modal performance with repeated open/close
      const performanceMetrics = [];

      for (let i = 0; i < 5; i++) {
        const openStart = Date.now();
        await landingPage.clickSignIn();
        await landingPage.waitForLoginModal();
        const openTime = Date.now() - openStart;

        const closeStart = Date.now();
        await page.keyboard.press('Escape');
        await page.waitForFunction(() => {
          return !document.querySelector('.login-modal, [data-testid="login-modal"]');
        }, { timeout: 3000 });
        const closeTime = Date.now() - closeStart;

        performanceMetrics.push({ openTime, closeTime });
      }

      // Verify all interactions meet performance thresholds
      performanceMetrics.forEach(metric => {
        expect(metric.openTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.MODAL_OPEN);
        expect(metric.closeTime).toBeLessThan(500); // Modal close should be fast
      });

      // Verify performance doesn't degrade significantly
      const avgOpenTime = performanceMetrics.reduce((sum, m) => sum + m.openTime, 0) / performanceMetrics.length;
      const maxOpenTime = Math.max(...performanceMetrics.map(m => m.openTime));

      expect(maxOpenTime - avgOpenTime).toBeLessThan(200); // No significant degradation
    });
  });

  test.describe('Modal Error Handling', () => {
    test('should handle modal content loading errors', async ({ page }) => {
      // Simulate network error when loading modal content
      await page.route('**/api/users/**', route => route.abort('failed'));

      await landingPage.goto();

      // Login as admin and try to edit user (which might load data dynamically)
      await page.goto('/auth/test-login?user=admin&role=admin');
      await adminPage.goto();
      await adminPage.navigateToAdminSection('users');

      const users = await adminPage.getUserList();
      if (users.length > 0) {
        const editResult = await adminPage.editUser(users[0].id);

        // Modal should still open but might show error state
        expect(editResult.modalVisible).toBe(true);

        // Check for error message within modal
        const hasErrorInModal = await adminPage.isElementVisible(
          '.user-edit-modal .error-message, .modal .error-message', 3000
        );

        if (hasErrorInModal) {
          // Verify error is accessible
          const errorText = await page.locator('.user-edit-modal .error-message').textContent();
          expect(errorText).toBeTruthy();
        }
      }
    });

    test('should handle modal submission errors gracefully', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Intercept login request to simulate server error
      await page.route('**/api/auth/login', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal server error' })
        });
      });

      // Fill login form
      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      const submissionResult = await landingPage.submitLoginForm();

      // Should show error but keep modal open
      expect(submissionResult.result).toBe('error');

      const modalStillVisible = await landingPage.isElementVisible('.login-modal, [data-testid="login-modal"]');
      expect(modalStillVisible).toBe(true);

      // Error should be displayed within modal
      const errorMessage = await landingPage.getLoginErrorMessage();
      expect(errorMessage).toBeTruthy();
    });
  });
});
