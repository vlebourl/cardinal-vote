import fs from 'fs';
import path from 'path';

/**
 * Global teardown for Playwright tests
 *
 * Performs cleanup, generates test summary reports,
 * manages test artifacts, and prepares final reporting.
 */
async function globalTeardown(config) {
  console.log('🧹 Starting Playwright global teardown...');

  const isCI = !!process.env.CI;
  const testEnv = process.env.TEST_ENV || 'development';

  try {
    // Load global state
    let globalState = {};
    const globalStateFile = 'tests/playwright/.auth/global-state.json';
    if (fs.existsSync(globalStateFile)) {
      globalState = JSON.parse(fs.readFileSync(globalStateFile, 'utf-8'));
    }

    // Generate test summary report
    await generateTestSummary(globalState);

    // Clean up temporary files
    await cleanupTempFiles();

    // Archive test artifacts in CI
    if (isCI) {
      await archiveTestArtifacts();
    }

    // Save teardown information
    const teardownInfo = {
      teardownTimestamp: new Date().toISOString(),
      environment: testEnv,
      testRunId: globalState.testRunId,
      status: 'completed'
    };

    fs.writeFileSync(
      'tests/playwright/.auth/teardown-info.json',
      JSON.stringify(teardownInfo, null, 2)
    );

    console.log('✅ Global teardown completed successfully');

  } catch (error) {
    console.error('❌ Global teardown failed:', error.message);

    // Save error information
    const errorInfo = {
      teardownTimestamp: new Date().toISOString(),
      environment: testEnv,
      error: error.message,
      status: 'failed'
    };

    fs.writeFileSync(
      'tests/playwright/.auth/teardown-error.json',
      JSON.stringify(errorInfo, null, 2)
    );

    if (isCI) {
      throw error; // Ensure CI is aware of teardown failures
    }
  }
}

/**
 * Generate a comprehensive test summary report
 */
async function generateTestSummary(globalState) {
  console.log('📊 Generating test summary report...');

  const resultsFile = 'tests/playwright/reports/results.json';
  let testResults = {};

  if (fs.existsSync(resultsFile)) {
    try {
      testResults = JSON.parse(fs.readFileSync(resultsFile, 'utf-8'));
    } catch (error) {
      console.log('⚠️  Could not parse results.json, generating basic summary');
    }
  }

  // Count test artifacts
  const artifactCounts = {
    screenshots: countFilesInDir('tests/playwright/screenshots'),
    videos: countFilesInDir('tests/playwright/videos'),
    traces: countFilesInDir('tests/playwright/traces'),
    reports: countFilesInDir('tests/playwright/reports')
  };

  const summary = {
    testRun: {
      id: globalState.testRunId,
      startTime: globalState.setupTimestamp,
      endTime: new Date().toISOString(),
      environment: globalState.environment,
      baseURL: globalState.baseURL
    },
    results: testResults,
    artifacts: artifactCounts,
    generatedAt: new Date().toISOString()
  };

  fs.writeFileSync(
    'tests/playwright/reports/test-summary.json',
    JSON.stringify(summary, null, 2)
  );

  console.log('📄 Test summary saved to tests/playwright/reports/test-summary.json');
}

/**
 * Clean up temporary files and old test artifacts
 */
async function cleanupTempFiles() {
  console.log('🗑️  Cleaning up temporary files...');

  const tempDirs = [
    'tests/playwright/.auth/debug-*.png',
    'tests/playwright/.auth/*-debug.png'
  ];

  for (const pattern of tempDirs) {
    try {
      // Simple cleanup for known debug files
      const authDir = 'tests/playwright/.auth';
      if (fs.existsSync(authDir)) {
        const files = fs.readdirSync(authDir);
        const debugFiles = files.filter(file =>
          file.includes('debug') && file.endsWith('.png')
        );

        for (const file of debugFiles) {
          const filePath = path.join(authDir, file);
          fs.unlinkSync(filePath);
          console.log(`🗑️  Removed debug file: ${file}`);
        }
      }
    } catch (error) {
      console.log(`⚠️  Could not clean up temporary files: ${error.message}`);
    }
  }
}

/**
 * Archive test artifacts for CI/CD systems
 */
async function archiveTestArtifacts() {
  console.log('📦 Archiving test artifacts for CI...');

  const archiveInfo = {
    timestamp: new Date().toISOString(),
    artifacts: {
      reports: 'tests/playwright/reports',
      screenshots: 'tests/playwright/screenshots',
      videos: 'tests/playwright/videos',
      traces: 'tests/playwright/traces'
    },
    status: 'archived'
  };

  fs.writeFileSync(
    'tests/playwright/reports/archive-info.json',
    JSON.stringify(archiveInfo, null, 2)
  );

  console.log('📦 Artifact archive information saved');
}

/**
 * Count files in a directory
 */
function countFilesInDir(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      return 0;
    }
    const files = fs.readdirSync(dirPath);
    return files.filter(file => {
      const filePath = path.join(dirPath, file);
      return fs.statSync(filePath).isFile();
    }).length;
  } catch (error) {
    return 0;
  }
}

export default globalTeardown;
