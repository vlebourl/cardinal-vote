import { expect } from '@playwright/test';
import { BasePage } from './base-page.js';
import { MATERIAL_DESIGN_FIXTURES } from '../fixtures/data/material-design-fixtures.js';
import { PERFORMANCE_FIXTURES } from '../fixtures/data/performance-accessibility-fixtures.js';

/**
 * Enhanced Vote Creation Page Object Model
 *
 * Extends BasePage with comprehensive vote creation functionality including:
 * - Multi-step form validation and submission
 * - File upload for vote options with previews
 * - Dynamic option management (add/remove/reorder)
 * - Vote settings and configuration
 * - Real-time validation and error handling
 * - Material Design form component validation
 * - Performance monitoring for large votes
 */
export class EnhancedVoteCreationPage extends BasePage {
  constructor(page) {
    super(page);

    // Form step navigation
    this.stepNavigation = {
      stepIndicator: '[data-testid="step-indicator"], .step-indicator',
      step1: '[data-testid="step-1"], .step-1',
      step2: '[data-testid="step-2"], .step-2',
      step3: '[data-testid="step-3"], .step-3',
      nextButton: '[data-testid="next-step"], button:has-text("Next")',
      previousButton: '[data-testid="previous-step"], button:has-text("Previous")',
      currentStepTitle: '[data-testid="current-step-title"], .current-step-title'
    };

    // Basic vote information (Step 1)
    this.basicInfo = {
      titleInput: '[data-testid="vote-title"], input[name="title"]',
      descriptionTextarea: '[data-testid="vote-description"], textarea[name="description"]',
      typeSelect: '[data-testid="vote-type"], select[name="type"]',
      categorySelect: '[data-testid="vote-category"], select[name="category"]',
      tagsInput: '[data-testid="vote-tags"], input[name="tags"]',
      isPublicToggle: '[data-testid="is-public"], input[type="checkbox"][name="isPublic"]',
      allowAnonymousToggle: '[data-testid="allow-anonymous"], input[type="checkbox"][name="allowAnonymous"]'
    };

    // Vote options (Step 2)
    this.optionsSection = {
      optionsContainer: '[data-testid="options-container"], .options-container',
      optionItem: '[data-testid="option-item"], .option-item',
      optionInput: '[data-testid="option-input"], input.option-input',
      optionFileInput: '[data-testid="option-file"], input[type="file"].option-file',
      optionPreview: '[data-testid="option-preview"], .option-preview',
      addOptionButton: '[data-testid="add-option"], button:has-text("Add Option")',
      removeOptionButton: '[data-testid="remove-option"], .remove-option',
      reorderHandle: '[data-testid="reorder-handle"], .reorder-handle',
      bulkImportButton: '[data-testid="bulk-import"], button:has-text("Bulk Import")',
      clearAllOptionsButton: '[data-testid="clear-options"], button:has-text("Clear All")'
    };

    // Vote settings (Step 3)
    this.settings = {
      startDateInput: '[data-testid="start-date"], input[name="startDate"]',
      endDateInput: '[data-testid="end-date"], input[name="endDate"]',
      maxVotesPerUserInput: '[data-testid="max-votes-per-user"], input[name="maxVotesPerUser"]',
      requireRegistrationToggle: '[data-testid="require-registration"], input[type="checkbox"][name="requireRegistration"]',
      showResultsSelect: '[data-testid="show-results"], select[name="showResults"]',
      allowCommentsToggle: '[data-testid="allow-comments"], input[type="checkbox"][name="allowComments"]',
      notificationToggle: '[data-testid="notifications"], input[type="checkbox"][name="notifications"]',
      duplicateVotingPreventionToggle: '[data-testid="prevent-duplicates"], input[type="checkbox"][name="preventDuplicates"]'
    };

    // Form submission and actions
    this.actions = {
      saveDraftButton: '[data-testid="save-draft"], button:has-text("Save Draft")',
      previewButton: '[data-testid="preview-vote"], button:has-text("Preview")',
      publishButton: '[data-testid="publish-vote"], button:has-text("Publish")',
      cancelButton: '[data-testid="cancel"], button:has-text("Cancel")',
      resetFormButton: '[data-testid="reset-form"], button:has-text("Reset")'
    };

    // Validation and error elements
    this.validation = {
      errorMessage: '.error-message, .field-error, [role="alert"]',
      warningMessage: '.warning-message, .field-warning',
      successMessage: '.success-message, .field-success',
      fieldError: '.field-error',
      globalError: '[data-testid="global-error"], .global-error',
      validationSummary: '[data-testid="validation-summary"], .validation-summary'
    };

    // File upload and preview elements
    this.fileUpload = {
      uploadZone: '[data-testid="upload-zone"], .upload-zone',
      fileList: '[data-testid="file-list"], .file-list',
      fileItem: '[data-testid="file-item"], .file-item',
      removeFileButton: '[data-testid="remove-file"], .remove-file',
      uploadProgress: '[data-testid="upload-progress"], .upload-progress',
      uploadError: '[data-testid="upload-error"], .upload-error'
    };

    // Modals and dialogs
    this.modals = {
      previewModal: '[data-testid="preview-modal"], .preview-modal',
      confirmationModal: '[data-testid="confirmation-modal"], .confirmation-modal',
      bulkImportModal: '[data-testid="bulk-import-modal"], .bulk-import-modal',
      modalOverlay: '.modal-overlay, .backdrop',
      modalClose: '[data-testid="modal-close"], .modal-close'
    };
  }

  /**
   * Navigation Methods
   */
  async goto() {
    const loadTime = await super.goto('/create-vote');
    await this.waitForFormToLoad();
    return loadTime;
  }

  async waitForFormToLoad() {
    // Wait for the form and essential elements to be ready
    await Promise.all([
      this.waitForElement(this.basicInfo.titleInput),
      this.waitForElement(this.basicInfo.descriptionTextarea),
      this.waitForElement(this.stepNavigation.nextButton)
    ]);

    // Wait for any initialization scripts to complete
    await this.page.waitForFunction(() => {
      return !document.querySelector('.form-loading, .initializing');
    }, { timeout: 5000 }).catch(() => {
      // Loading indicators might not be present
    });
  }

  /**
   * Step Navigation Methods
   */
  async getCurrentStep() {
    const stepElements = await this.page.locator(this.stepNavigation.stepIndicator + ' .active, .step.active').all();
    if (stepElements.length > 0) {
      const stepText = await stepElements[0].textContent();
      return parseInt(stepText?.match(/\d+/)?.[0] || '1');
    }
    return 1;
  }

  async goToNextStep() {
    const currentStep = await this.getCurrentStep();
    const startTime = Date.now();

    await this.clickElement(this.stepNavigation.nextButton);

    // Wait for step transition to complete
    await this.page.waitForFunction((step) => {
      const activeStep = document.querySelector('.step.active, .step-indicator .active');
      if (!activeStep) return false;
      const stepNum = parseInt(activeStep.textContent?.match(/\d+/)?.[0] || '1');
      return stepNum > step;
    }, currentStep, { timeout: 5000 });

    const transitionTime = Date.now() - startTime;
    return {
      newStep: await this.getCurrentStep(),
      transitionTime,
      isAcceptable: transitionTime < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION
    };
  }

  async goToPreviousStep() {
    const currentStep = await this.getCurrentStep();

    if (currentStep <= 1) {
      throw new Error('Already at first step');
    }

    await this.clickElement(this.stepNavigation.previousButton);

    // Wait for step transition to complete
    await this.page.waitForFunction((step) => {
      const activeStep = document.querySelector('.step.active, .step-indicator .active');
      if (!activeStep) return false;
      const stepNum = parseInt(activeStep.textContent?.match(/\d+/)?.[0] || '1');
      return stepNum < step;
    }, currentStep, { timeout: 5000 });

    return await this.getCurrentStep();
  }

  async goToStep(stepNumber) {
    const currentStep = await this.getCurrentStep();

    if (stepNumber === currentStep) {
      return currentStep;
    }

    // Click on the specific step indicator if available
    const stepSelector = `${this.stepNavigation.stepIndicator} [data-step="${stepNumber}"], .step-${stepNumber}`;
    if (await this.isElementVisible(stepSelector)) {
      await this.clickElement(stepSelector);
    } else {
      // Navigate using next/previous buttons
      while (await this.getCurrentStep() !== stepNumber) {
        if (await this.getCurrentStep() < stepNumber) {
          await this.goToNextStep();
        } else {
          await this.goToPreviousStep();
        }
      }
    }

    return await this.getCurrentStep();
  }

  /**
   * Basic Information Methods (Step 1)
   */
  async fillBasicInformation(voteData) {
    await this.goToStep(1);

    const startTime = Date.now();

    // Fill required fields
    await this.fillField(this.basicInfo.titleInput, voteData.title);
    await this.fillField(this.basicInfo.descriptionTextarea, voteData.description);

    // Handle vote type selection
    if (voteData.type) {
      await this.selectOption(this.basicInfo.typeSelect, voteData.type);
    }

    // Handle category selection
    if (voteData.category) {
      await this.selectOption(this.basicInfo.categorySelect, voteData.category);
    }

    // Handle tags input
    if (voteData.tags) {
      const tagsString = Array.isArray(voteData.tags) ? voteData.tags.join(', ') : voteData.tags;
      await this.fillField(this.basicInfo.tagsInput, tagsString);
    }

    // Handle toggles
    if (voteData.isPublic !== undefined) {
      await this.setToggle(this.basicInfo.isPublicToggle, voteData.isPublic);
    }

    if (voteData.allowAnonymous !== undefined) {
      await this.setToggle(this.basicInfo.allowAnonymousToggle, voteData.allowAnonymous);
    }

    const fillTime = Date.now() - startTime;
    return {
      fillTime,
      isAcceptable: fillTime < 2000 // 2 seconds for form filling
    };
  }

  async setToggle(selector, value) {
    const toggle = this.page.locator(selector);
    const isChecked = await toggle.isChecked();

    if ((value && !isChecked) || (!value && isChecked)) {
      await toggle.click();
    }
  }

  async validateBasicInformation() {
    const validation = {
      title: await this.validateField(this.basicInfo.titleInput, 'required'),
      description: await this.validateField(this.basicInfo.descriptionTextarea, 'required'),
      type: await this.validateField(this.basicInfo.typeSelect, 'selected')
    };

    return validation;
  }

  /**
   * Vote Options Methods (Step 2)
   */
  async addVoteOption(optionData) {
    await this.goToStep(2);

    const initialOptionCount = await this.getOptionCount();

    // Click add option button
    await this.clickElement(this.optionsSection.addOptionButton);

    // Wait for new option to appear
    await this.page.waitForFunction((count) => {
      const options = document.querySelectorAll('[data-testid="option-item"], .option-item');
      return options.length > count;
    }, initialOptionCount, { timeout: 5000 });

    // Fill the new option
    const optionInputs = await this.page.locator(this.optionsSection.optionInput).all();
    const newOptionInput = optionInputs[optionInputs.length - 1];

    await newOptionInput.fill(optionData.text || optionData.title || '');

    // Handle file upload if provided
    if (optionData.file) {
      const fileInputs = await this.page.locator(this.optionsSection.optionFileInput).all();
      const newFileInput = fileInputs[fileInputs.length - 1];
      await newFileInput.setInputFiles(optionData.file);

      // Wait for file upload to complete
      await this.waitForFileUpload(optionInputs.length - 1);
    }

    return await this.getOptionCount();
  }

  async removeVoteOption(index) {
    const initialCount = await this.getOptionCount();

    if (initialCount <= 2) {
      throw new Error('Cannot remove option: minimum 2 options required');
    }

    const removeButtons = await this.page.locator(this.optionsSection.removeOptionButton).all();
    if (index < removeButtons.length) {
      await removeButtons[index].click();

      // Wait for option to be removed
      await this.page.waitForFunction((count) => {
        const options = document.querySelectorAll('[data-testid="option-item"], .option-item');
        return options.length < count;
      }, initialCount, { timeout: 5000 });
    }

    return await this.getOptionCount();
  }

  async reorderOption(fromIndex, toIndex) {
    const options = await this.page.locator(this.optionsSection.optionItem).all();

    if (fromIndex >= options.length || toIndex >= options.length) {
      throw new Error('Invalid option index for reordering');
    }

    const sourceOption = options[fromIndex];
    const targetOption = options[toIndex];

    // Get the reorder handle
    const sourceHandle = sourceOption.locator(this.optionsSection.reorderHandle);
    const targetBounds = await targetOption.boundingBox();

    if (targetBounds) {
      // Perform drag and drop
      await sourceHandle.dragTo(targetOption, {
        targetPosition: { x: targetBounds.width / 2, y: targetBounds.height / 2 }
      });

      // Wait for reorder to complete
      await this.page.waitForTimeout(500);
    }
  }

  async getOptionCount() {
    const options = await this.page.locator(this.optionsSection.optionItem).all();
    return options.length;
  }

  async getOptions() {
    const optionElements = await this.page.locator(this.optionsSection.optionItem).all();
    const options = [];

    for (const [index, option] of optionElements.entries()) {
      const optionData = await option.evaluate((el, idx) => {
        const input = el.querySelector('input.option-input, [data-testid="option-input"]');
        const preview = el.querySelector('.option-preview, [data-testid="option-preview"]');
        const hasFile = !!el.querySelector('.file-preview, [data-testid="file-preview"]');

        return {
          index: idx,
          text: input?.value || '',
          hasFile,
          hasPreview: !!preview,
          isEmpty: !input?.value?.trim()
        };
      }, index);

      options.push(optionData);
    }

    return options;
  }

  async waitForFileUpload(optionIndex) {
    const uploadSelector = `${this.optionsSection.optionItem}:nth-child(${optionIndex + 1}) ${this.fileUpload.uploadProgress}`;

    // Wait for upload to start
    await this.waitForElement(uploadSelector, 'visible', 2000).catch(() => {
      // Upload progress might not be visible for small files
    });

    // Wait for upload to complete (progress disappears)
    await this.page.waitForFunction((selector) => {
      const progress = document.querySelector(selector);
      return !progress || !progress.offsetParent;
    }, uploadSelector, { timeout: 30000 }).catch(() => {
      // Continue if upload progress isn't found
    });
  }

  async bulkImportOptions(optionsText) {
    await this.clickElement(this.optionsSection.bulkImportButton);
    await this.waitForElement(this.modals.bulkImportModal);

    // Find the bulk import textarea and fill it
    const bulkTextarea = this.page.locator('.bulk-import-textarea, [data-testid="bulk-import-textarea"]');
    await bulkTextarea.fill(optionsText);

    // Click import button
    await this.clickElement('.import-button, [data-testid="import-button"]');

    // Wait for modal to close and options to be imported
    await this.page.waitForFunction(() => {
      return !document.querySelector('.bulk-import-modal, [data-testid="bulk-import-modal"]');
    }, { timeout: 10000 });

    return await this.getOptionCount();
  }

  /**
   * Vote Settings Methods (Step 3)
   */
  async fillVoteSettings(settingsData) {
    await this.goToStep(3);

    // Handle date inputs
    if (settingsData.startDate) {
      await this.fillField(this.settings.startDateInput, settingsData.startDate);
    }

    if (settingsData.endDate) {
      await this.fillField(this.settings.endDateInput, settingsData.endDate);
    }

    // Handle numeric inputs
    if (settingsData.maxVotesPerUser !== undefined) {
      await this.fillField(this.settings.maxVotesPerUserInput, settingsData.maxVotesPerUser.toString());
    }

    // Handle select inputs
    if (settingsData.showResults) {
      await this.selectOption(this.settings.showResultsSelect, settingsData.showResults);
    }

    // Handle toggle settings
    const toggleSettings = [
      { key: 'requireRegistration', selector: this.settings.requireRegistrationToggle },
      { key: 'allowComments', selector: this.settings.allowCommentsToggle },
      { key: 'notifications', selector: this.settings.notificationToggle },
      { key: 'preventDuplicates', selector: this.settings.duplicateVotingPreventionToggle }
    ];

    for (const setting of toggleSettings) {
      if (settingsData[setting.key] !== undefined) {
        await this.setToggle(setting.selector, settingsData[setting.key]);
      }
    }
  }

  async validateDateRange() {
    const startDate = await this.getElementValue(this.settings.startDateInput);
    const endDate = await this.getElementValue(this.settings.endDateInput);

    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);

      return {
        isValid: start < end,
        startDate,
        endDate,
        error: start >= end ? 'End date must be after start date' : null
      };
    }

    return { isValid: true, startDate, endDate, error: null };
  }

  /**
   * Form Submission Methods
   */
  async saveDraft() {
    const startTime = Date.now();

    await this.clickElement(this.actions.saveDraftButton);

    // Wait for save confirmation or redirect
    const result = await Promise.race([
      this.waitForElement(this.validation.successMessage, 'visible', 5000).then(() => 'success'),
      this.waitForElement(this.validation.errorMessage, 'visible', 5000).then(() => 'error'),
      this.waitForURL('**/dashboard', 5000).then(() => 'redirect'),
      this.page.waitForTimeout(5000).then(() => 'timeout')
    ]);

    const saveTime = Date.now() - startTime;

    return {
      result,
      saveTime,
      isAcceptable: saveTime < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.VOTE_CREATION
    };
  }

  async previewVote() {
    await this.clickElement(this.actions.previewButton);
    await this.waitForElement(this.modals.previewModal);

    // Extract preview data
    const previewData = await this.page.evaluate(() => {
      const modal = document.querySelector('.preview-modal, [data-testid="preview-modal"]');
      if (!modal) return null;

      return {
        title: modal.querySelector('.preview-title, [data-testid="preview-title"]')?.textContent?.trim(),
        description: modal.querySelector('.preview-description, [data-testid="preview-description"]')?.textContent?.trim(),
        optionCount: modal.querySelectorAll('.preview-option, [data-testid="preview-option"]').length,
        settings: modal.querySelector('.preview-settings, [data-testid="preview-settings"]')?.textContent?.trim()
      };
    });

    return previewData;
  }

  async publishVote() {
    const startTime = Date.now();

    await this.clickElement(this.actions.publishButton);

    // Wait for publish completion
    const result = await Promise.race([
      this.waitForElement(this.validation.successMessage, 'visible', 10000).then(() => 'success'),
      this.waitForElement(this.validation.errorMessage, 'visible', 5000).then(() => 'error'),
      this.waitForURL('**/dashboard', 10000).then(() => 'redirect'),
      this.waitForURL('**/vote/**', 10000).then(() => 'vote_page'),
      this.page.waitForTimeout(10000).then(() => 'timeout')
    ]);

    const publishTime = Date.now() - startTime;

    return {
      result,
      publishTime,
      isAcceptable: publishTime < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.VOTE_CREATION,
      url: this.page.url()
    };
  }

  /**
   * Validation Methods
   */
  async validateField(selector, validationType) {
    const element = this.page.locator(selector);

    const validation = {
      selector,
      exists: await element.count() > 0,
      visible: await element.isVisible().catch(() => false),
      value: await element.inputValue().catch(() => ''),
      isValid: true,
      errors: []
    };

    switch (validationType) {
      case 'required':
        validation.isValid = validation.value.trim() !== '';
        if (!validation.isValid) {
          validation.errors.push('Field is required');
        }
        break;

      case 'selected':
        if (await element.evaluate(el => el.tagName.toLowerCase()) === 'select') {
          const selectedValue = await element.inputValue();
          validation.isValid = selectedValue !== '' && selectedValue !== null;
          if (!validation.isValid) {
            validation.errors.push('Please select an option');
          }
        }
        break;
    }

    // Check for field-level error messages
    const errorElement = await element.locator('+ .field-error, ~ .field-error').first();
    if (await errorElement.isVisible().catch(() => false)) {
      const errorText = await errorElement.textContent();
      validation.errors.push(errorText?.trim() || 'Field has validation error');
      validation.isValid = false;
    }

    return validation;
  }

  async getFormValidationErrors() {
    const errorElements = await this.page.locator(this.validation.errorMessage).all();
    const errors = [];

    for (const errorElement of errorElements) {
      if (await errorElement.isVisible()) {
        const errorText = await errorElement.textContent();
        errors.push(errorText?.trim() || 'Unknown error');
      }
    }

    return errors;
  }

  async validateCompleteForm() {
    const validation = {
      step1: {
        title: await this.validateField(this.basicInfo.titleInput, 'required'),
        description: await this.validateField(this.basicInfo.descriptionTextarea, 'required'),
        type: await this.validateField(this.basicInfo.typeSelect, 'selected')
      },
      step2: {
        optionCount: await this.getOptionCount(),
        options: await this.getOptions(),
        hasMinimumOptions: await this.getOptionCount() >= 2
      },
      step3: {
        dateRange: await this.validateDateRange()
      },
      globalErrors: await this.getFormValidationErrors()
    };

    // Check for empty options
    validation.step2.hasEmptyOptions = validation.step2.options.some(opt => opt.isEmpty);
    validation.step2.isValid = validation.step2.hasMinimumOptions && !validation.step2.hasEmptyOptions;

    // Overall form validity
    validation.isValid =
      validation.step1.title.isValid &&
      validation.step1.description.isValid &&
      validation.step1.type.isValid &&
      validation.step2.isValid &&
      validation.step3.dateRange.isValid &&
      validation.globalErrors.length === 0;

    return validation;
  }

  /**
   * Performance and Material Design Validation
   */
  async validateFormPerformance() {
    const metrics = {};

    // Test form responsiveness
    const interactions = [
      {
        name: 'title_input',
        action: async () => {
          await this.fillField(this.basicInfo.titleInput, 'Test Performance Title');
        }
      },
      {
        name: 'add_option',
        action: async () => {
          await this.addVoteOption({ text: 'Performance Test Option' });
        }
      },
      {
        name: 'step_navigation',
        action: async () => {
          await this.goToNextStep();
        }
      }
    ];

    for (const interaction of interactions) {
      const startTime = Date.now();
      await interaction.action();
      const interactionTime = Date.now() - startTime;

      metrics[interaction.name] = {
        time: interactionTime,
        isAcceptable: interactionTime < PERFORMANCE_FIXTURES.THRESHOLDS.FIRST_INPUT_DELAY.ACCEPTABLE
      };
    }

    return metrics;
  }

  async validateFormMaterialDesign() {
    const baseValidation = await super.validateMaterialDesign();

    // Form-specific Material Design validations
    const formValidation = {
      textFields: await this.validateMaterialTextFields(),
      buttons: await this.validateFormButtons(),
      stepperDesign: await this.validateStepperDesign(),
      fileUploadDesign: await this.validateFileUploadDesign()
    };

    return {
      ...baseValidation,
      form: formValidation
    };
  }

  async validateStepperDesign() {
    const stepperElements = await this.page.locator(this.stepNavigation.stepIndicator).all();

    if (stepperElements.length === 0) {
      return { hasStepper: false };
    }

    const stepperValidation = await stepperElements[0].evaluate(stepper => {
      const computed = window.getComputedStyle(stepper);
      const steps = stepper.querySelectorAll('.step, [data-step]');

      return {
        stepCount: steps.length,
        hasHorizontalLayout: computed.display === 'flex' || computed.display === 'grid',
        hasProperSpacing: parseInt(computed.gap || computed.marginBottom) >= 8,
        steps: Array.from(steps).map(step => ({
          hasActiveState: step.classList.contains('active'),
          hasCompletedState: step.classList.contains('completed'),
          isInteractive: step.style.cursor === 'pointer'
        }))
      };
    });

    return {
      hasStepper: true,
      ...stepperValidation
    };
  }

  async validateFileUploadDesign() {
    const uploadZones = await this.page.locator(this.fileUpload.uploadZone).all();
    const validations = [];

    for (const zone of uploadZones) {
      const styles = await zone.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          border: computed.border,
          borderStyle: computed.borderStyle,
          backgroundColor: computed.backgroundColor,
          cursor: computed.cursor
        };
      });

      validations.push({
        hasMinHeight: parseInt(styles.minHeight) >= 100,
        hasBorder: styles.borderStyle !== 'none',
        isInteractive: styles.cursor === 'pointer',
        styles
      });
    }

    return {
      uploadZoneCount: uploadZones.length,
      validations
    };
  }

  async validateFormButtons() {
    const buttonSelectors = [
      this.stepNavigation.nextButton,
      this.stepNavigation.previousButton,
      this.actions.saveDraftButton,
      this.actions.publishButton
    ];

    const buttonValidations = [];

    for (const selector of buttonSelectors) {
      if (await this.isElementVisible(selector)) {
        const button = this.page.locator(selector);
        const styles = await button.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            minHeight: computed.minHeight,
            padding: computed.padding,
            borderRadius: computed.borderRadius,
            fontWeight: computed.fontWeight
          };
        });

        buttonValidations.push({
          selector,
          hasProperHeight: parseInt(styles.minHeight) >= 36,
          hasProperPadding: parseInt(styles.padding) >= 8,
          hasRoundedCorners: parseInt(styles.borderRadius) >= 4,
          styles
        });
      }
    }

    return {
      buttonCount: buttonValidations.length,
      validations: buttonValidations
    };
  }
}
