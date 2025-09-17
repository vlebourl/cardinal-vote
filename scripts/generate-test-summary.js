#!/usr/bin/env node

/**
 * Generate comprehensive test summary from Playwright test results
 * Used by GitHub Actions to create test reports
 */

const fs = require('fs');
const path = require('path');

class TestSummaryGenerator {
  constructor(artifactsPath) {
    this.artifactsPath = artifactsPath;
    this.summary = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: 0,
      suites: {},
      browsers: {},
      performance: {},
      accessibility: {},
      visual: {}
    };
  }

  /**
   * Generate comprehensive test summary
   */
  async generateSummary() {
    try {
      const artifacts = this.findTestArtifacts();

      for (const artifact of artifacts) {
        await this.processArtifact(artifact);
      }

      return this.formatSummary();
    } catch (error) {
      console.error('Error generating test summary:', error);
      return this.formatErrorSummary(error);
    }
  }

  /**
   * Find all test result artifacts
   */
  findTestArtifacts() {
    const artifacts = [];

    if (!fs.existsSync(this.artifactsPath)) {
      console.warn(`Artifacts path does not exist: ${this.artifactsPath}`);
      return artifacts;
    }

    const subdirs = fs.readdirSync(this.artifactsPath, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    for (const subdir of subdirs) {
      const subdirPath = path.join(this.artifactsPath, subdir);
      const files = this.findFilesRecursive(subdirPath, ['.json']);

      for (const file of files) {
        if (file.includes('results') || file.includes('report')) {
          artifacts.push({
            type: this.determineArtifactType(subdir),
            browser: this.extractBrowser(subdir),
            path: file,
            name: subdir
          });
        }
      }
    }

    return artifacts;
  }

  /**
   * Find files recursively
   */
  findFilesRecursive(dir, extensions) {
    const files = [];

    if (!fs.existsSync(dir)) return files;

    const items = fs.readdirSync(dir, { withFileTypes: true });

    for (const item of items) {
      const fullPath = path.join(dir, item.name);

      if (item.isDirectory()) {
        files.push(...this.findFilesRecursive(fullPath, extensions));
      } else if (extensions.some(ext => item.name.endsWith(ext))) {
        files.push(fullPath);
      }
    }

    return files;
  }

  /**
   * Determine artifact type from directory name
   */
  determineArtifactType(dirname) {
    if (dirname.includes('core')) return 'core-flows';
    if (dirname.includes('advanced')) return 'advanced-scenarios';
    if (dirname.includes('error')) return 'error-scenarios';
    if (dirname.includes('mobile')) return 'mobile';
    if (dirname.includes('performance')) return 'performance';
    if (dirname.includes('visual')) return 'visual-regression';
    if (dirname.includes('accessibility')) return 'accessibility';
    return 'other';
  }

  /**
   * Extract browser from directory name
   */
  extractBrowser(dirname) {
    if (dirname.includes('chromium')) return 'chromium';
    if (dirname.includes('firefox')) return 'firefox';
    if (dirname.includes('webkit')) return 'webkit';
    if (dirname.includes('chrome')) return 'mobile-chrome';
    if (dirname.includes('safari')) return 'mobile-safari';
    return 'unknown';
  }

  /**
   * Process individual test artifact
   */
  async processArtifact(artifact) {
    try {
      const content = fs.readFileSync(artifact.path, 'utf8');
      const data = JSON.parse(content);

      // Handle different Playwright result formats
      if (data.suites) {
        this.processPlaywrightResults(data, artifact);
      } else if (data.tests) {
        this.processTestResults(data, artifact);
      } else if (data.stats) {
        this.processStatsResults(data, artifact);
      }

    } catch (error) {
      console.warn(`Failed to process artifact ${artifact.path}:`, error.message);
    }
  }

  /**
   * Process Playwright test results
   */
  processPlaywrightResults(data, artifact) {
    for (const suite of data.suites) {
      this.processSuite(suite, artifact);
    }

    // Update browser stats
    if (!this.summary.browsers[artifact.browser]) {
      this.summary.browsers[artifact.browser] = { passed: 0, failed: 0, total: 0 };
    }

    // Update suite stats
    if (!this.summary.suites[artifact.type]) {
      this.summary.suites[artifact.type] = { passed: 0, failed: 0, total: 0, duration: 0 };
    }
  }

  /**
   * Process test suite
   */
  processSuite(suite, artifact) {
    for (const spec of suite.specs || []) {
      for (const test of spec.tests || []) {
        this.processTest(test, artifact);
      }
    }

    // Process nested suites
    for (const nestedSuite of suite.suites || []) {
      this.processSuite(nestedSuite, artifact);
    }
  }

  /**
   * Process individual test
   */
  processTest(test, artifact) {
    this.summary.total++;
    this.summary.suites[artifact.type].total++;
    this.summary.browsers[artifact.browser].total++;

    const status = this.getTestStatus(test);

    switch (status) {
      case 'passed':
        this.summary.passed++;
        this.summary.suites[artifact.type].passed++;
        this.summary.browsers[artifact.browser].passed++;
        break;
      case 'failed':
        this.summary.failed++;
        this.summary.suites[artifact.type].failed++;
        this.summary.browsers[artifact.browser].failed++;
        break;
      case 'skipped':
        this.summary.skipped++;
        break;
    }

    // Add duration if available
    if (test.results && test.results[0] && test.results[0].duration) {
      this.summary.duration += test.results[0].duration;
      this.summary.suites[artifact.type].duration += test.results[0].duration;
    }

    // Extract performance data
    if (artifact.type === 'performance' && test.annotations) {
      this.extractPerformanceData(test);
    }

    // Extract accessibility data
    if (artifact.type === 'accessibility' && test.annotations) {
      this.extractAccessibilityData(test);
    }
  }

  /**
   * Get test status
   */
  getTestStatus(test) {
    if (!test.results || test.results.length === 0) return 'skipped';

    const result = test.results[0];
    return result.status || 'unknown';
  }

  /**
   * Extract performance metrics from test
   */
  extractPerformanceData(test) {
    for (const annotation of test.annotations || []) {
      if (annotation.type === 'performance') {
        try {
          const metrics = JSON.parse(annotation.description);

          if (!this.summary.performance.metrics) {
            this.summary.performance.metrics = [];
          }

          this.summary.performance.metrics.push({
            test: test.title,
            ...metrics
          });
        } catch (error) {
          // Ignore parsing errors
        }
      }
    }
  }

  /**
   * Extract accessibility data from test
   */
  extractAccessibilityData(test) {
    for (const annotation of test.annotations || []) {
      if (annotation.type === 'accessibility') {
        try {
          const results = JSON.parse(annotation.description);

          if (!this.summary.accessibility.violations) {
            this.summary.accessibility.violations = [];
          }

          this.summary.accessibility.violations.push({
            test: test.title,
            ...results
          });
        } catch (error) {
          // Ignore parsing errors
        }
      }
    }
  }

  /**
   * Format final summary
   */
  formatSummary() {
    const successRate = this.summary.total > 0 ?
      Math.round((this.summary.passed / this.summary.total) * 100) : 0;

    const durationFormatted = this.formatDuration(this.summary.duration);

    let markdown = `# 🎭 Playwright Test Results\n\n`;

    // Overall status
    const statusIcon = successRate >= 95 ? '✅' : successRate >= 80 ? '⚠️' : '❌';
    markdown += `## ${statusIcon} Overall Status\n\n`;
    markdown += `- **Success Rate**: ${successRate}%\n`;
    markdown += `- **Total Tests**: ${this.summary.total}\n`;
    markdown += `- **Passed**: ${this.summary.passed}\n`;
    markdown += `- **Failed**: ${this.summary.failed}\n`;
    markdown += `- **Skipped**: ${this.summary.skipped}\n`;
    markdown += `- **Duration**: ${durationFormatted}\n\n`;

    // Test suites breakdown
    markdown += `## 📊 Test Suites\n\n`;
    markdown += `| Suite | Total | Passed | Failed | Success Rate | Duration |\n`;
    markdown += `|-------|-------|--------|--------|--------------|----------|\n`;

    for (const [suite, stats] of Object.entries(this.summary.suites)) {
      const suiteSuccessRate = stats.total > 0 ?
        Math.round((stats.passed / stats.total) * 100) : 0;
      const suiteDuration = this.formatDuration(stats.duration);
      const suiteIcon = suiteSuccessRate >= 95 ? '✅' : suiteSuccessRate >= 80 ? '⚠️' : '❌';

      markdown += `| ${suiteIcon} ${suite} | ${stats.total} | ${stats.passed} | ${stats.failed} | ${suiteSuccessRate}% | ${suiteDuration} |\n`;
    }

    // Browser compatibility
    markdown += `\n## 🌐 Browser Compatibility\n\n`;
    markdown += `| Browser | Total | Passed | Failed | Success Rate |\n`;
    markdown += `|---------|-------|--------|--------|------|\n`;

    for (const [browser, stats] of Object.entries(this.summary.browsers)) {
      const browserSuccessRate = stats.total > 0 ?
        Math.round((stats.passed / stats.total) * 100) : 0;
      const browserIcon = browserSuccessRate >= 95 ? '✅' : browserSuccessRate >= 80 ? '⚠️' : '❌';

      markdown += `| ${browserIcon} ${browser} | ${stats.total} | ${stats.passed} | ${stats.failed} | ${browserSuccessRate}% |\n`;
    }

    // Performance summary
    if (this.summary.performance.metrics && this.summary.performance.metrics.length > 0) {
      markdown += `\n## ⚡ Performance Summary\n\n`;

      const avgLoadTime = this.calculateAverage(this.summary.performance.metrics, 'loadTime');
      const avgLCP = this.calculateAverage(this.summary.performance.metrics, 'lcp');
      const avgFID = this.calculateAverage(this.summary.performance.metrics, 'fid');

      if (avgLoadTime) markdown += `- **Average Load Time**: ${avgLoadTime}ms\n`;
      if (avgLCP) markdown += `- **Average LCP**: ${avgLCP}ms\n`;
      if (avgFID) markdown += `- **Average FID**: ${avgFID}ms\n`;
    }

    // Accessibility summary
    if (this.summary.accessibility.violations && this.summary.accessibility.violations.length > 0) {
      markdown += `\n## ♿ Accessibility Summary\n\n`;
      markdown += `- **Total Violations**: ${this.summary.accessibility.violations.length}\n`;

      const violationTypes = {};
      for (const violation of this.summary.accessibility.violations) {
        violationTypes[violation.type] = (violationTypes[violation.type] || 0) + 1;
      }

      for (const [type, count] of Object.entries(violationTypes)) {
        markdown += `- **${type}**: ${count}\n`;
      }
    }

    // Failed tests details
    if (this.summary.failed > 0) {
      markdown += `\n## ❌ Failed Tests\n\n`;
      markdown += `_Check individual test reports for detailed failure information._\n`;
    }

    markdown += `\n---\n`;
    markdown += `*Generated on ${new Date().toISOString()}*\n`;

    return markdown;
  }

  /**
   * Calculate average of numeric values
   */
  calculateAverage(data, field) {
    const values = data.map(item => item[field]).filter(val => typeof val === 'number');
    if (values.length === 0) return null;
    return Math.round(values.reduce((sum, val) => sum + val, 0) / values.length);
  }

  /**
   * Format duration in human readable format
   */
  formatDuration(milliseconds) {
    if (!milliseconds) return '0s';

    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  /**
   * Format error summary when generation fails
   */
  formatErrorSummary(error) {
    return `# ❌ Test Summary Generation Failed\n\n` +
           `Error: ${error.message}\n\n` +
           `Please check the test artifacts and try again.\n`;
  }
}

// Main execution
async function main() {
  const artifactsPath = process.argv[2] || './test-artifacts';

  const generator = new TestSummaryGenerator(artifactsPath);
  const summary = await generator.generateSummary();

  console.log(summary);
}

if (require.main === module) {
  main().catch(error => {
    console.error('Failed to generate test summary:', error);
    process.exit(1);
  });
}

module.exports = TestSummaryGenerator;
