import { expect } from '@playwright/test';
import { BasePage } from './base-page.js';
import { MATERIAL_DESIGN_FIXTURES } from '../fixtures/data/material-design-fixtures.js';
import { PERFORMANCE_FIXTURES } from '../fixtures/data/performance-accessibility-fixtures.js';

/**
 * Enhanced Public Voting Page Object Model
 *
 * Extends BasePage with comprehensive public voting functionality including:
 * - Vote option selection and submission workflows
 * - Anonymous and authenticated voting support
 * - Real-time results display and updates
 * - Social sharing and interaction features
 * - Mobile-responsive voting interface
 * - Material Design voting component validation
 * - Performance monitoring for vote submissions
 */
export class EnhancedPublicVotingPage extends BasePage {
  constructor(page) {
    super(page);

    // Vote display elements
    this.voteDisplay = {
      voteTitle: '[data-testid="vote-title"], .vote-title, h1',
      voteDescription: '[data-testid="vote-description"], .vote-description',
      voteMetadata: '[data-testid="vote-metadata"], .vote-metadata',
      voteStatus: '[data-testid="vote-status"], .vote-status',
      voteDuration: '[data-testid="vote-duration"], .vote-duration',
      totalVotes: '[data-testid="total-votes"], .total-votes',
      authorInfo: '[data-testid="vote-author"], .vote-author'
    };

    // Voting interface elements
    this.votingInterface = {
      optionsContainer: '[data-testid="voting-options"], .voting-options',
      voteOption: '[data-testid="vote-option"], .vote-option',
      optionRadio: '[data-testid="option-radio"], input[type="radio"][name="vote"]',
      optionCheckbox: '[data-testid="option-checkbox"], input[type="checkbox"][name="vote"]',
      optionLabel: '[data-testid="option-label"], .option-label',
      optionImage: '[data-testid="option-image"], .option-image',
      optionDescription: '[data-testid="option-description"], .option-description',
      selectedOption: '.vote-option.selected, [data-selected="true"]',
      submitButton: '[data-testid="submit-vote"], button:has-text("Submit Vote")',
      clearSelectionButton: '[data-testid="clear-selection"], button:has-text("Clear")'
    };

    // Authentication and user interface
    this.userInterface = {
      loginPrompt: '[data-testid="login-prompt"], .login-prompt',
      loginButton: '[data-testid="login-button"], button:has-text("Login")',
      registerButton: '[data-testid="register-button"], button:has-text("Register")',
      anonymousVoteToggle: '[data-testid="anonymous-toggle"], input[type="checkbox"][name="anonymous"]',
      voterNameInput: '[data-testid="voter-name"], input[name="voterName"]',
      voterEmailInput: '[data-testid="voter-email"], input[name="voterEmail"]',
      userProfile: '[data-testid="user-profile"], .user-profile',
      logoutLink: '[data-testid="logout-link"], a:has-text("Logout")'
    };

    // Results and analytics
    this.resultsDisplay = {
      resultsContainer: '[data-testid="results-container"], .results-container',
      resultItem: '[data-testid="result-item"], .result-item',
      resultBar: '[data-testid="result-bar"], .result-bar',
      resultPercentage: '[data-testid="result-percentage"], .result-percentage',
      resultCount: '[data-testid="result-count"], .result-count',
      winningOption: '[data-testid="winning-option"], .winning-option',
      resultsChart: '[data-testid="results-chart"], .results-chart',
      showResultsButton: '[data-testid="show-results"], button:has-text("Show Results")',
      hideResultsButton: '[data-testid="hide-results"], button:has-text("Hide Results")'
    };

    // Social and sharing features
    this.socialFeatures = {
      shareButton: '[data-testid="share-vote"], button:has-text("Share")',
      shareModal: '[data-testid="share-modal"], .share-modal',
      shareUrl: '[data-testid="share-url"], .share-url',
      copyUrlButton: '[data-testid="copy-url"], button:has-text("Copy")',
      socialShareButtons: '[data-testid="social-share"], .social-share',
      facebookShare: '[data-testid="facebook-share"], .facebook-share',
      twitterShare: '[data-testid="twitter-share"], .twitter-share',
      linkedinShare: '[data-testid="linkedin-share"], .linkedin-share',
      emailShare: '[data-testid="email-share"], .email-share'
    };

    // Comments and interaction
    this.commentsSection = {
      commentsContainer: '[data-testid="comments-container"], .comments-container',
      commentItem: '[data-testid="comment-item"], .comment-item',
      commentText: '[data-testid="comment-text"], .comment-text',
      commentAuthor: '[data-testid="comment-author"], .comment-author',
      commentDate: '[data-testid="comment-date"], .comment-date',
      addCommentForm: '[data-testid="add-comment-form"], .add-comment-form',
      commentInput: '[data-testid="comment-input"], textarea[name="comment"]',
      submitCommentButton: '[data-testid="submit-comment"], button:has-text("Add Comment")',
      showCommentsButton: '[data-testid="show-comments"], button:has-text("Show Comments")'
    };

    // Vote confirmation and feedback
    this.confirmationElements = {
      confirmationModal: '[data-testid="vote-confirmation"], .vote-confirmation',
      successMessage: '[data-testid="vote-success"], .vote-success',
      errorMessage: '[data-testid="vote-error"], .vote-error',
      changeVoteButton: '[data-testid="change-vote"], button:has-text("Change Vote")',
      confirmSubmitButton: '[data-testid="confirm-submit"], button:has-text("Confirm")',
      cancelSubmitButton: '[data-testid="cancel-submit"], button:has-text("Cancel")',
      thankYouMessage: '[data-testid="thank-you"], .thank-you'
    };

    // Mobile and responsive elements
    this.mobileElements = {
      mobileMenu: '[data-testid="mobile-menu"], .mobile-menu',
      mobileToggle: '[data-testid="mobile-toggle"], .mobile-toggle',
      swipeIndicator: '[data-testid="swipe-indicator"], .swipe-indicator',
      mobileActions: '[data-testid="mobile-actions"], .mobile-actions'
    };

    // Real-time updates
    this.realTimeElements = {
      updateIndicator: '[data-testid="update-indicator"], .update-indicator',
      liveCount: '[data-testid="live-count"], .live-count',
      refreshButton: '[data-testid="refresh-results"], button:has-text("Refresh")',
      autoRefreshToggle: '[data-testid="auto-refresh"], input[type="checkbox"][name="autoRefresh"]'
    };
  }

  /**
   * Navigation and Loading Methods
   */
  async gotoVote(voteId) {
    const loadTime = await super.goto(`/vote/${voteId}`);
    await this.waitForVoteToLoad();
    return loadTime;
  }

  async gotoPublicVote(voteSlug) {
    const loadTime = await super.goto(`/v/${voteSlug}`);
    await this.waitForVoteToLoad();
    return loadTime;
  }

  async waitForVoteToLoad() {
    // Wait for essential vote elements to be visible
    await Promise.all([
      this.waitForElement(this.voteDisplay.voteTitle),
      this.waitForElement(this.votingInterface.optionsContainer),
      this.waitForElement(this.votingInterface.voteOption, 'visible', 10000).catch(() => {
        // Vote might not have options loaded yet
      })
    ]);

    // Wait for any loading spinners to disappear
    await this.page.waitForFunction(() => {
      const spinners = document.querySelectorAll('.loading, .spinner, [data-testid="loading"]');
      return spinners.length === 0;
    }, { timeout: 10000 }).catch(() => {
      // Loading indicators might not be present
    });
  }

  /**
   * Vote Information Methods
   */
  async getVoteInformation() {
    const voteInfo = {
      title: await this.getElementText(this.voteDisplay.voteTitle).catch(() => ''),
      description: await this.getElementText(this.voteDisplay.voteDescription).catch(() => ''),
      status: await this.getElementText(this.voteDisplay.voteStatus).catch(() => ''),
      totalVotes: await this.getTotalVoteCount(),
      author: await this.getElementText(this.voteDisplay.authorInfo).catch(() => ''),
      duration: await this.getElementText(this.voteDisplay.voteDuration).catch(() => '')
    };

    return voteInfo;
  }

  async getTotalVoteCount() {
    try {
      const countText = await this.getElementText(this.voteDisplay.totalVotes);
      const match = countText.match(/(\d+)/);
      return match ? parseInt(match[1]) : 0;
    } catch {
      return 0;
    }
  }

  async getVoteOptions() {
    const optionElements = await this.page.locator(this.votingInterface.voteOption).all();
    const options = [];

    for (const [index, option] of optionElements.entries()) {
      const optionData = await option.evaluate((el, idx) => {
        const label = el.querySelector('[data-testid="option-label"], .option-label');
        const description = el.querySelector('[data-testid="option-description"], .option-description');
        const image = el.querySelector('[data-testid="option-image"], .option-image');
        const radio = el.querySelector('input[type="radio"]');
        const checkbox = el.querySelector('input[type="checkbox"]');

        return {
          index: idx,
          id: radio?.value || checkbox?.value || '',
          text: label?.textContent?.trim() || '',
          description: description?.textContent?.trim() || '',
          hasImage: !!image,
          imageUrl: image?.src || '',
          isSelectable: !!(radio || checkbox),
          isSelected: radio?.checked || checkbox?.checked || false,
          isDisabled: radio?.disabled || checkbox?.disabled || false
        };
      }, index);

      options.push(optionData);
    }

    return options;
  }

  /**
   * Voting Methods
   */
  async selectOption(optionIndex) {
    const options = await this.page.locator(this.votingInterface.voteOption).all();

    if (optionIndex >= options.length) {
      throw new Error(`Option index ${optionIndex} is out of range`);
    }

    const option = options[optionIndex];
    const startTime = Date.now();

    // Try radio button first, then checkbox
    const radioButton = option.locator('input[type="radio"]');
    const checkboxButton = option.locator('input[type="checkbox"]');

    if (await radioButton.count() > 0) {
      await radioButton.click();
    } else if (await checkboxButton.count() > 0) {
      await checkboxButton.click();
    } else {
      // Click the option container if no input found
      await option.click();
    }

    // Wait for selection visual feedback
    await this.page.waitForTimeout(200);

    const selectionTime = Date.now() - startTime;
    return {
      optionIndex,
      selectionTime,
      isAcceptable: selectionTime < PERFORMANCE_FIXTURES.THRESHOLDS.FIRST_INPUT_DELAY.ACCEPTABLE
    };
  }

  async selectMultipleOptions(optionIndices) {
    const results = [];

    for (const index of optionIndices) {
      const result = await this.selectOption(index);
      results.push(result);
    }

    return results;
  }

  async clearSelection() {
    if (await this.isElementVisible(this.votingInterface.clearSelectionButton)) {
      await this.clickElement(this.votingInterface.clearSelectionButton);
      await this.page.waitForTimeout(200);
    } else {
      // Manually clear by unchecking selected options
      const selectedOptions = await this.page.locator(this.votingInterface.selectedOption).all();
      for (const option of selectedOptions) {
        await option.click();
      }
    }
  }

  async getSelectedOptions() {
    const options = await this.getVoteOptions();
    return options.filter(option => option.isSelected);
  }

  async submitVote() {
    const selectedOptions = await this.getSelectedOptions();

    if (selectedOptions.length === 0) {
      throw new Error('No options selected for voting');
    }

    const startTime = Date.now();

    await this.clickElement(this.votingInterface.submitButton);

    // Handle confirmation modal if present
    if (await this.isElementVisible(this.confirmationElements.confirmationModal, 2000)) {
      await this.clickElement(this.confirmationElements.confirmSubmitButton);
    }

    // Wait for submission to complete
    const result = await Promise.race([
      this.waitForElement(this.confirmationElements.successMessage, 'visible', 10000).then(() => 'success'),
      this.waitForElement(this.confirmationElements.errorMessage, 'visible', 5000).then(() => 'error'),
      this.waitForElement(this.confirmationElements.thankYouMessage, 'visible', 10000).then(() => 'thank_you'),
      this.page.waitForTimeout(10000).then(() => 'timeout')
    ]);

    const submissionTime = Date.now() - startTime;

    return {
      result,
      selectedOptions,
      submissionTime,
      isAcceptable: submissionTime < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.VOTE_SUBMISSION,
      url: this.page.url()
    };
  }

  /**
   * Authentication and User Management
   */
  async isLoginRequired() {
    return await this.isElementVisible(this.userInterface.loginPrompt);
  }

  async loginToVote(credentials) {
    if (await this.isLoginRequired()) {
      await this.clickElement(this.userInterface.loginButton);

      // Handle login modal or redirect
      if (await this.waitForURL('**/login', 3000).catch(() => false)) {
        // Redirected to login page
        await this.fillField('input[name="email"], input[type="email"]', credentials.email);
        await this.fillField('input[name="password"], input[type="password"]', credentials.password);
        await this.clickElement('button[type="submit"], button:has-text("Login")');
        await this.waitForURL('**/vote/**', 10000);
      } else {
        // Login modal
        await this.waitForElement('.login-modal, [data-testid="login-modal"]');
        await this.fillField('.login-modal input[name="email"]', credentials.email);
        await this.fillField('.login-modal input[name="password"]', credentials.password);
        await this.clickElement('.login-modal button[type="submit"]');
        await this.page.waitForFunction(() => {
          return !document.querySelector('.login-modal, [data-testid="login-modal"]');
        }, { timeout: 10000 });
      }

      await this.waitForVoteToLoad();
    }
  }

  async toggleAnonymousVoting(enabled = true) {
    if (await this.isElementVisible(this.userInterface.anonymousVoteToggle)) {
      const toggle = this.page.locator(this.userInterface.anonymousVoteToggle);
      const isChecked = await toggle.isChecked();

      if ((enabled && !isChecked) || (!enabled && isChecked)) {
        await toggle.click();
        await this.page.waitForTimeout(200);
      }
    }
  }

  async fillVoterInformation(voterData) {
    if (voterData.name && await this.isElementVisible(this.userInterface.voterNameInput)) {
      await this.fillField(this.userInterface.voterNameInput, voterData.name);
    }

    if (voterData.email && await this.isElementVisible(this.userInterface.voterEmailInput)) {
      await this.fillField(this.userInterface.voterEmailInput, voterData.email);
    }
  }

  /**
   * Results Display Methods
   */
  async getVoteResults() {
    await this.showResults();

    const resultElements = await this.page.locator(this.resultsDisplay.resultItem).all();
    const results = [];

    for (const [index, result] of resultElements.entries()) {
      const resultData = await result.evaluate((el, idx) => {
        const percentage = el.querySelector('[data-testid="result-percentage"], .result-percentage');
        const count = el.querySelector('[data-testid="result-count"], .result-count');
        const label = el.querySelector('[data-testid="option-label"], .option-label');
        const bar = el.querySelector('[data-testid="result-bar"], .result-bar');

        return {
          index: idx,
          option: label?.textContent?.trim() || '',
          percentage: percentage?.textContent?.trim() || '0%',
          count: count?.textContent?.trim() || '0',
          percentageValue: parseFloat(percentage?.textContent?.replace('%', '') || '0'),
          countValue: parseInt(count?.textContent?.match(/\d+/)?.[0] || '0'),
          barWidth: bar?.style.width || '0%',
          isWinning: el.classList.contains('winning-option') || el.hasAttribute('data-winning')
        };
      }, index);

      results.push(resultData);
    }

    return results.sort((a, b) => b.percentageValue - a.percentageValue);
  }

  async showResults() {
    if (await this.isElementVisible(this.resultsDisplay.showResultsButton)) {
      await this.clickElement(this.resultsDisplay.showResultsButton);
      await this.waitForElement(this.resultsDisplay.resultsContainer, 'visible', 5000);
    }
  }

  async hideResults() {
    if (await this.isElementVisible(this.resultsDisplay.hideResultsButton)) {
      await this.clickElement(this.resultsDisplay.hideResultsButton);
      await this.page.waitForFunction(() => {
        const container = document.querySelector('[data-testid="results-container"], .results-container');
        return !container || !container.offsetParent;
      }, { timeout: 5000 });
    }
  }

  async getWinningOption() {
    const results = await this.getVoteResults();
    return results.find(result => result.isWinning) || results[0];
  }

  /**
   * Social Sharing Methods
   */
  async shareVote() {
    await this.clickElement(this.socialFeatures.shareButton);
    await this.waitForElement(this.socialFeatures.shareModal);

    const shareUrl = await this.getElementText(this.socialFeatures.shareUrl).catch(() => '');

    return {
      shareUrl,
      hasModal: true
    };
  }

  async copyShareUrl() {
    await this.shareVote();
    await this.clickElement(this.socialFeatures.copyUrlButton);

    // Check if copy was successful
    const copiedUrl = await this.page.evaluate(() => {
      return navigator.clipboard.readText().catch(() => '');
    });

    return copiedUrl;
  }

  async shareToSocialMedia(platform) {
    await this.shareVote();

    const platformSelectors = {
      facebook: this.socialFeatures.facebookShare,
      twitter: this.socialFeatures.twitterShare,
      linkedin: this.socialFeatures.linkedinShare,
      email: this.socialFeatures.emailShare
    };

    const selector = platformSelectors[platform.toLowerCase()];
    if (!selector) {
      throw new Error(`Unknown social platform: ${platform}`);
    }

    if (await this.isElementVisible(selector)) {
      await this.clickElement(selector);

      // Note: Actual social sharing opens new windows/tabs which Playwright handles differently
      // This method initiates the sharing process
      return true;
    }

    return false;
  }

  /**
   * Comments and Interaction Methods
   */
  async addComment(commentText) {
    if (!await this.isElementVisible(this.commentsSection.addCommentForm)) {
      // Try to show comments section
      if (await this.isElementVisible(this.commentsSection.showCommentsButton)) {
        await this.clickElement(this.commentsSection.showCommentsButton);
        await this.waitForElement(this.commentsSection.addCommentForm);
      }
    }

    await this.fillField(this.commentsSection.commentInput, commentText);
    await this.clickElement(this.commentsSection.submitCommentButton);

    // Wait for comment to be added
    await this.page.waitForTimeout(2000);

    return await this.getComments();
  }

  async getComments() {
    const commentElements = await this.page.locator(this.commentsSection.commentItem).all();
    const comments = [];

    for (const [index, comment] of commentElements.entries()) {
      const commentData = await comment.evaluate((el, idx) => {
        const text = el.querySelector('[data-testid="comment-text"], .comment-text');
        const author = el.querySelector('[data-testid="comment-author"], .comment-author');
        const date = el.querySelector('[data-testid="comment-date"], .comment-date');

        return {
          index: idx,
          text: text?.textContent?.trim() || '',
          author: author?.textContent?.trim() || '',
          date: date?.textContent?.trim() || '',
          timestamp: date?.getAttribute('datetime') || ''
        };
      }, index);

      comments.push(commentData);
    }

    return comments;
  }

  /**
   * Mobile and Responsive Functionality
   */
  async validateMobileVoting() {
    // Set mobile viewport
    await this.page.setViewportSize({ width: 375, height: 667 });
    await this.page.waitForTimeout(500);

    const validation = {
      viewport: { width: 375, height: 667 },
      optionsVisible: await this.isElementVisible(this.votingInterface.optionsContainer),
      submitButtonVisible: await this.isElementVisible(this.votingInterface.submitButton),
      mobileMenuVisible: await this.isElementVisible(this.mobileElements.mobileMenu),
      hasSwipeSupport: await this.validateSwipeSupport(),
      touchInteractions: await this.validateTouchInteractions()
    };

    return validation;
  }

  async validateSwipeSupport() {
    const options = await this.page.locator(this.votingInterface.voteOption).all();

    if (options.length < 2) {
      return { supported: false, reason: 'Not enough options to test' };
    }

    // Test swipe gesture on first option
    const firstOption = options[0];
    const boundingBox = await firstOption.boundingBox();

    if (!boundingBox) {
      return { supported: false, reason: 'Option not visible' };
    }

    // Simulate swipe gesture
    await this.page.mouse.move(boundingBox.x + 50, boundingBox.y + boundingBox.height / 2);
    await this.page.mouse.down();
    await this.page.mouse.move(boundingBox.x + boundingBox.width - 50, boundingBox.y + boundingBox.height / 2);
    await this.page.mouse.up();

    await this.page.waitForTimeout(500);

    // Check if option was selected by swipe
    const isSelected = await firstOption.evaluate(el => {
      const radio = el.querySelector('input[type="radio"]');
      const checkbox = el.querySelector('input[type="checkbox"]');
      return radio?.checked || checkbox?.checked || el.classList.contains('selected');
    });

    return { supported: isSelected, tested: true };
  }

  async validateTouchInteractions() {
    const interactions = [];

    // Test touch on vote options
    const options = await this.page.locator(this.votingInterface.voteOption).all();
    for (const [index, option] of options.entries().slice(0, 2)) {
      const boundingBox = await option.boundingBox();

      if (boundingBox) {
        await this.page.touchscreen.tap(
          boundingBox.x + boundingBox.width / 2,
          boundingBox.y + boundingBox.height / 2
        );

        await this.page.waitForTimeout(200);

        const isSelected = await option.evaluate(el => {
          const radio = el.querySelector('input[type="radio"]');
          const checkbox = el.querySelector('input[type="checkbox"]');
          return radio?.checked || checkbox?.checked || el.classList.contains('selected');
        });

        interactions.push({
          optionIndex: index,
          touchWorked: isSelected,
          boundingBox
        });
      }
    }

    return interactions;
  }

  /**
   * Real-time Updates and Performance
   */
  async enableAutoRefresh() {
    if (await this.isElementVisible(this.realTimeElements.autoRefreshToggle)) {
      const toggle = this.page.locator(this.realTimeElements.autoRefreshToggle);
      if (!await toggle.isChecked()) {
        await toggle.click();
      }
    }
  }

  async refreshResults() {
    if (await this.isElementVisible(this.realTimeElements.refreshButton)) {
      const beforeCount = await this.getTotalVoteCount();
      await this.clickElement(this.realTimeElements.refreshButton);

      // Wait for refresh to complete
      await this.page.waitForTimeout(1000);

      const afterCount = await this.getTotalVoteCount();
      return { beforeCount, afterCount, updated: beforeCount !== afterCount };
    }

    return { updated: false };
  }

  async monitorLiveUpdates(duration = 10000) {
    const updates = [];
    const startTime = Date.now();

    while (Date.now() - startTime < duration) {
      const currentCount = await this.getTotalVoteCount();
      updates.push({
        timestamp: Date.now(),
        voteCount: currentCount
      });

      await this.page.waitForTimeout(1000);
    }

    return {
      updates,
      hasLiveUpdates: updates.some((update, index) =>
        index > 0 && update.voteCount !== updates[index - 1].voteCount
      )
    };
  }

  /**
   * Performance Monitoring
   */
  async measureVotingPerformance() {
    const metrics = {};

    // Measure option selection performance
    const selectionStart = Date.now();
    await this.selectOption(0);
    metrics.optionSelection = Date.now() - selectionStart;

    // Measure vote submission performance
    const submissionStart = Date.now();
    const submissionResult = await this.submitVote();
    metrics.voteSubmission = submissionResult.submissionTime;

    // Measure results loading performance
    const resultsStart = Date.now();
    await this.getVoteResults();
    metrics.resultsLoading = Date.now() - resultsStart;

    return {
      ...metrics,
      optionSelectionAcceptable: metrics.optionSelection < PERFORMANCE_FIXTURES.THRESHOLDS.FIRST_INPUT_DELAY.ACCEPTABLE,
      voteSubmissionAcceptable: metrics.voteSubmission < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.VOTE_SUBMISSION,
      resultsLoadingAcceptable: metrics.resultsLoading < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.DATA_RETRIEVAL
    };
  }

  /**
   * Material Design Validation for Voting Interface
   */
  async validateVotingMaterialDesign() {
    const baseValidation = await super.validateMaterialDesign();

    const votingValidation = {
      voteOptions: await this.validateVoteOptionDesign(),
      submitButton: await this.validateSubmitButtonDesign(),
      resultsDisplay: await this.validateResultsDesign(),
      socialSharing: await this.validateSocialSharingDesign()
    };

    return {
      ...baseValidation,
      voting: votingValidation
    };
  }

  async validateVoteOptionDesign() {
    const options = await this.page.locator(this.votingInterface.voteOption).all();
    const validations = [];

    for (const option of options.slice(0, 3)) {
      const styles = await option.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          padding: computed.padding,
          borderRadius: computed.borderRadius,
          border: computed.border,
          cursor: computed.cursor,
          transition: computed.transition
        };
      });

      validations.push({
        hasMinHeight: parseInt(styles.minHeight) >= 48,
        hasProperPadding: parseInt(styles.padding) >= 16,
        isInteractive: styles.cursor === 'pointer',
        hasTransition: styles.transition !== 'none',
        hasRoundedCorners: parseInt(styles.borderRadius) >= 4,
        styles
      });
    }

    return {
      optionCount: options.length,
      validations,
      allOptionsValid: validations.every(v => v.hasMinHeight && v.hasProperPadding && v.isInteractive)
    };
  }

  async validateSubmitButtonDesign() {
    if (await this.isElementVisible(this.votingInterface.submitButton)) {
      const button = this.page.locator(this.votingInterface.submitButton);
      const styles = await button.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          padding: computed.padding,
          backgroundColor: computed.backgroundColor,
          borderRadius: computed.borderRadius,
          fontWeight: computed.fontWeight
        };
      });

      return {
        visible: true,
        hasProperHeight: parseInt(styles.minHeight) >= 36,
        hasProperPadding: parseInt(styles.padding) >= 16,
        hasRoundedCorners: parseInt(styles.borderRadius) >= 4,
        isBold: parseInt(styles.fontWeight) >= 600,
        styles
      };
    }

    return { visible: false };
  }

  async validateResultsDesign() {
    await this.showResults();

    const resultBars = await this.page.locator(this.resultsDisplay.resultBar).all();
    const validations = [];

    for (const bar of resultBars.slice(0, 3)) {
      const styles = await bar.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          height: computed.height,
          borderRadius: computed.borderRadius,
          backgroundColor: computed.backgroundColor,
          transition: computed.transition
        };
      });

      validations.push({
        hasProperHeight: parseInt(styles.height) >= 8,
        hasRoundedCorners: parseInt(styles.borderRadius) >= 2,
        hasTransition: styles.transition !== 'none',
        styles
      });
    }

    return {
      barCount: resultBars.length,
      validations,
      allBarsValid: validations.every(v => v.hasProperHeight && v.hasRoundedCorners)
    };
  }

  async validateSocialSharingDesign() {
    if (await this.isElementVisible(this.socialFeatures.shareButton)) {
      await this.shareVote();

      const socialButtons = await this.page.locator(this.socialFeatures.socialShareButtons + ' button').all();
      const validations = [];

      for (const button of socialButtons) {
        const styles = await button.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            minHeight: computed.minHeight,
            minWidth: computed.minWidth,
            borderRadius: computed.borderRadius
          };
        });

        validations.push({
          hasProperSize: parseInt(styles.minHeight) >= 32 && parseInt(styles.minWidth) >= 32,
          hasRoundedCorners: parseInt(styles.borderRadius) >= 16,
          styles
        });
      }

      return {
        buttonCount: socialButtons.length,
        validations
      };
    }

    return { visible: false };
  }
}
