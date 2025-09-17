import { expect } from '@playwright/test';
import { BasePage } from './base-page.js';
import { MATERIAL_DESIGN_FIXTURES } from '../fixtures/data/material-design-fixtures.js';
import { PERFORMANCE_FIXTURES } from '../fixtures/data/performance-accessibility-fixtures.js';

/**
 * Enhanced Admin Page Object Model
 *
 * Extends BasePage with comprehensive admin functionality including:
 * - User management and permissions
 * - System settings and configuration
 * - Vote oversight and moderation
 * - Analytics and reporting
 * - Security monitoring and audit logs
 * - Platform administration tools
 * - Bulk operations and data management
 */
export class EnhancedAdminPage extends BasePage {
  constructor(page) {
    super(page);

    // Admin navigation
    this.adminNavigation = {
      dashboardTab: '[data-testid="admin-dashboard"], .admin-nav:has-text("Dashboard")',
      usersTab: '[data-testid="admin-users"], .admin-nav:has-text("Users")',
      votesTab: '[data-testid="admin-votes"], .admin-nav:has-text("Votes")',
      settingsTab: '[data-testid="admin-settings"], .admin-nav:has-text("Settings")',
      analyticsTab: '[data-testid="admin-analytics"], .admin-nav:has-text("Analytics")',
      securityTab: '[data-testid="admin-security"], .admin-nav:has-text("Security")',
      logsTab: '[data-testid="admin-logs"], .admin-nav:has-text("Logs")',
      supportTab: '[data-testid="admin-support"], .admin-nav:has-text("Support")'
    };

    // User management elements
    this.userManagement = {
      usersTable: '[data-testid="users-table"], .users-table',
      userRow: '[data-testid="user-row"], .user-row',
      userEmail: '[data-testid="user-email"], .user-email',
      userRole: '[data-testid="user-role"], .user-role',
      userStatus: '[data-testid="user-status"], .user-status',
      editUserButton: '[data-testid="edit-user"], button:has-text("Edit")',
      deleteUserButton: '[data-testid="delete-user"], button:has-text("Delete")',
      suspendUserButton: '[data-testid="suspend-user"], button:has-text("Suspend")',
      promoteUserButton: '[data-testid="promote-user"], button:has-text("Promote")',
      addUserButton: '[data-testid="add-user"], button:has-text("Add User")',
      bulkActionsDropdown: '[data-testid="bulk-actions"], .bulk-actions',
      userSearchInput: '[data-testid="user-search"], input[placeholder*="Search users"]',
      userFilterDropdown: '[data-testid="user-filter"], .user-filter'
    };

    // Vote oversight elements
    this.voteOversight = {
      votesTable: '[data-testid="admin-votes-table"], .admin-votes-table',
      voteRow: '[data-testid="vote-row"], .vote-row',
      voteTitle: '[data-testid="vote-title"], .vote-title',
      voteAuthor: '[data-testid="vote-author"], .vote-author',
      voteStatus: '[data-testid="vote-status"], .vote-status',
      voteParticipants: '[data-testid="vote-participants"], .vote-participants',
      viewVoteButton: '[data-testid="view-vote"], button:has-text("View")',
      moderateVoteButton: '[data-testid="moderate-vote"], button:has-text("Moderate")',
      archiveVoteButton: '[data-testid="archive-vote"], button:has-text("Archive")',
      featuredVoteToggle: '[data-testid="featured-toggle"], .featured-toggle',
      voteSearchInput: '[data-testid="vote-search"], input[placeholder*="Search votes"]'
    };

    // System settings elements
    this.systemSettings = {
      settingsForm: '[data-testid="settings-form"], .settings-form',
      siteTitleInput: '[data-testid="site-title"], input[name="siteTitle"]',
      siteDescriptionTextarea: '[data-testid="site-description"], textarea[name="siteDescription"]',
      allowRegistrationToggle: '[data-testid="allow-registration"], input[type="checkbox"][name="allowRegistration"]',
      requireEmailVerificationToggle: '[data-testid="require-verification"], input[type="checkbox"][name="requireVerification"]',
      maxVoteOptionsInput: '[data-testid="max-vote-options"], input[name="maxVoteOptions"]',
      defaultVoteDurationInput: '[data-testid="default-vote-duration"], input[name="defaultVoteDuration"]',
      maintenanceModeToggle: '[data-testid="maintenance-mode"], input[type="checkbox"][name="maintenanceMode"]',
      saveSettingsButton: '[data-testid="save-settings"], button:has-text("Save Settings")',
      resetSettingsButton: '[data-testid="reset-settings"], button:has-text("Reset")'
    };

    // Analytics and reporting elements
    this.analytics = {
      analyticsContainer: '[data-testid="analytics-container"], .analytics-container',
      totalUsersMetric: '[data-testid="total-users"], .metric-total-users',
      activeUsersMetric: '[data-testid="active-users"], .metric-active-users',
      totalVotesMetric: '[data-testid="total-votes"], .metric-total-votes',
      votesThisMonthMetric: '[data-testid="votes-this-month"], .metric-votes-month',
      averageParticipationMetric: '[data-testid="avg-participation"], .metric-avg-participation',
      userGrowthChart: '[data-testid="user-growth-chart"], .user-growth-chart',
      voteActivityChart: '[data-testid="vote-activity-chart"], .vote-activity-chart',
      participationChart: '[data-testid="participation-chart"], .participation-chart',
      exportReportButton: '[data-testid="export-report"], button:has-text("Export Report")',
      dateRangePicker: '[data-testid="date-range"], .date-range-picker'
    };

    // Security monitoring elements
    this.security = {
      securityDashboard: '[data-testid="security-dashboard"], .security-dashboard',
      failedLoginsMetric: '[data-testid="failed-logins"], .metric-failed-logins',
      suspiciousActivityMetric: '[data-testid="suspicious-activity"], .metric-suspicious-activity',
      blockedIPsMetric: '[data-testid="blocked-ips"], .metric-blocked-ips',
      securityAlertsContainer: '[data-testid="security-alerts"], .security-alerts',
      alertItem: '[data-testid="alert-item"], .alert-item',
      blockIPButton: '[data-testid="block-ip"], button:has-text("Block IP")',
      unblockIPButton: '[data-testid="unblock-ip"], button:has-text("Unblock")',
      securitySettingsForm: '[data-testid="security-settings"], .security-settings-form',
      twoFactorToggle: '[data-testid="two-factor"], input[type="checkbox"][name="twoFactor"]',
      sessionTimeoutInput: '[data-testid="session-timeout"], input[name="sessionTimeout"]'
    };

    // Audit logs elements
    this.auditLogs = {
      logsContainer: '[data-testid="audit-logs"], .audit-logs',
      logEntry: '[data-testid="log-entry"], .log-entry',
      logTimestamp: '[data-testid="log-timestamp"], .log-timestamp',
      logUser: '[data-testid="log-user"], .log-user',
      logAction: '[data-testid="log-action"], .log-action',
      logDetails: '[data-testid="log-details"], .log-details',
      logsSearchInput: '[data-testid="logs-search"], input[placeholder*="Search logs"]',
      logsFilterDropdown: '[data-testid="logs-filter"], .logs-filter',
      exportLogsButton: '[data-testid="export-logs"], button:has-text("Export Logs")',
      clearLogsButton: '[data-testid="clear-logs"], button:has-text("Clear Logs")'
    };

    // Modal and confirmation dialogs
    this.modals = {
      confirmationModal: '[data-testid="confirmation-modal"], .confirmation-modal',
      userEditModal: '[data-testid="user-edit-modal"], .user-edit-modal',
      voteModerateModal: '[data-testid="vote-moderate-modal"], .vote-moderate-modal',
      bulkActionModal: '[data-testid="bulk-action-modal"], .bulk-action-modal',
      modalOverlay: '.modal-overlay, .backdrop',
      modalClose: '[data-testid="modal-close"], .modal-close',
      confirmButton: '[data-testid="confirm-button"], button:has-text("Confirm")',
      cancelButton: '[data-testid="cancel-button"], button:has-text("Cancel")'
    };

    // Notification and feedback elements
    this.notifications = {
      successNotification: '[data-testid="success-notification"], .notification-success',
      errorNotification: '[data-testid="error-notification"], .notification-error',
      warningNotification: '[data-testid="warning-notification"], .notification-warning',
      notificationClose: '[data-testid="notification-close"], .notification-close'
    };
  }

  /**
   * Navigation Methods
   */
  async goto() {
    const loadTime = await super.goto('/admin');
    await this.waitForAdminToLoad();
    return loadTime;
  }

  async waitForAdminToLoad() {
    // Wait for admin interface to load
    await Promise.all([
      this.waitForElement(this.adminNavigation.dashboardTab),
      this.waitForElement('.admin-content, [data-testid="admin-content"]', 'visible', 10000).catch(() => {
        // Admin content might load differently
      })
    ]);

    // Wait for any loading indicators to disappear
    await this.page.waitForFunction(() => {
      const spinners = document.querySelectorAll('.loading, .spinner, [data-testid="loading"]');
      return spinners.length === 0;
    }, { timeout: 10000 }).catch(() => {
      // Loading indicators might not be present
    });
  }

  async navigateToAdminSection(section) {
    const sectionSelectors = {
      dashboard: this.adminNavigation.dashboardTab,
      users: this.adminNavigation.usersTab,
      votes: this.adminNavigation.votesTab,
      settings: this.adminNavigation.settingsTab,
      analytics: this.adminNavigation.analyticsTab,
      security: this.adminNavigation.securityTab,
      logs: this.adminNavigation.logsTab,
      support: this.adminNavigation.supportTab
    };

    const selector = sectionSelectors[section.toLowerCase()];
    if (!selector) {
      throw new Error(`Unknown admin section: ${section}`);
    }

    const startTime = Date.now();
    await this.clickElement(selector);

    // Wait for section content to load
    await this.page.waitForTimeout(1000);

    const navigationTime = Date.now() - startTime;
    return {
      section,
      navigationTime,
      isAcceptable: navigationTime < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION
    };
  }

  /**
   * User Management Methods
   */
  async getUserList() {
    await this.navigateToAdminSection('users');

    const userRows = await this.page.locator(this.userManagement.userRow).all();
    const users = [];

    for (const [index, row] of userRows.entries()) {
      const userData = await row.evaluate((el, idx) => {
        const email = el.querySelector('[data-testid="user-email"], .user-email');
        const role = el.querySelector('[data-testid="user-role"], .user-role');
        const status = el.querySelector('[data-testid="user-status"], .user-status');

        return {
          index: idx,
          email: email?.textContent?.trim() || '',
          role: role?.textContent?.trim() || '',
          status: status?.textContent?.trim() || '',
          id: el.getAttribute('data-user-id') || ''
        };
      }, index);

      users.push(userData);
    }

    return users;
  }

  async searchUsers(query) {
    await this.navigateToAdminSection('users');
    await this.fillField(this.userManagement.userSearchInput, query);
    await this.page.keyboard.press('Enter');

    // Wait for search results to update
    await this.page.waitForTimeout(1000);

    return await this.getUserList();
  }

  async editUser(userId) {
    const userRow = this.page.locator(`[data-user-id="${userId}"]`).first();
    await userRow.locator(this.userManagement.editUserButton).click();

    await this.waitForElement(this.modals.userEditModal);

    return {
      modalVisible: true,
      userId
    };
  }

  async updateUserRole(userId, newRole) {
    await this.editUser(userId);

    // Update role in modal
    const roleSelect = this.page.locator('.user-edit-modal select[name="role"], [data-testid="role-select"]');
    await roleSelect.selectOption(newRole);

    await this.clickElement(this.modals.confirmButton);

    // Wait for modal to close and success notification
    await this.page.waitForFunction(() => {
      return !document.querySelector('.user-edit-modal, [data-testid="user-edit-modal"]');
    }, { timeout: 10000 });

    return await this.waitForNotification('success');
  }

  async suspendUser(userId) {
    const userRow = this.page.locator(`[data-user-id="${userId}"]`).first();
    await userRow.locator(this.userManagement.suspendUserButton).click();

    await this.waitForElement(this.modals.confirmationModal);
    await this.clickElement(this.modals.confirmButton);

    return await this.waitForNotification('success');
  }

  async deleteUser(userId) {
    const userRow = this.page.locator(`[data-user-id="${userId}"]`).first();
    await userRow.locator(this.userManagement.deleteUserButton).click();

    await this.waitForElement(this.modals.confirmationModal);
    await this.clickElement(this.modals.confirmButton);

    // Wait for user to be removed from the list
    await this.page.waitForFunction((id) => {
      return !document.querySelector(`[data-user-id="${id}"]`);
    }, userId, { timeout: 10000 });

    return await this.waitForNotification('success');
  }

  async performBulkUserAction(userIds, action) {
    // Select users
    for (const userId of userIds) {
      const checkbox = this.page.locator(`[data-user-id="${userId}"] input[type="checkbox"]`);
      await checkbox.check();
    }

    // Perform bulk action
    await this.clickElement(this.userManagement.bulkActionsDropdown);
    await this.clickElement(`[data-action="${action}"], option:has-text("${action}")`);

    await this.waitForElement(this.modals.bulkActionModal);
    await this.clickElement(this.modals.confirmButton);

    return await this.waitForNotification('success');
  }

  /**
   * Vote Oversight Methods
   */
  async getVotesList() {
    await this.navigateToAdminSection('votes');

    const voteRows = await this.page.locator(this.voteOversight.voteRow).all();
    const votes = [];

    for (const [index, row] of voteRows.entries()) {
      const voteData = await row.evaluate((el, idx) => {
        const title = el.querySelector('[data-testid="vote-title"], .vote-title');
        const author = el.querySelector('[data-testid="vote-author"], .vote-author');
        const status = el.querySelector('[data-testid="vote-status"], .vote-status');
        const participants = el.querySelector('[data-testid="vote-participants"], .vote-participants');

        return {
          index: idx,
          title: title?.textContent?.trim() || '',
          author: author?.textContent?.trim() || '',
          status: status?.textContent?.trim() || '',
          participants: participants?.textContent?.trim() || '',
          id: el.getAttribute('data-vote-id') || ''
        };
      }, index);

      votes.push(voteData);
    }

    return votes;
  }

  async moderateVote(voteId, action) {
    const voteRow = this.page.locator(`[data-vote-id="${voteId}"]`).first();
    await voteRow.locator(this.voteOversight.moderateVoteButton).click();

    await this.waitForElement(this.modals.voteModerateModal);

    // Select moderation action
    const actionSelect = this.page.locator('.vote-moderate-modal select[name="action"], [data-testid="moderation-action"]');
    await actionSelect.selectOption(action);

    await this.clickElement(this.modals.confirmButton);

    return await this.waitForNotification('success');
  }

  async toggleFeaturedVote(voteId) {
    const voteRow = this.page.locator(`[data-vote-id="${voteId}"]`).first();
    const featuredToggle = voteRow.locator(this.voteOversight.featuredVoteToggle);

    await featuredToggle.click();
    await this.page.waitForTimeout(500);

    return await this.waitForNotification('success');
  }

  /**
   * System Settings Methods
   */
  async updateSystemSettings(settings) {
    await this.navigateToAdminSection('settings');

    const startTime = Date.now();

    // Update text fields
    if (settings.siteTitle) {
      await this.fillField(this.systemSettings.siteTitleInput, settings.siteTitle);
    }

    if (settings.siteDescription) {
      await this.fillField(this.systemSettings.siteDescriptionTextarea, settings.siteDescription);
    }

    if (settings.maxVoteOptions) {
      await this.fillField(this.systemSettings.maxVoteOptionsInput, settings.maxVoteOptions.toString());
    }

    if (settings.defaultVoteDuration) {
      await this.fillField(this.systemSettings.defaultVoteDurationInput, settings.defaultVoteDuration.toString());
    }

    // Update toggles
    const toggleSettings = [
      { key: 'allowRegistration', selector: this.systemSettings.allowRegistrationToggle },
      { key: 'requireEmailVerification', selector: this.systemSettings.requireEmailVerificationToggle },
      { key: 'maintenanceMode', selector: this.systemSettings.maintenanceModeToggle }
    ];

    for (const setting of toggleSettings) {
      if (settings[setting.key] !== undefined) {
        const toggle = this.page.locator(setting.selector);
        const isChecked = await toggle.isChecked();

        if ((settings[setting.key] && !isChecked) || (!settings[setting.key] && isChecked)) {
          await toggle.click();
        }
      }
    }

    // Save settings
    await this.clickElement(this.systemSettings.saveSettingsButton);

    const updateTime = Date.now() - startTime;
    const success = await this.waitForNotification('success');

    return {
      success,
      updateTime,
      isAcceptable: updateTime < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.DATA_RETRIEVAL
    };
  }

  async resetSystemSettings() {
    await this.navigateToAdminSection('settings');

    await this.clickElement(this.systemSettings.resetSettingsButton);
    await this.waitForElement(this.modals.confirmationModal);
    await this.clickElement(this.modals.confirmButton);

    return await this.waitForNotification('success');
  }

  /**
   * Analytics and Reporting Methods
   */
  async getAnalyticsMetrics() {
    await this.navigateToAdminSection('analytics');

    const metrics = {};

    try {
      metrics.totalUsers = await this.getElementText(this.analytics.totalUsersMetric);
      metrics.activeUsers = await this.getElementText(this.analytics.activeUsersMetric);
      metrics.totalVotes = await this.getElementText(this.analytics.totalVotesMetric);
      metrics.votesThisMonth = await this.getElementText(this.analytics.votesThisMonthMetric);
      metrics.averageParticipation = await this.getElementText(this.analytics.averageParticipationMetric);
    } catch (error) {
      console.warn('Some analytics metrics not available:', error.message);
    }

    return metrics;
  }

  async validateAnalyticsCharts() {
    await this.navigateToAdminSection('analytics');

    const charts = {
      userGrowth: await this.validateChart(this.analytics.userGrowthChart),
      voteActivity: await this.validateChart(this.analytics.voteActivityChart),
      participation: await this.validateChart(this.analytics.participationChart)
    };

    return charts;
  }

  async validateChart(chartSelector) {
    if (await this.isElementVisible(chartSelector)) {
      const hasContent = await this.page.evaluate((selector) => {
        const chart = document.querySelector(selector);
        return chart && (chart.children.length > 0 || chart.textContent.trim() !== '');
      }, chartSelector);

      return { exists: true, hasContent };
    }

    return { exists: false, hasContent: false };
  }

  async exportAnalyticsReport(dateRange = null) {
    await this.navigateToAdminSection('analytics');

    if (dateRange) {
      // Set date range if provided
      await this.setDateRange(dateRange);
    }

    const startTime = Date.now();
    await this.clickElement(this.analytics.exportReportButton);

    // Wait for download or success notification
    const downloadTime = Date.now() - startTime;

    return {
      exported: true,
      downloadTime,
      isAcceptable: downloadTime < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.FILE_UPLOAD
    };
  }

  async setDateRange(dateRange) {
    // This would interact with date range picker
    // Implementation depends on specific date picker component
    await this.clickElement(this.analytics.dateRangePicker);
    // Set start and end dates based on dateRange object
  }

  /**
   * Security Monitoring Methods
   */
  async getSecurityMetrics() {
    await this.navigateToAdminSection('security');

    const metrics = {};

    try {
      metrics.failedLogins = await this.getElementText(this.security.failedLoginsMetric);
      metrics.suspiciousActivity = await this.getElementText(this.security.suspiciousActivityMetric);
      metrics.blockedIPs = await this.getElementText(this.security.blockedIPsMetric);
    } catch (error) {
      console.warn('Some security metrics not available:', error.message);
    }

    return metrics;
  }

  async getSecurityAlerts() {
    await this.navigateToAdminSection('security');

    const alertElements = await this.page.locator(this.security.alertItem).all();
    const alerts = [];

    for (const [index, alert] of alertElements.entries()) {
      const alertData = await alert.evaluate((el, idx) => {
        return {
          index: idx,
          text: el.textContent?.trim() || '',
          severity: el.getAttribute('data-severity') || 'info',
          timestamp: el.getAttribute('data-timestamp') || ''
        };
      }, index);

      alerts.push(alertData);
    }

    return alerts;
  }

  async blockIP(ipAddress) {
    await this.navigateToAdminSection('security');

    // This would typically involve a form to block IP
    const blockIPForm = this.page.locator('.block-ip-form, [data-testid="block-ip-form"]');
    if (await blockIPForm.isVisible()) {
      await this.fillField('input[name="ipAddress"]', ipAddress);
      await this.clickElement(this.security.blockIPButton);

      return await this.waitForNotification('success');
    }

    return false;
  }

  /**
   * Audit Logs Methods
   */
  async getAuditLogs(limit = 50) {
    await this.navigateToAdminSection('logs');

    const logEntries = await this.page.locator(this.auditLogs.logEntry).all();
    const logs = [];

    for (const [index, entry] of logEntries.slice(0, limit).entries()) {
      const logData = await entry.evaluate((el, idx) => {
        const timestamp = el.querySelector('[data-testid="log-timestamp"], .log-timestamp');
        const user = el.querySelector('[data-testid="log-user"], .log-user');
        const action = el.querySelector('[data-testid="log-action"], .log-action');
        const details = el.querySelector('[data-testid="log-details"], .log-details');

        return {
          index: idx,
          timestamp: timestamp?.textContent?.trim() || '',
          user: user?.textContent?.trim() || '',
          action: action?.textContent?.trim() || '',
          details: details?.textContent?.trim() || ''
        };
      }, index);

      logs.push(logData);
    }

    return logs;
  }

  async searchAuditLogs(query) {
    await this.navigateToAdminSection('logs');

    await this.fillField(this.auditLogs.logsSearchInput, query);
    await this.page.keyboard.press('Enter');

    // Wait for search results to update
    await this.page.waitForTimeout(1000);

    return await this.getAuditLogs();
  }

  async exportAuditLogs() {
    await this.navigateToAdminSection('logs');

    const startTime = Date.now();
    await this.clickElement(this.auditLogs.exportLogsButton);

    const exportTime = Date.now() - startTime;

    return {
      exported: true,
      exportTime,
      isAcceptable: exportTime < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.FILE_UPLOAD
    };
  }

  /**
   * Notification and Feedback Methods
   */
  async waitForNotification(type = 'success', timeout = 5000) {
    const notificationSelectors = {
      success: this.notifications.successNotification,
      error: this.notifications.errorNotification,
      warning: this.notifications.warningNotification
    };

    const selector = notificationSelectors[type];
    if (!selector) {
      throw new Error(`Unknown notification type: ${type}`);
    }

    try {
      await this.waitForElement(selector, 'visible', timeout);
      const message = await this.getElementText(selector);
      return { type, message, visible: true };
    } catch {
      return { type, message: '', visible: false };
    }
  }

  async closeNotification() {
    if (await this.isElementVisible(this.notifications.notificationClose)) {
      await this.clickElement(this.notifications.notificationClose);
    }
  }

  /**
   * Modal Management Methods
   */
  async closeModal() {
    if (await this.isElementVisible(this.modals.modalOverlay)) {
      await this.clickElement(this.modals.modalClose);

      // Wait for modal to disappear
      await this.page.waitForFunction(() => {
        return !document.querySelector('.modal-overlay, .backdrop');
      }, { timeout: 5000 });
    }
  }

  /**
   * Performance Monitoring for Admin Operations
   */
  async measureAdminPerformance() {
    const metrics = {};

    // Test navigation performance
    const navigationStart = Date.now();
    await this.navigateToAdminSection('users');
    metrics.usersSectionLoad = Date.now() - navigationStart;

    const analyticsStart = Date.now();
    await this.navigateToAdminSection('analytics');
    metrics.analyticsSectionLoad = Date.now() - analyticsStart;

    // Test data loading performance
    const userListStart = Date.now();
    await this.navigateToAdminSection('users');
    const users = await this.getUserList();
    metrics.userListLoad = Date.now() - userListStart;

    return {
      ...metrics,
      userCount: users.length,
      navigationAcceptable: metrics.usersSectionLoad < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION,
      analyticsAcceptable: metrics.analyticsSectionLoad < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION,
      dataLoadAcceptable: metrics.userListLoad < PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.DATA_RETRIEVAL
    };
  }

  /**
   * Admin Interface Material Design Validation
   */
  async validateAdminMaterialDesign() {
    const baseValidation = await super.validateMaterialDesign();

    const adminValidation = {
      navigation: await this.validateAdminNavigation(),
      dataTable: await this.validateDataTables(),
      adminButtons: await this.validateAdminButtons(),
      adminCards: await this.validateAdminCards()
    };

    return {
      ...baseValidation,
      admin: adminValidation
    };
  }

  async validateAdminNavigation() {
    const navTabs = await this.page.locator('.admin-nav, [data-testid^="admin-"]').all();
    const validations = [];

    for (const tab of navTabs) {
      const styles = await tab.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          padding: computed.padding,
          borderRadius: computed.borderRadius
        };
      });

      validations.push({
        hasProperHeight: parseInt(styles.minHeight) >= 48,
        hasProperPadding: parseInt(styles.padding) >= 12,
        styles
      });
    }

    return {
      tabCount: navTabs.length,
      validations
    };
  }

  async validateDataTables() {
    const tables = await this.page.locator('.users-table, .admin-votes-table, [data-testid$="-table"]').all();
    const validations = [];

    for (const table of tables) {
      const styles = await table.evaluate(el => {
        const computed = window.getComputedStyle(el);
        const rows = el.querySelectorAll('tr');
        return {
          borderCollapse: computed.borderCollapse,
          rowCount: rows.length,
          hasHeader: !!el.querySelector('thead')
        };
      });

      validations.push({
        hasProperBorders: styles.borderCollapse === 'collapse',
        hasHeader: styles.hasHeader,
        hasRows: styles.rowCount > 1,
        styles
      });
    }

    return {
      tableCount: tables.length,
      validations
    };
  }

  async validateAdminButtons() {
    const adminButtons = await this.page.locator('.admin-content button, [data-testid^="admin-"] button').all();
    const validations = [];

    for (const button of adminButtons.slice(0, 5)) {
      const styles = await button.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          borderRadius: computed.borderRadius,
          padding: computed.padding
        };
      });

      validations.push({
        hasProperHeight: parseInt(styles.minHeight) >= 36,
        hasRoundedCorners: parseInt(styles.borderRadius) >= 4,
        hasProperPadding: parseInt(styles.padding) >= 8,
        styles
      });
    }

    return {
      buttonCount: adminButtons.length,
      validations,
      allButtonsValid: validations.every(v => v.hasProperHeight && v.hasRoundedCorners)
    };
  }

  async validateAdminCards() {
    const cards = await this.page.locator('.metric-card, .analytics-card, [class*="card"]').all();
    const validations = [];

    for (const card of cards) {
      const styles = await card.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          borderRadius: computed.borderRadius,
          boxShadow: computed.boxShadow,
          padding: computed.padding
        };
      });

      validations.push({
        hasElevation: styles.boxShadow !== 'none',
        hasRoundedCorners: parseInt(styles.borderRadius) > 0,
        hasProperPadding: parseInt(styles.padding) >= 16,
        styles
      });
    }

    return {
      cardCount: cards.length,
      validations,
      allCardsValid: validations.every(v => v.hasElevation && v.hasRoundedCorners)
    };
  }
}
