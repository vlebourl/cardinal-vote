import { test, expect } from '@playwright/test';
import { EnhancedLandingPage } from '../../pages/landing-page.enhanced.js';
import { EnhancedVoteCreationPage } from '../../pages/vote-creation-page.enhanced.js';
import { EnhancedAdminPage } from '../../pages/admin-page.enhanced.js';
import { EnhancedPublicVotingPage } from '../../pages/public-voting-page.enhanced.js';
import { testDataManager } from '../../fixtures/data/test-data-factory.js';
import { PERFORMANCE_FIXTURES } from '../../fixtures/data/performance-accessibility-fixtures.js';

test.describe('Advanced Form Validation Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  let landingPage;
  let voteCreationPage;
  let adminPage;
  let publicVotingPage;

  test.beforeEach(async ({ page }) => {
    landingPage = new EnhancedLandingPage(page);
    voteCreationPage = new EnhancedVoteCreationPage(page);
    adminPage = new EnhancedAdminPage(page);
    publicVotingPage = new EnhancedPublicVotingPage(page);
  });

  test.afterEach(async ({ page }) => {
    await testDataManager.runCleanup();
  });

  test.describe('Real-time Field Validation', () => {
    test('should validate email format in real-time', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const emailField = page.locator('input[type="email"], input[name="email"]');

      // Test invalid email formats
      const invalidEmails = [
        'invalid',
        'invalid@',
        'invalid@domain',
        '@domain.com',
        'user..name@domain.com',
        'user name@domain.com'
      ];

      for (const email of invalidEmails) {
        await emailField.fill(email);
        await emailField.blur(); // Trigger validation

        // Should show validation error
        const hasError = await landingPage.isElementVisible('.field-error, .email-error, [aria-invalid="true"]', 2000);
        expect(hasError).toBe(true);

        // Error should be descriptive
        const errorMessage = await landingPage.getFieldError('email');
        expect(errorMessage.toLowerCase()).toMatch(/email|format|invalid/);
      }

      // Test valid email
      await emailField.fill('valid.email@domain.com');
      await emailField.blur();

      // Error should disappear
      const errorGone = await page.waitForFunction(() => {
        const errorElement = document.querySelector('.field-error, .email-error');
        return !errorElement || !errorElement.offsetParent;
      }, { timeout: 3000 });
      expect(errorGone).toBe(true);
    });

    test('should validate password strength in real-time', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      const passwordField = page.locator('input[type="password"][name="password"]');
      const strengthIndicator = page.locator('.password-strength, [data-testid="password-strength"]');

      // Test weak passwords
      const weakPasswords = [
        '123',
        'password',
        'abcdef',
        '123456'
      ];

      for (const password of weakPasswords) {
        await passwordField.fill(password);
        await page.waitForTimeout(500); // Allow debounced validation

        // Should show weak strength
        if (await strengthIndicator.isVisible()) {
          const strengthText = await strengthIndicator.textContent();
          expect(strengthText.toLowerCase()).toMatch(/weak|poor|too short/);
        }

        // Should show validation error
        const hasError = await landingPage.isElementVisible('.password-error, .field-error', 1000);
        expect(hasError).toBe(true);
      }

      // Test strong password
      await passwordField.fill('StrongPassword123!');
      await page.waitForTimeout(500);

      // Should show strong strength
      if (await strengthIndicator.isVisible()) {
        const strengthText = await strengthIndicator.textContent();
        expect(strengthText.toLowerCase()).toMatch(/strong|good|excellent/);
      }
    });

    test('should validate form fields on blur and focus', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      const emailField = page.locator('input[name="email"]');
      const passwordField = page.locator('input[name="password"]');

      // Focus and blur empty field
      await emailField.focus();
      await emailField.blur();

      // Should show required field error
      const requiredError = await landingPage.isElementVisible('.field-error, [aria-invalid="true"]', 2000);
      expect(requiredError).toBe(true);

      // Focus field again - error styling should remain but not duplicate messages
      await emailField.focus();
      await emailField.fill('test@example.com');

      // Error should clear on valid input
      const errorCleared = await page.waitForFunction(() => {
        const emailField = document.querySelector('input[name="email"]');
        return emailField && emailField.getAttribute('aria-invalid') !== 'true';
      }, { timeout: 3000 });
      expect(errorCleared).toBe(true);
    });

    test('should handle async validation (email uniqueness)', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      const emailField = page.locator('input[name="email"]');

      // Use existing test user email to trigger uniqueness validation
      await emailField.fill('user1.test@cardinalvote.local');
      await emailField.blur();

      // Should show loading state during validation
      const loadingIndicator = await landingPage.isElementVisible('.validating, .checking, [data-testid="validating"]', 1000);

      // Wait for validation to complete
      await page.waitForTimeout(2000);

      // Should show email already exists error
      const uniquenessError = await landingPage.isElementVisible('.field-error', 5000);
      if (uniquenessError) {
        const errorText = await landingPage.getFieldError('email');
        expect(errorText.toLowerCase()).toMatch(/already|exists|taken|registered/);
      }
    });
  });

  test.describe('Form Validation Performance', () => {
    test('should validate forms within performance thresholds', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      const formData = testDataManager.createFormData('registration', 'valid');

      // Measure form validation performance
      const validationTimes = [];

      for (const [field, value] of Object.entries(formData)) {
        const fieldSelector = `input[name="${field}"], textarea[name="${field}"], select[name="${field}"]`;
        const fieldElement = page.locator(fieldSelector);

        if (await fieldElement.isVisible()) {
          const startTime = Date.now();
          await fieldElement.fill(value.toString());
          await fieldElement.blur();

          // Wait for validation to complete
          await page.waitForTimeout(100);

          const validationTime = Date.now() - startTime;
          validationTimes.push({ field, time: validationTime });

          expect(validationTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.FORM_VALIDATION || 500);
        }
      }

      // Overall form validation should be responsive
      const avgValidationTime = validationTimes.reduce((sum, v) => sum + v.time, 0) / validationTimes.length;
      expect(avgValidationTime).toBeLessThan(200);
    });

    test('should handle rapid field updates without validation lag', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const emailField = page.locator('input[name="email"]');

      // Rapid typing simulation
      const rapidInputs = [
        'a',
        'ab',
        'abc',
        'abc@',
        'abc@d',
        'abc@dom',
        'abc@domain',
        'abc@domain.',
        'abc@domain.c',
        'abc@domain.com'
      ];

      const startTime = Date.now();

      for (const input of rapidInputs) {
        await emailField.fill(input);
        await page.waitForTimeout(50); // Rapid typing
      }

      const totalTime = Date.now() - startTime;
      expect(totalTime).toBeLessThan(2000); // Should handle rapid input smoothly

      // Final validation should be accurate
      const finalValidation = await landingPage.validateField('email');
      expect(finalValidation.isValid).toBe(true);
    });
  });

  test.describe('Complex Vote Creation Form Validation', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await voteCreationPage.goto();
    });

    test('should validate multi-step form progression', async ({ page }) => {
      // Step 1: Try to proceed without required fields
      const initialStep = await voteCreationPage.getCurrentStep();
      expect(initialStep).toBe(1);

      // Attempt to go to next step without filling required fields
      await voteCreationPage.clickElement(voteCreationPage.stepNavigation.nextButton);

      // Should remain on step 1 and show validation errors
      const stepAfterAttempt = await voteCreationPage.getCurrentStep();
      expect(stepAfterAttempt).toBe(1);

      const validation = await voteCreationPage.validateBasicInformation();
      expect(validation.title.isValid).toBe(false);
      expect(validation.description.isValid).toBe(false);

      // Fill required fields
      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);

      // Now should be able to proceed
      const nextStepResult = await voteCreationPage.goToNextStep();
      expect(nextStepResult.newStep).toBe(2);
    });

    test('should validate vote options requirements', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Try to proceed without minimum options
      await voteCreationPage.goToNextStep();

      // Should show validation error for insufficient options
      const validation = await voteCreationPage.validateCompleteForm();
      expect(validation.step2.hasMinimumOptions).toBe(false);

      // Add one option (still not enough)
      await voteCreationPage.addVoteOption({ text: 'Single Option' });

      const validationWithOne = await voteCreationPage.validateCompleteForm();
      expect(validationWithOne.step2.hasMinimumOptions).toBe(false);

      // Add second option
      await voteCreationPage.addVoteOption({ text: 'Second Option' });

      const validationWithTwo = await voteCreationPage.validateCompleteForm();
      expect(validationWithTwo.step2.hasMinimumOptions).toBe(true);
    });

    test('should validate empty and duplicate options', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Add options with validation issues
      await voteCreationPage.addVoteOption({ text: 'Valid Option' });
      await voteCreationPage.addVoteOption({ text: '' }); // Empty
      await voteCreationPage.addVoteOption({ text: 'Valid Option' }); // Duplicate

      const validation = await voteCreationPage.validateCompleteForm();
      expect(validation.step2.hasEmptyOptions).toBe(true);

      // Check for duplicate validation if implemented
      const options = await voteCreationPage.getOptions();
      const duplicateTexts = options.filter(opt => opt.text === 'Valid Option');
      expect(duplicateTexts.length).toBe(2);
    });

    test('should validate date range settings', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();

      // Set end date before start date
      const today = new Date().toISOString().split('T')[0];
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      await voteCreationPage.fillVoteSettings({
        startDate: today,
        endDate: yesterday
      });

      const dateValidation = await voteCreationPage.validateDateRange();
      expect(dateValidation.isValid).toBe(false);
      expect(dateValidation.error).toBeTruthy();

      // Try to publish with invalid dates
      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('error');
    });

    test('should validate numeric field constraints', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();

      // Test invalid numeric inputs
      const maxVotesField = page.locator(voteCreationPage.settings.maxVotesPerUserInput);

      if (await maxVotesField.isVisible()) {
        // Test negative number
        await maxVotesField.fill('-1');
        await maxVotesField.blur();

        const hasError = await voteCreationPage.isElementVisible('.field-error, [aria-invalid="true"]', 2000);
        expect(hasError).toBe(true);

        // Test zero
        await maxVotesField.fill('0');
        await maxVotesField.blur();

        const zeroError = await voteCreationPage.isElementVisible('.field-error, [aria-invalid="true"]', 2000);
        expect(zeroError).toBe(true);

        // Test valid number
        await maxVotesField.fill('3');
        await maxVotesField.blur();

        const errorCleared = await page.waitForFunction(() => {
          const field = document.querySelector('input[name="maxVotesPerUser"]');
          return field && field.getAttribute('aria-invalid') !== 'true';
        }, { timeout: 3000 });
        expect(errorCleared).toBe(true);
      }
    });
  });

  test.describe('Admin Form Validation', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/auth/test-login?user=admin&role=admin');
      await adminPage.goto();
    });

    test('should validate user management forms', async ({ page }) => {
      await adminPage.navigateToAdminSection('users');

      const users = await adminPage.getUserList();
      if (users.length > 0) {
        // Open user edit modal
        await adminPage.editUser(users[0].id);

        // Test email validation in user edit
        const emailField = page.locator('.user-edit-modal input[name="email"]');
        if (await emailField.isVisible()) {
          await emailField.fill('invalid-email');
          await emailField.blur();

          const emailError = await adminPage.isElementVisible('.field-error, [aria-invalid="true"]', 2000);
          expect(emailError).toBe(true);

          // Test valid email
          await emailField.fill('valid.user@example.com');
          await emailField.blur();

          const errorCleared = await page.waitForFunction(() => {
            const field = document.querySelector('.user-edit-modal input[name="email"]');
            return field && field.getAttribute('aria-invalid') !== 'true';
          }, { timeout: 3000 });
          expect(errorCleared).toBe(true);
        }

        await adminPage.closeModal();
      }
    });

    test('should validate system settings forms', async ({ page }) => {
      await adminPage.navigateToAdminSection('settings');

      // Test site title validation
      const siteTitleField = page.locator(adminPage.systemSettings.siteTitleInput);
      if (await siteTitleField.isVisible()) {
        // Clear field to test required validation
        await siteTitleField.fill('');
        await siteTitleField.blur();

        const requiredError = await adminPage.isElementVisible('.field-error', 2000);
        expect(requiredError).toBe(true);

        // Test minimum length if applicable
        await siteTitleField.fill('A');
        await siteTitleField.blur();

        const lengthError = await adminPage.isElementVisible('.field-error', 2000);
        if (lengthError) {
          const errorText = await page.locator('.field-error').first().textContent();
          expect(errorText.toLowerCase()).toMatch(/length|characters|minimum/);
        }

        // Valid title
        await siteTitleField.fill('Valid Site Title');
        await siteTitleField.blur();
      }

      // Test numeric field validation
      const maxOptionsField = page.locator(adminPage.systemSettings.maxVoteOptionsInput);
      if (await maxOptionsField.isVisible()) {
        await maxOptionsField.fill('invalid');
        await maxOptionsField.blur();

        const numericError = await adminPage.isElementVisible('.field-error', 2000);
        expect(numericError).toBe(true);

        await maxOptionsField.fill('10');
        await maxOptionsField.blur();
      }
    });

    test('should validate security settings with complex rules', async ({ page }) => {
      await adminPage.navigateToAdminSection('security');

      // Test session timeout validation
      const sessionTimeoutField = page.locator(adminPage.security.sessionTimeoutInput);
      if (await sessionTimeoutField.isVisible()) {
        // Test invalid range
        await sessionTimeoutField.fill('0');
        await sessionTimeoutField.blur();

        const rangeError = await adminPage.isElementVisible('.field-error', 2000);
        expect(rangeError).toBe(true);

        // Test maximum value
        await sessionTimeoutField.fill('999999');
        await sessionTimeoutField.blur();

        const maxError = await adminPage.isElementVisible('.field-error', 2000);
        if (maxError) {
          const errorText = await page.locator('.field-error').first().textContent();
          expect(errorText.toLowerCase()).toMatch(/maximum|too high|limit/);
        }
      }
    });
  });

  test.describe('Cross-field Validation', () => {
    test('should validate password confirmation matching', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      const passwordField = page.locator('input[name="password"]');
      const confirmPasswordField = page.locator('input[name="confirmPassword"]');

      await passwordField.fill('TestPassword123!');
      await confirmPasswordField.fill('DifferentPassword123!');
      await confirmPasswordField.blur();

      // Should show mismatch error
      const mismatchError = await landingPage.isElementVisible('.field-error, [aria-invalid="true"]', 2000);
      expect(mismatchError).toBe(true);

      const errorText = await landingPage.getFieldError('confirmPassword');
      expect(errorText.toLowerCase()).toMatch(/match|confirm|same/);

      // Fix the mismatch
      await confirmPasswordField.fill('TestPassword123!');
      await confirmPasswordField.blur();

      const errorFixed = await page.waitForFunction(() => {
        const field = document.querySelector('input[name="confirmPassword"]');
        return field && field.getAttribute('aria-invalid') !== 'true';
      }, { timeout: 3000 });
      expect(errorFixed).toBe(true);
    });

    test('should validate start/end date relationships', async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await voteCreationPage.goto();

      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();

      const startDateField = page.locator(voteCreationPage.settings.startDateInput);
      const endDateField = page.locator(voteCreationPage.settings.endDateInput);

      // Set start date in future
      const futureDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      await startDateField.fill(futureDate);

      // Set end date before start date
      const pastDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      await endDateField.fill(pastDate);
      await endDateField.blur();

      // Should show relationship validation error
      const relationshipError = await voteCreationPage.isElementVisible('.field-error, .date-range-error', 2000);
      expect(relationshipError).toBe(true);
    });

    test('should validate dependent field relationships', async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await voteCreationPage.goto();

      const voteData = testDataManager.createVote('multi-choice');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Add 5 options
      for (let i = 1; i <= 5; i++) {
        await voteCreationPage.addVoteOption({ text: `Option ${i}` });
      }

      await voteCreationPage.goToNextStep();

      // Set max votes per user higher than available options
      const maxVotesField = page.locator(voteCreationPage.settings.maxVotesPerUserInput);
      if (await maxVotesField.isVisible()) {
        await maxVotesField.fill('10'); // More than 5 options
        await maxVotesField.blur();

        const dependencyError = await voteCreationPage.isElementVisible('.field-error', 2000);
        if (dependencyError) {
          const errorText = await page.locator('.field-error').first().textContent();
          expect(errorText.toLowerCase()).toMatch(/options|maximum|available/);
        }
      }
    });
  });

  test.describe('Form Validation Accessibility', () => {
    test('should provide accessible error messages', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const emailField = page.locator('input[name="email"]');

      // Trigger validation error
      await emailField.fill('invalid-email');
      await emailField.blur();

      // Check ARIA attributes
      const ariaInvalid = await emailField.getAttribute('aria-invalid');
      expect(ariaInvalid).toBe('true');

      const ariaDescribedBy = await emailField.getAttribute('aria-describedby');
      expect(ariaDescribedBy).toBeTruthy();

      // Error message should be associated with field
      if (ariaDescribedBy) {
        const errorElement = page.locator(`#${ariaDescribedBy}`);
        expect(await errorElement.isVisible()).toBe(true);

        const errorText = await errorElement.textContent();
        expect(errorText).toBeTruthy();
      }

      // Error should be announced to screen readers
      const roleAlert = await page.locator('[role="alert"]').first();
      if (await roleAlert.isVisible()) {
        const alertText = await roleAlert.textContent();
        expect(alertText).toBeTruthy();
      }
    });

    test('should support keyboard navigation of validation errors', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      // Submit form with errors
      await landingPage.clickElement('button[type="submit"], .submit-button');

      // Should focus first error field
      const focusedElement = await page.evaluate(() => document.activeElement?.name);
      expect(['email', 'password', 'firstName']).toContain(focusedElement);

      // Tab through form and verify error indicators are accessible
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab');

        const currentField = await page.evaluate(() => {
          const active = document.activeElement;
          return {
            name: active?.name,
            ariaInvalid: active?.getAttribute('aria-invalid'),
            hasError: active?.getAttribute('aria-describedby') !== null
          };
        });

        if (currentField.ariaInvalid === 'true') {
          expect(currentField.hasError).toBe(true);
        }
      }
    });
  });

  test.describe('Form Validation Error Recovery', () => {
    test('should clear errors when fields become valid', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const emailField = page.locator('input[name="email"]');

      // Create error
      await emailField.fill('invalid');
      await emailField.blur();

      const hasError = await landingPage.isElementVisible('.field-error', 2000);
      expect(hasError).toBe(true);

      // Fix error
      await emailField.fill('valid@example.com');
      await emailField.blur();

      // Error should clear
      const errorCleared = await page.waitForFunction(() => {
        const errorElement = document.querySelector('.field-error');
        return !errorElement || !errorElement.offsetParent;
      }, { timeout: 3000 });
      expect(errorCleared).toBe(true);

      // ARIA attributes should update
      const ariaInvalid = await emailField.getAttribute('aria-invalid');
      expect(ariaInvalid).not.toBe('true');
    });

    test('should handle server-side validation errors', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      // Intercept registration to return validation errors
      await page.route('**/api/auth/register', route => {
        route.fulfill({
          status: 400,
          body: JSON.stringify({
            errors: {
              email: 'Email already exists',
              password: 'Password too weak'
            }
          })
        });
      });

      const formData = testDataManager.createFormData('registration', 'valid');
      await landingPage.fillRegistrationForm(formData);
      const result = await landingPage.submitRegistrationForm();

      expect(result.result).toBe('error');

      // Server errors should be displayed as field errors
      const emailError = await landingPage.getFieldError('email');
      expect(emailError).toContain('already exists');

      const passwordError = await landingPage.getFieldError('password');
      expect(passwordError).toContain('too weak');
    });

    test('should handle network errors during validation', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      // Intercept email validation request
      await page.route('**/api/validate/email', route => route.abort('failed'));

      const emailField = page.locator('input[name="email"]');
      await emailField.fill('test@example.com');
      await emailField.blur();

      // Should handle gracefully - either show generic error or skip validation
      await page.waitForTimeout(2000);

      // Should not block form submission
      const formData = testDataManager.createFormData('registration', 'valid');
      await landingPage.fillRegistrationForm(formData);

      // Form should still be submittable despite validation network error
      const submitButton = page.locator('button[type="submit"]');
      const isDisabled = await submitButton.isDisabled();
      expect(isDisabled).toBe(false);
    });
  });
});
