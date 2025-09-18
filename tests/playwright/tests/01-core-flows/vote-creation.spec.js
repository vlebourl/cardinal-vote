import { test, expect } from '@playwright/test';
import { EnhancedVoteCreationPage } from '../../pages/vote-creation-page.enhanced.js';
import { EnhancedDashboardPage } from '../../pages/dashboard-page.enhanced.js';
import { EnhancedPublicVotingPage } from '../../pages/public-voting-page.enhanced.js';
import { testDataManager } from '../../fixtures/data/test-data-factory.js';
import { PERFORMANCE_FIXTURES } from '../../fixtures/data/performance-accessibility-fixtures.js';

test.describe('Core Vote Creation Flow Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  let voteCreationPage;
  let dashboardPage;
  let publicVotingPage;

  test.beforeEach(async ({ page }) => {
    voteCreationPage = new EnhancedVoteCreationPage(page);
    dashboardPage = new EnhancedDashboardPage(page);
    publicVotingPage = new EnhancedPublicVotingPage(page);

    // Login as a user who can create votes
    await page.goto('/auth/test-login?user=user1&role=user');
  });

  test.afterEach(async ({ page }) => {
    await testDataManager.runCleanup();
  });

  test.describe('Basic Vote Creation', () => {
    test('should successfully create a simple vote', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();

      // Validate page load performance
      const loadTime = await voteCreationPage.measurePageLoadTime();
      expect(loadTime.isAcceptable).toBe(true);

      // Step 1: Basic Information
      const basicInfoResult = await voteCreationPage.fillBasicInformation(voteData);
      expect(basicInfoResult.isAcceptable).toBe(true);

      // Validate basic information
      const basicValidation = await voteCreationPage.validateBasicInformation();
      expect(basicValidation.title.isValid).toBe(true);
      expect(basicValidation.description.isValid).toBe(true);
      expect(basicValidation.type.isValid).toBe(true);

      // Navigate to next step
      const nextStepResult = await voteCreationPage.goToNextStep();
      expect(nextStepResult.isAcceptable).toBe(true);
      expect(nextStepResult.newStep).toBe(2);

      // Step 2: Add vote options
      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });

      const optionCount = await voteCreationPage.getOptionCount();
      expect(optionCount).toBe(2);

      const options = await voteCreationPage.getOptions();
      expect(options.every(option => !option.isEmpty)).toBe(true);

      // Navigate to final step
      await voteCreationPage.goToNextStep();
      expect(await voteCreationPage.getCurrentStep()).toBe(3);

      // Step 3: Vote settings (use defaults)
      const settingsData = {
        startDate: new Date().toISOString().split('T')[0],
        endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      };
      await voteCreationPage.fillVoteSettings(settingsData);

      // Validate complete form
      const formValidation = await voteCreationPage.validateCompleteForm();
      expect(formValidation.isValid).toBe(true);

      // Publish the vote
      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('success');
      expect(publishResult.isAcceptable).toBe(true);

      // Verify redirect to vote page or dashboard
      expect(['vote_page', 'redirect']).toContain(publishResult.result);
    });

    test('should create a multi-choice vote', async ({ page }) => {
      const multiChoiceData = testDataManager.createVote('multi-choice', { optionCount: 4 });

      await voteCreationPage.goto();

      // Fill basic information
      await voteCreationPage.fillBasicInformation(multiChoiceData);
      await voteCreationPage.goToNextStep();

      // Add multiple options
      for (let i = 0; i < multiChoiceData.options.length; i++) {
        await voteCreationPage.addVoteOption({ text: multiChoiceData.options[i] });
      }

      const optionCount = await voteCreationPage.getOptionCount();
      expect(optionCount).toBe(multiChoiceData.options.length);

      // Navigate to settings and set multi-choice specific settings
      await voteCreationPage.goToNextStep();
      await voteCreationPage.fillVoteSettings({
        maxVotesPerUser: 3,
        requireRegistration: false
      });

      // Validate and publish
      const formValidation = await voteCreationPage.validateCompleteForm();
      expect(formValidation.isValid).toBe(true);

      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('success');
    });

    test('should create a time-limited vote', async ({ page }) => {
      const timeLimitedData = testDataManager.createVote('time-limited', {
        duration: 'hours',
        amount: 2
      });

      await voteCreationPage.goto();

      await voteCreationPage.fillBasicInformation(timeLimitedData);
      await voteCreationPage.goToNextStep();

      // Add basic options
      await voteCreationPage.addVoteOption({ text: 'Yes' });
      await voteCreationPage.addVoteOption({ text: 'No' });

      await voteCreationPage.goToNextStep();

      // Set time-limited settings
      const now = new Date();
      const endTime = new Date(now.getTime() + 2 * 60 * 60 * 1000); // 2 hours from now

      await voteCreationPage.fillVoteSettings({
        startDate: now.toISOString().split('T')[0],
        endDate: endTime.toISOString().split('T')[0]
      });

      // Validate date range
      const dateValidation = await voteCreationPage.validateDateRange();
      expect(dateValidation.isValid).toBe(true);

      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('success');
    });
  });

  test.describe('Complex Vote Creation', () => {
    test('should create a complex vote with advanced features', async ({ page }) => {
      const complexData = testDataManager.createVote('complex');

      await voteCreationPage.goto();

      // Fill comprehensive basic information
      await voteCreationPage.fillBasicInformation(complexData);
      await voteCreationPage.goToNextStep();

      // Add multiple options with variety
      for (let i = 0; i < Math.min(complexData.options.length, 5); i++) {
        await voteCreationPage.addVoteOption({ text: complexData.options[i] });
      }

      // Test option reordering
      const initialOptions = await voteCreationPage.getOptions();
      if (initialOptions.length >= 2) {
        await voteCreationPage.reorderOption(0, 1);
        const reorderedOptions = await voteCreationPage.getOptions();
        expect(reorderedOptions[0].text).not.toBe(initialOptions[0].text);
      }

      await voteCreationPage.goToNextStep();

      // Configure advanced settings
      await voteCreationPage.fillVoteSettings({
        requireRegistration: true,
        allowComments: true,
        showResults: 'after_voting',
        notifications: true,
        maxVotesPerUser: complexData.maxOptionsPerVoter || 3
      });

      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('success');
    });

    test('should handle bulk option import', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Test bulk import functionality
      const bulkOptions = 'Option 1\nOption 2\nOption 3\nOption 4\nOption 5';
      const optionCount = await voteCreationPage.bulkImportOptions(bulkOptions);
      expect(optionCount).toBe(5);

      const options = await voteCreationPage.getOptions();
      expect(options.length).toBe(5);
      expect(options.every(option => !option.isEmpty)).toBe(true);

      await voteCreationPage.goToNextStep();
      await voteCreationPage.fillVoteSettings({});

      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('success');
    });
  });

  test.describe('File Upload for Vote Options', () => {
    test('should handle image uploads for vote options', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Create a test image file
      const testImagePath = './tests/playwright/fixtures/test-image.png';

      // Add option with image (if file upload is supported)
      await voteCreationPage.addVoteOption({
        text: 'Option with Image',
        file: testImagePath
      });

      const options = await voteCreationPage.getOptions();
      expect(options.some(option => option.hasFile)).toBe(true);

      await voteCreationPage.goToNextStep();
      await voteCreationPage.fillVoteSettings({});

      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('success');
    });
  });

  test.describe('Draft Management', () => {
    test('should save and load vote drafts', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();

      // Fill partial information
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();
      await voteCreationPage.addVoteOption({ text: 'Draft Option 1' });

      // Save as draft
      const draftResult = await voteCreationPage.saveDraft();
      expect(draftResult.result).toBe('success');
      expect(draftResult.isAcceptable).toBe(true);

      // Navigate away and back
      await dashboardPage.goto();

      // Check if draft appears in dashboard
      const votes = await dashboardPage.getVoteCards();
      const hasDraft = votes.some(vote => vote.status.toLowerCase().includes('draft'));
      expect(hasDraft).toBe(true);
    });
  });

  test.describe('Preview Functionality', () => {
    test('should show accurate vote preview', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      await voteCreationPage.addVoteOption({ text: 'Preview Option A' });
      await voteCreationPage.addVoteOption({ text: 'Preview Option B' });

      // Open preview
      const previewData = await voteCreationPage.previewVote();
      expect(previewData).toBeTruthy();
      expect(previewData.title).toBe(voteData.title);
      expect(previewData.description).toBe(voteData.description);
      expect(previewData.optionCount).toBe(2);
    });
  });

  test.describe('Form Validation', () => {
    test('should validate required fields', async ({ page }) => {
      await voteCreationPage.goto();

      // Try to proceed without filling required fields
      const nextStepResult = await voteCreationPage.goToNextStep().catch(() => ({ newStep: 1 }));
      expect(nextStepResult.newStep).toBe(1); // Should stay on step 1

      // Validate specific field errors
      const validation = await voteCreationPage.validateBasicInformation();
      expect(validation.title.isValid).toBe(false);
      expect(validation.description.isValid).toBe(false);

      // Fill required fields and try again
      const validData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(validData);

      const validationAfterFill = await voteCreationPage.validateBasicInformation();
      expect(validationAfterFill.title.isValid).toBe(true);
      expect(validationAfterFill.description.isValid).toBe(true);

      const nextStepAfterFill = await voteCreationPage.goToNextStep();
      expect(nextStepAfterFill.newStep).toBe(2);
    });

    test('should validate minimum options requirement', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Try to proceed with only one option
      await voteCreationPage.addVoteOption({ text: 'Only Option' });

      const validation = await voteCreationPage.validateCompleteForm();
      expect(validation.step2.hasMinimumOptions).toBe(false);

      // Add second option
      await voteCreationPage.addVoteOption({ text: 'Second Option' });

      const validationAfterSecond = await voteCreationPage.validateCompleteForm();
      expect(validationAfterSecond.step2.hasMinimumOptions).toBe(true);
    });

    test('should validate empty options', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Add options, one empty
      await voteCreationPage.addVoteOption({ text: 'Valid Option' });
      await voteCreationPage.addVoteOption({ text: '' }); // Empty option

      const validation = await voteCreationPage.validateCompleteForm();
      expect(validation.step2.hasEmptyOptions).toBe(true);
      expect(validation.step2.isValid).toBe(false);
    });

    test('should validate date ranges', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();

      // Set invalid date range (end before start)
      const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000);
      const today = new Date();

      await voteCreationPage.fillVoteSettings({
        startDate: tomorrow.toISOString().split('T')[0],
        endDate: today.toISOString().split('T')[0]
      });

      const dateValidation = await voteCreationPage.validateDateRange();
      expect(dateValidation.isValid).toBe(false);
      expect(dateValidation.error).toBeTruthy();
    });
  });

  test.describe('Step Navigation', () => {
    test('should handle step navigation correctly', async ({ page }) => {
      await voteCreationPage.goto();

      // Test forward navigation
      expect(await voteCreationPage.getCurrentStep()).toBe(1);

      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);

      await voteCreationPage.goToNextStep();
      expect(await voteCreationPage.getCurrentStep()).toBe(2);

      // Test backward navigation
      await voteCreationPage.goToPreviousStep();
      expect(await voteCreationPage.getCurrentStep()).toBe(1);

      // Test direct navigation
      await voteCreationPage.goToStep(3);
      expect(await voteCreationPage.getCurrentStep()).toBe(3);
    });

    test('should preserve data across step navigation', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();

      // Fill step 1
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Fill step 2
      await voteCreationPage.addVoteOption({ text: 'Preserved Option' });
      await voteCreationPage.goToNextStep();

      // Go back to step 1 and verify data is preserved
      await voteCreationPage.goToStep(1);

      const titleValue = await voteCreationPage.getElementValue(voteCreationPage.basicInfo.titleInput);
      expect(titleValue).toBe(voteData.title);

      // Go back to step 2 and verify options are preserved
      await voteCreationPage.goToStep(2);

      const options = await voteCreationPage.getOptions();
      expect(options.some(option => option.text === 'Preserved Option')).toBe(true);
    });
  });

  test.describe('Performance Testing', () => {
    test('should meet performance thresholds for vote creation', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();

      // Measure form interaction performance
      const performanceMetrics = await voteCreationPage.validateFormPerformance();

      Object.values(performanceMetrics).forEach(metric => {
        expect(metric.isAcceptable).toBe(true);
      });

      // Complete vote creation and measure total time
      const startTime = Date.now();

      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();
      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();
      await voteCreationPage.fillVoteSettings({});
      const publishResult = await voteCreationPage.publishVote();

      const totalTime = Date.now() - startTime;

      expect(publishResult.isAcceptable).toBe(true);
      expect(totalTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.VOTE_CREATION * 3); // Allow extra time for full flow
    });
  });

  test.describe('Accessibility Testing', () => {
    test('should have accessible vote creation form', async ({ page }) => {
      await voteCreationPage.goto();

      const accessibility = await voteCreationPage.validateAccessibility();

      expect(accessibility.focusManagement.focusableElementCount).toBeGreaterThan(0);
      expect(accessibility.ariaAttributes.hasAriaElements).toBe(true);
      expect(accessibility.keyboardNavigation.tabNavigationWorks).toBe(true);
      expect(accessibility.semanticStructure.hasMainContent).toBe(true);
    });

    test('should support keyboard navigation through vote creation', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      await voteCreationPage.goto();

      // Test keyboard navigation through step 1
      await page.keyboard.press('Tab'); // Title field
      await page.keyboard.type(voteData.title);

      await page.keyboard.press('Tab'); // Description field
      await page.keyboard.type(voteData.description);

      // Navigate through the form using keyboard
      let tabCount = 0;
      while (tabCount < 10) { // Safety limit
        await page.keyboard.press('Tab');
        tabCount++;

        // Check if we've reached the next button
        const activeElement = await page.evaluate(() => document.activeElement?.textContent);
        if (activeElement && activeElement.includes('Next')) {
          await page.keyboard.press('Enter');
          break;
        }
      }

      // Should be on step 2
      expect(await voteCreationPage.getCurrentStep()).toBe(2);
    });
  });

  test.describe('Material Design Validation', () => {
    test('should follow Material Design principles for vote creation form', async ({ page }) => {
      await voteCreationPage.goto();

      const materialDesign = await voteCreationPage.validateFormMaterialDesign();

      expect(materialDesign.form.textFields.hasTextFields).toBe(true);
      expect(materialDesign.form.buttons.allButtonsValid).toBe(true);

      if (materialDesign.form.stepperDesign.hasStepper) {
        expect(materialDesign.form.stepperDesign.stepCount).toBeGreaterThan(0);
      }

      if (materialDesign.form.fileUploadDesign.uploadZoneCount > 0) {
        expect(materialDesign.form.fileUploadDesign.validations.every(v => v.isInteractive)).toBe(true);
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle server errors gracefully', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      // Intercept and simulate server error
      await page.route('**/api/votes**', route => route.abort('failed'));

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();
      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();
      await voteCreationPage.fillVoteSettings({});

      const publishResult = await voteCreationPage.publishVote();
      expect(publishResult.result).toBe('error');

      // Verify error message is displayed
      const errors = await voteCreationPage.getFormValidationErrors();
      expect(errors.length).toBeGreaterThan(0);
    });

    test('should handle network timeout', async ({ page }) => {
      const voteData = testDataManager.createVote('basic');

      // Simulate network timeout
      await page.route('**/api/votes**', route => {
        setTimeout(() => route.abort('timedout'), 30000);
      });

      await voteCreationPage.goto();
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();
      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();
      await voteCreationPage.fillVoteSettings({});

      const publishResult = await voteCreationPage.publishVote();
      expect(['error', 'timeout']).toContain(publishResult.result);
    });
  });
});
