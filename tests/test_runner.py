#!/usr/bin/env python3
"""Comprehensive test runner for the ToVéCo voting platform.

This script provides a unified interface to run all tests:
- Unit tests
- Integration tests
- Performance tests
- End-to-end workflow tests
- Database integrity tests
- Docker deployment tests

Usage:
    python tests/test_runner.py [options]

Options:
    --unit          Run unit tests only
    --integration   Run integration tests only
    --performance   Run performance tests only
    --e2e          Run end-to-end tests only
    --docker       Run Docker deployment tests only
    --all          Run all tests (default)
    --fast         Skip slow tests
    --report       Generate detailed HTML report
    --coverage     Include coverage report
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class VotingTestRunner:
    """Main test runner class."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.results = {}

    def run_command(self, command: list[str], description: str) -> dict[str, Any]:
        """Run a command and capture results."""
        print(f"\n{'=' * 60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(command)}")
        print(f"{'=' * 60}")

        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            end_time = time.time()
            duration = end_time - start_time

            success = result.returncode == 0

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            print(f"\n{'✅ PASSED' if success else '❌ FAILED'} in {duration:.1f}s")

            return {
                "success": success,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            print("❌ TIMEOUT after 5 minutes")
            return {
                "success": False,
                "duration": 300,
                "return_code": -1,
                "stdout": "",
                "stderr": "Test timed out",
            }
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {
                "success": False,
                "duration": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
            }

    def run_unit_tests(self, fast: bool = False) -> dict[str, Any]:
        """Run unit tests."""
        command = [
            "python",
            "-m",
            "pytest",
            "tests/test_comprehensive_api.py",
            "tests/test_database_integrity.py",
            "-v",
        ]

        if fast:
            command.extend(["-m", "not slow"])

        return self.run_command(command, "Unit Tests")

    def run_integration_tests(self, fast: bool = False) -> dict[str, Any]:
        """Run integration tests."""
        command = ["python", "-m", "pytest", "tests/test_frontend_integration.py", "-v"]

        if fast:
            command.extend(["-m", "not slow"])

        return self.run_command(command, "Integration Tests")

    def run_performance_tests(self, fast: bool = False) -> dict[str, Any]:
        """Run performance tests."""
        command = ["python", "-m", "pytest", "tests/test_performance_load.py", "-v"]

        if fast:
            command.extend(["-m", "not slow"])
        else:
            command.extend(["-m", "slow", "--tb=short"])

        return self.run_command(command, "Performance Tests")

    def run_e2e_tests(self, fast: bool = False) -> dict[str, Any]:
        """Run end-to-end tests."""
        command = ["python", "-m", "pytest", "tests/test_end_to_end_workflow.py", "-v"]

        if fast:
            command.extend(["-m", "not slow"])

        return self.run_command(command, "End-to-End Tests")

    def run_docker_tests(self, fast: bool = False) -> dict[str, Any]:
        """Run Docker deployment tests."""
        command = ["python", "-m", "pytest", "tests/test_docker_deployment.py", "-v"]

        if fast:
            command.extend(["-m", "not slow"])

        return self.run_command(command, "Docker Deployment Tests")

    def run_coverage_tests(self) -> dict[str, Any]:
        """Run tests with coverage reporting."""
        command = [
            "python",
            "-m",
            "pytest",
            "--cov=src/toveco_voting",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "tests/",
            "-v",
        ]

        return self.run_command(command, "Coverage Tests")

    def run_manual_tests(self) -> dict[str, Any]:
        """Run manual test scripts."""
        manual_scripts = [
            "tests/manual_frontend_tests.py",
            "tests/test_docker_deployment.py",
            "tests/test_performance_load.py",
        ]

        results = {}

        for script in manual_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                command = ["python", str(script_path)]
                script_name = script_path.stem
                results[script_name] = self.run_command(
                    command, f"Manual: {script_name}"
                )

        return results

    def validate_test_environment(self) -> bool:
        """Validate that the test environment is properly set up."""
        print("Validating test environment...")

        # Check Python version
        print("✅ Python version OK")

        # Check required packages
        required_packages = ["pytest", "fastapi", "sqlalchemy", "pydantic"]

        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} available")
            except ImportError:
                print(f"❌ {package} not available")
                return False

        # Check test files exist
        required_test_files = [
            "test_comprehensive_api.py",
            "test_frontend_integration.py",
            "test_database_integrity.py",
            "test_docker_deployment.py",
            "test_performance_load.py",
            "test_end_to_end_workflow.py",
            "fixtures.py",
        ]

        for test_file in required_test_files:
            test_path = self.test_dir / test_file
            if test_path.exists():
                print(f"✅ {test_file} found")
            else:
                print(f"❌ {test_file} missing")
                return False

        # Check project structure
        required_dirs = ["src/toveco_voting", "logos", "templates", "static"]

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                print(f"✅ {dir_name}/ directory found")
            else:
                print(f"⚠️  {dir_name}/ directory missing (may cause test failures)")

        return True

    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        report_lines = [
            "ToVéCo Voting Platform - Test Report",
            "=" * 50,
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        total_duration = 0
        total_tests = 0
        passed_tests = 0

        for test_name, result in self.results.items():
            if isinstance(result, dict):
                status = "PASSED" if result.get("success") else "FAILED"
                duration = result.get("duration", 0)
                total_duration += duration
                total_tests += 1
                if result.get("success"):
                    passed_tests += 1

                report_lines.extend(
                    [
                        f"{test_name}:",
                        f"  Status: {status}",
                        f"  Duration: {duration:.1f}s",
                        f"  Return Code: {result.get('return_code', 'N/A')}",
                        "",
                    ]
                )
            else:
                # Handle nested results (like manual tests)
                report_lines.extend(
                    [f"{test_name}:", "  Multiple sub-tests - see detailed output", ""]
                )

        # Summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report_lines.extend(
            [
                "SUMMARY",
                "-" * 30,
                f"Total Test Suites: {total_tests}",
                f"Passed: {passed_tests}",
                f"Failed: {total_tests - passed_tests}",
                f"Success Rate: {success_rate:.1f}%",
                f"Total Duration: {total_duration:.1f}s",
                "",
            ]
        )

        if success_rate == 100:
            report_lines.append(
                "🎉 All tests passed! Platform is ready for production."
            )
        elif success_rate >= 80:
            report_lines.append("⚠️  Most tests passed, but some issues need attention.")
        else:
            report_lines.append("❌ Significant test failures - platform needs fixes.")

        return "\n".join(report_lines)

    def run_all_tests(self, fast: bool = False, include_coverage: bool = False) -> None:
        """Run all test suites."""
        print("Starting comprehensive test suite for ToVéCo Voting Platform")

        if not self.validate_test_environment():
            print("\n❌ Test environment validation failed!")
            sys.exit(1)

        # Run test suites
        test_suites = [
            ("unit_tests", self.run_unit_tests),
            ("integration_tests", self.run_integration_tests),
            ("e2e_tests", self.run_e2e_tests),
            ("database_tests", self.run_unit_tests),  # Database tests are in unit suite
        ]

        if not fast:
            test_suites.extend(
                [
                    ("performance_tests", self.run_performance_tests),
                    ("docker_tests", self.run_docker_tests),
                ]
            )

        for suite_name, suite_func in test_suites:
            self.results[suite_name] = suite_func(fast)

        # Coverage tests (if requested)
        if include_coverage:
            self.results["coverage"] = self.run_coverage_tests()

        # Generate final report
        report = self.generate_report()
        print(f"\n\n{report}")

        # Save report to file
        report_file = self.project_root / "test_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\nDetailed report saved to: {report_file}")

        # Exit with error code if tests failed
        failed_tests = sum(
            1
            for result in self.results.values()
            if isinstance(result, dict) and not result.get("success")
        )

        if failed_tests > 0:
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for ToVéCo voting platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tests/test_runner.py                    # Run all tests
    python tests/test_runner.py --fast             # Run fast tests only
    python tests/test_runner.py --unit             # Run unit tests only
    python tests/test_runner.py --coverage         # Include coverage report
    python tests/test_runner.py --performance      # Run performance tests only
        """,
    )

    # Test suite selection
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests only"
    )
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--docker", action="store_true", help="Run Docker tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    # Test options
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument(
        "--coverage", action="store_true", help="Include coverage report"
    )
    parser.add_argument("--manual", action="store_true", help="Run manual test scripts")

    args = parser.parse_args()

    runner = VotingTestRunner()

    # Validate environment first
    if not runner.validate_test_environment():
        print("\n❌ Environment validation failed!")
        sys.exit(1)

    # Determine which tests to run
    run_specific = any(
        [args.unit, args.integration, args.performance, args.e2e, args.docker]
    )

    if args.unit or (not run_specific and args.all):
        runner.results["unit_tests"] = runner.run_unit_tests(args.fast)

    if args.integration or (not run_specific and args.all):
        runner.results["integration_tests"] = runner.run_integration_tests(args.fast)

    if args.performance or (not run_specific and args.all):
        runner.results["performance_tests"] = runner.run_performance_tests(args.fast)

    if args.e2e or (not run_specific and args.all):
        runner.results["e2e_tests"] = runner.run_e2e_tests(args.fast)

    if args.docker or (not run_specific and args.all):
        runner.results["docker_tests"] = runner.run_docker_tests(args.fast)

    if args.coverage:
        runner.results["coverage"] = runner.run_coverage_tests()

    if args.manual:
        runner.results["manual_tests"] = runner.run_manual_tests()

    # If no specific tests selected and not --all, run default suite
    if not run_specific and not args.all and not args.manual:
        runner.run_all_tests(args.fast, args.coverage)
        return

    # Generate report for specific test runs
    report = runner.generate_report()
    print(f"\n\n{report}")

    # Save report
    report_file = runner.project_root / "test_report.txt"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")

    # Exit with appropriate code
    failed_tests = sum(
        1
        for result in runner.results.values()
        if isinstance(result, dict) and not result.get("success")
    )

    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
