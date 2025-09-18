import { test, expect } from '@playwright/test';
import { EnhancedLandingPage as LandingPage } from '../../pages/LandingPage.js';
import { EnhancedDashboardPage as DashboardPage } from '../../pages/DashboardPage.js';
import { EnhancedVoteCreationPage as VoteCreationPage } from '../../pages/VoteCreationPage.js';
import { EnhancedPublicVotingPage as PublicVotingPage } from '../../pages/PublicVotingPage.js';
import { EnhancedAdminPage as AdminPage } from '../../pages/AdminPage.js';
import { EnhancedErrorPage as ErrorPage } from '../../pages/ErrorPage.js';
import { VALIDATION_FIXTURES, PERFORMANCE_FIXTURES } from '../../fixtures/validationFixtures.js';

test.describe('Validation Error Scenarios', () => {
  let landingPage, dashboardPage, voteCreationPage, publicVotingPage, adminPage, errorPage;

  test.beforeEach(async ({ page }) => {
    landingPage = new LandingPage(page);
    dashboardPage = new DashboardPage(page);
    voteCreationPage = new VoteCreationPage(page);
    publicVotingPage = new PublicVotingPage(page);
    adminPage = new AdminPage(page);
    errorPage = new ErrorPage(page);
    await landingPage.goto();
  });

  test.describe('Authentication Validation Errors', () => {
    test('should handle empty authentication fields', async ({ page }) => {
      await landingPage.clickSignIn();

      // Submit empty form
      const submitResult = await landingPage.submitLoginForm();
      expect(submitResult.result).toBe('error');

      // Verify specific validation messages
      const usernameError = await landingPage.getFieldValidationError('username');
      const passwordError = await landingPage.getFieldValidationError('password');

      expect(usernameError).toContain('required');
      expect(passwordError).toContain('required');

      // Verify form state persists
      const formData = await landingPage.getFormData();
      expect(formData.username).toBe('');
      expect(formData.password).toBe('');
    });

    test('should handle invalid email format validation', async ({ page }) => {
      await landingPage.clickSignUp();

      const invalidEmails = VALIDATION_FIXTURES.INVALID_EMAILS;

      for (const email of invalidEmails) {
        await landingPage.fillEmail(email);
        await landingPage.triggerFieldValidation('email');

        const validationError = await landingPage.getFieldValidationError('email');
        expect(validationError).toContain('valid email');

        // Clear field for next test
        await landingPage.clearField('email');
      }
    });

    test('should validate password strength requirements', async ({ page }) => {
      await landingPage.clickSignUp();

      const weakPasswords = VALIDATION_FIXTURES.WEAK_PASSWORDS;

      for (const password of weakPasswords) {
        await landingPage.fillPassword(password);
        await landingPage.triggerFieldValidation('password');

        const validationError = await landingPage.getFieldValidationError('password');
        expect(validationError).toBeTruthy();

        // Verify password strength indicator
        const strengthIndicator = await landingPage.getPasswordStrengthIndicator();
        expect(strengthIndicator.level).toBe('weak');

        await landingPage.clearField('password');
      }
    });

    test('should validate password confirmation mismatch', async ({ page }) => {
      await landingPage.clickSignUp();

      await landingPage.fillPassword('StrongPassword123!');
      await landingPage.fillPasswordConfirmation('DifferentPassword456!');
      await landingPage.triggerFieldValidation('passwordConfirmation');

      const validationError = await landingPage.getFieldValidationError('passwordConfirmation');
      expect(validationError).toContain('match');

      // Verify form cannot be submitted
      const submitResult = await landingPage.submitRegistrationForm();
      expect(submitResult.result).toBe('error');
    });

    test('should handle duplicate username/email validation', async ({ page }) => {
      await landingPage.clickSignUp();

      // Use existing user data
      const existingUser = VALIDATION_FIXTURES.EXISTING_USER;

      await landingPage.fillEmail(existingUser.email);
      await landingPage.fillUsername(existingUser.username);
      await landingPage.fillPassword('NewPassword123!');
      await landingPage.fillPasswordConfirmation('NewPassword123!');

      const submitResult = await landingPage.submitRegistrationForm();
      expect(submitResult.result).toBe('error');

      const emailError = await landingPage.getFieldValidationError('email');
      const usernameError = await landingPage.getFieldValidationError('username');

      expect(emailError || usernameError).toBeTruthy();
    });
  });

  test.describe('Vote Creation Validation Errors', () => {
    test.beforeEach(async ({ page }) => {
      // Login as admin first
      await landingPage.loginAsAdmin();
      await dashboardPage.waitForDashboard();
      await dashboardPage.clickCreateVote();
    });

    test('should validate required vote fields', async ({ page }) => {
      // Submit form without filling required fields
      const submitResult = await voteCreationPage.submitVoteCreation();
      expect(submitResult.result).toBe('error');

      // Check all required field validations
      const titleError = await voteCreationPage.getFieldValidationError('title');
      const descriptionError = await voteCreationPage.getFieldValidationError('description');
      const deadlineError = await voteCreationPage.getFieldValidationError('deadline');

      expect(titleError).toContain('required');
      expect(descriptionError).toContain('required');
      expect(deadlineError).toContain('required');
    });

    test('should validate vote title length constraints', async ({ page }) => {
      const longTitle = 'x'.repeat(VALIDATION_FIXTURES.VOTE_TITLE_MAX_LENGTH + 1);

      await voteCreationPage.fillTitle(longTitle);
      await voteCreationPage.triggerFieldValidation('title');

      const validationError = await voteCreationPage.getFieldValidationError('title');
      expect(validationError).toContain('too long');

      // Verify character counter
      const charCount = await voteCreationPage.getCharacterCount('title');
      expect(charCount.current).toBeGreaterThan(charCount.max);
      expect(charCount.isOverLimit).toBe(true);
    });

    test('should validate vote deadline constraints', async ({ page }) => {
      // Test past date
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - 1);

      await voteCreationPage.fillDeadline(pastDate.toISOString().split('T')[0]);
      await voteCreationPage.triggerFieldValidation('deadline');

      const pastDateError = await voteCreationPage.getFieldValidationError('deadline');
      expect(pastDateError).toContain('future');

      // Test too far future date
      const farFutureDate = new Date();
      farFutureDate.setFullYear(farFutureDate.getFullYear() + 2);

      await voteCreationPage.fillDeadline(farFutureDate.toISOString().split('T')[0]);
      await voteCreationPage.triggerFieldValidation('deadline');

      const futureError = await voteCreationPage.getFieldValidationError('deadline');
      expect(futureError).toBeTruthy();
    });

    test('should validate minimum vote options requirement', async ({ page }) => {
      await voteCreationPage.fillTitle('Test Vote');
      await voteCreationPage.fillDescription('Test Description');

      // Try to submit with no options
      const submitResult = await voteCreationPage.submitVoteCreation();
      expect(submitResult.result).toBe('error');

      const optionsError = await voteCreationPage.getValidationError('options');
      expect(optionsError).toContain('minimum');

      // Add one option (still insufficient)
      await voteCreationPage.addVoteOption('Option 1', 'Description 1');

      const oneOptionResult = await voteCreationPage.submitVoteCreation();
      expect(oneOptionResult.result).toBe('error');

      const minOptionsError = await voteCreationPage.getValidationError('options');
      expect(minOptionsError).toContain('at least');
    });

    test('should validate vote option content requirements', async ({ page }) => {
      await voteCreationPage.fillTitle('Test Vote');
      await voteCreationPage.fillDescription('Test Description');

      // Add option with empty title
      await voteCreationPage.addVoteOption('', 'Valid description');

      const titleValidation = await voteCreationPage.getOptionValidationError(0, 'title');
      expect(titleValidation).toContain('required');

      // Add option with excessively long title
      const longTitle = 'x'.repeat(VALIDATION_FIXTURES.OPTION_TITLE_MAX_LENGTH + 1);
      await voteCreationPage.addVoteOption(longTitle, 'Valid description');

      const lengthValidation = await voteCreationPage.getOptionValidationError(1, 'title');
      expect(lengthValidation).toContain('too long');
    });

    test('should validate file upload constraints', async ({ page }) => {
      await voteCreationPage.fillTitle('Test Vote');
      await voteCreationPage.fillDescription('Test Description');
      await voteCreationPage.addVoteOption('Option 1', 'Description 1');

      // Test file too large
      const largeFile = VALIDATION_FIXTURES.LARGE_FILE_PATH;
      const uploadResult = await voteCreationPage.uploadOptionFile(0, largeFile);

      expect(uploadResult.success).toBe(false);
      expect(uploadResult.error).toContain('too large');

      // Test invalid file type
      const invalidFile = VALIDATION_FIXTURES.INVALID_FILE_TYPE_PATH;
      const typeResult = await voteCreationPage.uploadOptionFile(0, invalidFile);

      expect(typeResult.success).toBe(false);
      expect(typeResult.error).toContain('type');
    });
  });

  test.describe('Voting Validation Errors', () => {
    test.beforeEach(async ({ page }) => {
      // Create a test vote first
      await landingPage.loginAsAdmin();
      await dashboardPage.waitForDashboard();

      const voteId = await dashboardPage.createQuickTestVote({
        title: 'Validation Test Vote',
        options: ['Option A', 'Option B', 'Option C']
      });

      // Navigate to public voting
      await publicVotingPage.goto(voteId);
    });

    test('should validate vote value constraints', async ({ page }) => {
      // Test out of range values
      const invalidValues = VALIDATION_FIXTURES.INVALID_VOTE_VALUES;

      for (let i = 0; i < invalidValues.length; i++) {
        const value = invalidValues[i];
        const setResult = await publicVotingPage.setVoteValue(0, value);

        expect(setResult.success).toBe(false);
        expect(setResult.error).toContain('range');
      }
    });

    test('should validate total vote allocation', async ({ page }) => {
      // Set votes that exceed maximum allocation
      await publicVotingPage.setVoteValue(0, 2);
      await publicVotingPage.setVoteValue(1, 2);
      await publicVotingPage.setVoteValue(2, 2);

      const submitResult = await publicVotingPage.submitVotes();
      expect(submitResult.result).toBe('error');

      const allocationError = await publicVotingPage.getValidationError('allocation');
      expect(allocationError).toContain('exceeds');

      // Verify allocation indicator shows over-allocation
      const allocationStatus = await publicVotingPage.getAllocationStatus();
      expect(allocationStatus.isOverAllocated).toBe(true);
      expect(allocationStatus.remaining).toBeLessThan(0);
    });

    test('should validate voting deadline constraints', async ({ page }) => {
      // Simulate expired vote
      await errorPage.simulateExpiredVote();

      const voteResult = await publicVotingPage.setVoteValue(0, 1);
      expect(voteResult.success).toBe(false);

      const submitResult = await publicVotingPage.submitVotes();
      expect(submitResult.result).toBe('error');
      expect(submitResult.error).toContain('expired');

      // Verify UI indicates vote is closed
      const voteStatus = await publicVotingPage.getVoteStatus();
      expect(voteStatus.isActive).toBe(false);
      expect(voteStatus.reason).toContain('deadline');
    });

    test('should validate duplicate voting prevention', async ({ page }) => {
      // Submit valid votes
      await publicVotingPage.setVoteValue(0, 1);
      await publicVotingPage.setVoteValue(1, -1);

      const firstSubmit = await publicVotingPage.submitVotes();
      expect(firstSubmit.result).toBe('success');

      // Try to vote again
      await publicVotingPage.setVoteValue(0, 2);
      const secondSubmit = await publicVotingPage.submitVotes();

      expect(secondSubmit.result).toBe('error');
      expect(secondSubmit.error).toContain('already voted');

      // Verify UI shows vote already submitted
      const voteStatus = await publicVotingPage.getVoteStatus();
      expect(voteStatus.hasVoted).toBe(true);
    });
  });

  test.describe('Admin Validation Errors', () => {
    test.beforeEach(async ({ page }) => {
      await landingPage.loginAsAdmin();
      await adminPage.goto();
    });

    test('should validate user management constraints', async ({ page }) => {
      // Try to delete admin user
      const deleteResult = await adminPage.deleteUser('admin');
      expect(deleteResult.success).toBe(false);
      expect(deleteResult.error).toContain('cannot delete');

      // Try to modify admin role
      const roleResult = await adminPage.changeUserRole('admin', 'user');
      expect(roleResult.success).toBe(false);
      expect(roleResult.error).toContain('admin role');
    });

    test('should validate system settings constraints', async ({ page }) => {
      // Test invalid vote allocation limits
      const invalidLimits = VALIDATION_FIXTURES.INVALID_ALLOCATION_LIMITS;

      for (const limit of invalidLimits) {
        const setResult = await adminPage.setAllocationLimit(limit);
        expect(setResult.success).toBe(false);
        expect(setResult.error).toBeTruthy();
      }
    });

    test('should validate backup/restore operations', async ({ page }) => {
      // Test invalid backup file
      const invalidBackup = VALIDATION_FIXTURES.INVALID_BACKUP_FILE;
      const restoreResult = await adminPage.restoreFromBackup(invalidBackup);

      expect(restoreResult.success).toBe(false);
      expect(restoreResult.error).toContain('invalid');

      // Verify system state unchanged
      const systemStatus = await adminPage.getSystemStatus();
      expect(systemStatus.hasChanges).toBe(false);
    });
  });

  test.describe('Performance Under Validation Load', () => {
    test('should maintain performance during validation cascades', async ({ page }) => {
      await landingPage.clickSignUp();

      const startTime = Date.now();

      // Trigger multiple validation errors simultaneously
      await Promise.all([
        landingPage.fillEmail('invalid-email'),
        landingPage.fillUsername('x'),
        landingPage.fillPassword('weak'),
        landingPage.fillPasswordConfirmation('different')
      ]);

      // Trigger all validations
      await landingPage.triggerAllFieldValidations();

      const validationTime = Date.now() - startTime;
      expect(validationTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.VALIDATION.MULTIPLE_FIELDS);

      // Verify all errors are displayed
      const errors = await landingPage.getAllValidationErrors();
      expect(errors.length).toBeGreaterThan(0);
    });

    test('should handle validation with slow network', async ({ page }) => {
      // Simulate slow network
      await errorPage.simulateSlowNetwork();

      await landingPage.clickSignUp();
      await landingPage.fillEmail('test@unique-email-domain.com');

      const validationStart = Date.now();
      await landingPage.triggerFieldValidation('email');

      // Should show loading state during async validation
      const hasLoadingState = await landingPage.hasValidationLoadingState('email');
      expect(hasLoadingState).toBe(true);

      // Wait for validation to complete
      await landingPage.waitForValidationCompletion('email');

      const validationTime = Date.now() - validationStart;
      expect(validationTime).toBeGreaterThan(PERFORMANCE_FIXTURES.THRESHOLDS.VALIDATION.ASYNC_MIN);

      // Restore normal network
      await errorPage.restoreNormalNetwork();
    });
  });

  test.describe('Validation Error Recovery', () => {
    test('should recover from validation errors gracefully', async ({ page }) => {
      await landingPage.clickSignUp();

      // Enter invalid data
      await landingPage.fillEmail('invalid-email');
      await landingPage.submitRegistrationForm();

      // Verify error state
      const hasErrors = await landingPage.hasValidationErrors();
      expect(hasErrors).toBe(true);

      // Correct the data
      await landingPage.fillEmail('valid@email.com');
      await landingPage.fillUsername('validuser');
      await landingPage.fillPassword('ValidPassword123!');
      await landingPage.fillPasswordConfirmation('ValidPassword123!');

      // Verify errors clear
      const errorsCleared = await landingPage.waitForValidationErrorsClear();
      expect(errorsCleared).toBe(true);

      // Verify successful submission
      const submitResult = await landingPage.submitRegistrationForm();
      expect(submitResult.result).toBe('success');
    });

    test('should maintain form state during validation errors', async ({ page }) => {
      await landingPage.clickSignUp();

      const testData = {
        email: 'test@email.com',
        username: 'testuser',
        password: 'TestPassword123!',
        passwordConfirmation: 'WrongConfirmation'
      };

      // Fill form with one invalid field
      await landingPage.fillRegistrationForm(testData);
      await landingPage.submitRegistrationForm();

      // Verify valid fields retain their values
      const formData = await landingPage.getFormData();
      expect(formData.email).toBe(testData.email);
      expect(formData.username).toBe(testData.username);
      expect(formData.password).toBe(testData.password);

      // Verify only confirmation field has error
      const emailError = await landingPage.getFieldValidationError('email');
      const usernameError = await landingPage.getFieldValidationError('username');
      const passwordError = await landingPage.getFieldValidationError('password');
      const confirmationError = await landingPage.getFieldValidationError('passwordConfirmation');

      expect(emailError).toBeFalsy();
      expect(usernameError).toBeFalsy();
      expect(passwordError).toBeFalsy();
      expect(confirmationError).toBeTruthy();
    });
  });

  test.describe('Cross-Field Validation', () => {
    test('should validate interdependent fields correctly', async ({ page }) => {
      await landingPage.loginAsAdmin();
      await dashboardPage.clickCreateVote();

      // Set start date after end date
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);

      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);

      await voteCreationPage.fillStartDate(tomorrow.toISOString().split('T')[0]);
      await voteCreationPage.fillEndDate(yesterday.toISOString().split('T')[0]);

      const submitResult = await voteCreationPage.submitVoteCreation();
      expect(submitResult.result).toBe('error');

      const dateRangeError = await voteCreationPage.getCrossFieldValidationError('dateRange');
      expect(dateRangeError).toContain('start date must be before end date');
    });

    test('should validate allocation totals across vote options', async ({ page }) => {
      const voteId = await landingPage.loginAndCreateTestVote();
      await publicVotingPage.goto(voteId);

      // Set votes that sum to more than allowed
      await publicVotingPage.setVoteValue(0, 2);
      await publicVotingPage.setVoteValue(1, 1);
      await publicVotingPage.setVoteValue(2, 2); // Total = 5, max = 4

      const allocationStatus = await publicVotingPage.getAllocationStatus();
      expect(allocationStatus.isOverAllocated).toBe(true);
      expect(allocationStatus.total).toBe(5);
      expect(allocationStatus.remaining).toBe(-1);

      const submitResult = await publicVotingPage.submitVotes();
      expect(submitResult.result).toBe('error');
      expect(submitResult.error).toContain('allocation');
    });
  });
});
