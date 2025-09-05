"""Test data fixtures and mock data for the ToVéCo voting platform.

This module provides:
- Reusable test data fixtures
- Mock data generators
- Test database setup utilities
- Sample vote data in various formats
- Edge case test scenarios
"""

import json
import os
import random
import tempfile
from typing import Any

import pytest

from src.toveco_voting.database import DatabaseManager


class TestDataGenerator:
    """Generate various types of test data for voting platform."""

    LOGO_FILES = [f"toveco{i}.png" for i in range(1, 12)]

    @staticmethod
    def generate_voter_name(index: int = None, prefix: str = "TestUser") -> str:
        """Generate a voter name."""
        if index is not None:
            return f"{prefix} {index}"
        return f"{prefix} {random.randint(1, 10000)}"

    @staticmethod
    def generate_random_ratings(logos: list[str] = None) -> dict[str, int]:
        """Generate random ratings for logos."""
        if logos is None:
            logos = TestDataGenerator.LOGO_FILES

        return {logo: random.randint(-2, 2) for logo in logos}

    @staticmethod
    def generate_specific_ratings(pattern: str = "ascending") -> dict[str, int]:
        """Generate specific rating patterns for predictable testing."""
        logos = TestDataGenerator.LOGO_FILES
        ratings = {}

        if pattern == "ascending":
            # Ratings from -2 to 2 in order
            for i, logo in enumerate(logos):
                rating = -2 + (i * 4 // len(logos))
                ratings[logo] = min(2, rating)

        elif pattern == "descending":
            # Ratings from 2 to -2 in order
            for i, logo in enumerate(logos):
                rating = 2 - (i * 4 // len(logos))
                ratings[logo] = max(-2, rating)

        elif pattern == "alternating":
            # Alternating positive/negative
            for i, logo in enumerate(logos):
                ratings[logo] = 2 if i % 2 == 0 else -2

        elif pattern == "neutral":
            # All neutral ratings
            for logo in logos:
                ratings[logo] = 0

        elif pattern == "extreme":
            # Only extreme ratings (no neutral)
            for logo in logos:
                ratings[logo] = random.choice([-2, -1, 1, 2])

        elif pattern == "positive_bias":
            # Bias toward positive ratings
            for logo in logos:
                ratings[logo] = random.choices(
                    [-2, -1, 0, 1, 2], weights=[1, 2, 3, 6, 8]
                )[0]

        elif pattern == "negative_bias":
            # Bias toward negative ratings
            for logo in logos:
                ratings[logo] = random.choices(
                    [-2, -1, 0, 1, 2], weights=[8, 6, 3, 2, 1]
                )[0]

        else:
            # Default to random
            return TestDataGenerator.generate_random_ratings(logos)

        return ratings

    @staticmethod
    def generate_incomplete_ratings(missing_count: int = 1) -> dict[str, int]:
        """Generate ratings with some logos missing."""
        all_logos = TestDataGenerator.LOGO_FILES.copy()
        logos_to_rate = random.sample(all_logos, len(all_logos) - missing_count)
        return {logo: random.randint(-2, 2) for logo in logos_to_rate}

    @staticmethod
    def generate_vote_submission(
        voter_name: str = None, ratings: dict[str, int] = None
    ) -> dict[str, Any]:
        """Generate a complete vote submission."""
        return {
            "voter_name": voter_name or TestDataGenerator.generate_voter_name(),
            "ratings": ratings or TestDataGenerator.generate_random_ratings(),
        }

    @staticmethod
    def generate_bulk_votes(
        count: int, pattern: str = "random"
    ) -> list[dict[str, Any]]:
        """Generate multiple votes for bulk testing."""
        votes = []

        for i in range(count):
            if pattern == "random":
                ratings = TestDataGenerator.generate_random_ratings()
            else:
                ratings = TestDataGenerator.generate_specific_ratings(pattern)

            vote = {
                "voter_name": TestDataGenerator.generate_voter_name(i + 1, "BulkUser"),
                "ratings": ratings,
            }
            votes.append(vote)

        return votes

    @staticmethod
    def generate_edge_case_data() -> list[dict[str, Any]]:
        """Generate edge case test data."""
        return [
            # Empty voter name
            {"voter_name": "", "ratings": TestDataGenerator.generate_random_ratings()},
            # Very long voter name
            {
                "voter_name": "x" * 150,
                "ratings": TestDataGenerator.generate_random_ratings(),
            },
            # Special characters in name
            {
                "voter_name": "Test User with émojis 🎉 and 'quotes'",
                "ratings": TestDataGenerator.generate_random_ratings(),
            },
            # Non-Latin characters
            {
                "voter_name": "Тест Пользователь",
                "ratings": TestDataGenerator.generate_random_ratings(),
            },
            # Chinese characters
            {
                "voter_name": "测试用户",
                "ratings": TestDataGenerator.generate_random_ratings(),
            },
            # Missing logo ratings
            {
                "voter_name": "Incomplete User",
                "ratings": TestDataGenerator.generate_incomplete_ratings(3),
            },
            # Extra logo ratings
            {
                "voter_name": "Extra Ratings User",
                "ratings": {
                    **TestDataGenerator.generate_random_ratings(),
                    "invalid_logo.png": 1,
                    "another_invalid.png": -1,
                },
            },
            # All neutral ratings
            {
                "voter_name": "Neutral User",
                "ratings": TestDataGenerator.generate_specific_ratings("neutral"),
            },
            # All extreme ratings
            {
                "voter_name": "Extreme User",
                "ratings": {
                    logo: random.choice([-2, 2])
                    for logo in TestDataGenerator.LOGO_FILES
                },
            },
        ]

    @staticmethod
    def generate_invalid_vote_data() -> list[dict[str, Any]]:
        """Generate invalid vote data for negative testing."""
        return [
            # Invalid rating values
            {
                "voter_name": "Invalid Ratings User",
                "ratings": {"toveco1.png": 5, "toveco2.png": -5},  # Out of range
            },
            # Non-integer ratings
            {
                "voter_name": "Float Ratings User",
                "ratings": {"toveco1.png": 1.5, "toveco2.png": -1.7},
            },
            # String ratings
            {
                "voter_name": "String Ratings User",
                "ratings": {"toveco1.png": "good", "toveco2.png": "bad"},
            },
            # Invalid logo names
            {
                "voter_name": "Invalid Logos User",
                "ratings": {"not_a_logo.jpg": 1, "invalid.gif": -1},
            },
            # Empty ratings
            {"voter_name": "Empty Ratings User", "ratings": {}},
            # None values
            {
                "voter_name": "None Ratings User",
                "ratings": {"toveco1.png": None, "toveco2.png": 1},
            },
        ]


class MockDatabaseHelper:
    """Helper for creating and managing mock databases."""

    @staticmethod
    def create_temp_database() -> tuple[DatabaseManager, str]:
        """Create a temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db_path = temp_file.name
        temp_file.close()

        db_manager = DatabaseManager(temp_db_path)
        return db_manager, temp_db_path

    @staticmethod
    def cleanup_temp_database(db_path: str):
        """Clean up temporary database."""
        if os.path.exists(db_path):
            os.unlink(db_path)

    @staticmethod
    def populate_database(db_manager: DatabaseManager, vote_data: list[dict[str, Any]]):
        """Populate database with test vote data."""
        vote_ids = []
        for vote in vote_data:
            try:
                vote_id = db_manager.save_vote(vote["voter_name"], vote["ratings"])
                vote_ids.append(vote_id)
            except Exception as e:
                print(f"Failed to save vote for {vote['voter_name']}: {e}")
        return vote_ids

    @staticmethod
    def create_populated_database(
        vote_count: int = 10, pattern: str = "random"
    ) -> tuple[DatabaseManager, str]:
        """Create and populate a temporary database."""
        db_manager, db_path = MockDatabaseHelper.create_temp_database()

        # Generate and insert test data
        votes = TestDataGenerator.generate_bulk_votes(vote_count, pattern)
        MockDatabaseHelper.populate_database(db_manager, votes)

        return db_manager, db_path


class TestScenarios:
    """Pre-defined test scenarios for comprehensive testing."""

    @staticmethod
    def small_voting_session() -> list[dict[str, Any]]:
        """Simulate a small voting session (5 voters)."""
        return [
            {
                "voter_name": "Alice",
                "ratings": {
                    "toveco1.png": 2,
                    "toveco2.png": 1,
                    "toveco3.png": 0,
                    "toveco4.png": -1,
                    "toveco5.png": -2,
                    "toveco6.png": 1,
                    "toveco7.png": 0,
                    "toveco8.png": 2,
                    "toveco9.png": 1,
                    "toveco10.png": -1,
                    "toveco11.png": 0,
                },
            },
            {
                "voter_name": "Bob",
                "ratings": {
                    "toveco1.png": 1,
                    "toveco2.png": 2,
                    "toveco3.png": -1,
                    "toveco4.png": 0,
                    "toveco5.png": 1,
                    "toveco6.png": -2,
                    "toveco7.png": 1,
                    "toveco8.png": 0,
                    "toveco9.png": 2,
                    "toveco10.png": 1,
                    "toveco11.png": -1,
                },
            },
            {
                "voter_name": "Charlie",
                "ratings": {
                    "toveco1.png": 0,
                    "toveco2.png": -1,
                    "toveco3.png": 2,
                    "toveco4.png": 1,
                    "toveco5.png": 0,
                    "toveco6.png": 2,
                    "toveco7.png": -2,
                    "toveco8.png": 1,
                    "toveco9.png": 0,
                    "toveco10.png": 2,
                    "toveco11.png": 1,
                },
            },
            {
                "voter_name": "Diana",
                "ratings": {
                    "toveco1.png": -2,
                    "toveco2.png": 0,
                    "toveco3.png": 1,
                    "toveco4.png": 2,
                    "toveco5.png": -1,
                    "toveco6.png": 0,
                    "toveco7.png": 1,
                    "toveco8.png": -2,
                    "toveco9.png": -1,
                    "toveco10.png": 0,
                    "toveco11.png": 2,
                },
            },
            {
                "voter_name": "Eve",
                "ratings": {
                    "toveco1.png": 1,
                    "toveco2.png": -2,
                    "toveco3.png": 0,
                    "toveco4.png": -1,
                    "toveco5.png": 2,
                    "toveco6.png": 1,
                    "toveco7.png": 0,
                    "toveco8.png": -1,
                    "toveco9.png": 2,
                    "toveco10.png": -2,
                    "toveco11.png": 1,
                },
            },
        ]

    @staticmethod
    def polarized_voting_session() -> list[dict[str, Any]]:
        """Simulate a polarized voting session (strong opinions)."""
        votes = []

        # Group 1: Love first half of logos, hate second half
        for i in range(5):
            ratings = {}
            for j, logo in enumerate(TestDataGenerator.LOGO_FILES):
                if j < 6:  # First 6 logos
                    ratings[logo] = random.choice([1, 2])
                else:  # Last 5 logos
                    ratings[logo] = random.choice([-2, -1])

            votes.append({"voter_name": f"Group1_User_{i + 1}", "ratings": ratings})

        # Group 2: Opposite preferences
        for i in range(5):
            ratings = {}
            for j, logo in enumerate(TestDataGenerator.LOGO_FILES):
                if j < 6:  # First 6 logos
                    ratings[logo] = random.choice([-2, -1])
                else:  # Last 5 logos
                    ratings[logo] = random.choice([1, 2])

            votes.append({"voter_name": f"Group2_User_{i + 1}", "ratings": ratings})

        return votes

    @staticmethod
    def unanimous_voting_session() -> list[dict[str, Any]]:
        """Simulate a unanimous voting session (everyone agrees)."""
        # Everyone loves toveco1, hates toveco11, neutral on others
        base_ratings = {
            "toveco1.png": 2,
            "toveco11.png": -2,
        }

        votes = []
        for i in range(8):
            ratings = base_ratings.copy()

            # Add some variation for other logos
            for logo in TestDataGenerator.LOGO_FILES:
                if logo not in ratings:
                    ratings[logo] = random.choice([-1, 0, 1])

            votes.append({"voter_name": f"Unanimous_User_{i + 1}", "ratings": ratings})

        return votes

    @staticmethod
    def tie_scenario() -> list[dict[str, Any]]:
        """Simulate a scenario with tied results."""
        votes = []

        # Create votes that result in ties
        patterns = [
            {"toveco1.png": 2, "toveco2.png": 2},  # Both get +2
            {"toveco1.png": -2, "toveco2.png": -2},  # Both get -2
        ]

        for i, pattern in enumerate(patterns * 3):  # 6 votes total
            ratings = dict.fromkeys(
                TestDataGenerator.LOGO_FILES, 0
            )  # Neutral for others
            ratings.update(pattern)

            votes.append({"voter_name": f"Tie_User_{i + 1}", "ratings": ratings})

        return votes

    @staticmethod
    def large_scale_simulation(voter_count: int = 100) -> list[dict[str, Any]]:
        """Simulate a large-scale voting session."""
        votes = []

        # Create diverse voting patterns
        patterns = ["random", "positive_bias", "negative_bias", "extreme", "neutral"]

        for i in range(voter_count):
            pattern = patterns[i % len(patterns)]
            ratings = TestDataGenerator.generate_specific_ratings(pattern)

            votes.append(
                {"voter_name": f"LargeScale_User_{i + 1:03d}", "ratings": ratings}
            )

        return votes


# Pytest fixtures that can be used across test modules
@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    db_manager, db_path = MockDatabaseHelper.create_temp_database()

    yield db_manager

    # Cleanup
    MockDatabaseHelper.cleanup_temp_database(db_path)


@pytest.fixture
def populated_database():
    """Create a database populated with test data."""
    db_manager, db_path = MockDatabaseHelper.create_populated_database(count=10)

    yield db_manager

    # Cleanup
    MockDatabaseHelper.cleanup_temp_database(db_path)


@pytest.fixture
def sample_vote_data():
    """Provide sample vote data."""
    return TestDataGenerator.generate_vote_submission()


@pytest.fixture
def complete_vote_data():
    """Provide complete valid vote data with all logos."""
    return {
        "voter_name": "Complete Test User",
        "ratings": {
            logo: random.randint(-2, 2) for logo in TestDataGenerator.LOGO_FILES
        },
    }


@pytest.fixture
def bulk_vote_data():
    """Provide bulk vote data for testing."""
    return TestDataGenerator.generate_bulk_votes(20, "random")


@pytest.fixture
def edge_case_data():
    """Provide edge case test data."""
    return TestDataGenerator.generate_edge_case_data()


@pytest.fixture
def invalid_vote_data():
    """Provide invalid vote data for negative testing."""
    return TestDataGenerator.generate_invalid_vote_data()


@pytest.fixture
def small_voting_session():
    """Provide small voting session scenario."""
    return TestScenarios.small_voting_session()


@pytest.fixture
def polarized_voting_session():
    """Provide polarized voting session scenario."""
    return TestScenarios.polarized_voting_session()


@pytest.fixture
def unanimous_voting_session():
    """Provide unanimous voting session scenario."""
    return TestScenarios.unanimous_voting_session()


@pytest.fixture
def tie_scenario():
    """Provide tie scenario test data."""
    return TestScenarios.tie_scenario()


# Mock file system fixtures
@pytest.fixture
def mock_logos_directory(tmp_path):
    """Create a temporary logos directory with mock files."""
    logos_dir = tmp_path / "logos"
    logos_dir.mkdir()

    # Create mock logo files
    for logo in TestDataGenerator.LOGO_FILES:
        logo_file = logos_dir / logo
        logo_file.write_bytes(b"mock image data")  # Mock PNG data

    return logos_dir


@pytest.fixture
def mock_templates_directory(tmp_path):
    """Create a temporary templates directory with mock files."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create mock template files
    index_html = templates_dir / "index.html"
    index_html.write_text(
        """
    <!DOCTYPE html>
    <html>
    <head><title>ToVéCo Mock</title></head>
    <body>
        <div id="welcome-screen">Welcome</div>
        <div id="voting-screen" style="display: none;">Voting</div>
    </body>
    </html>
    """
    )

    results_html = templates_dir / "results.html"
    results_html.write_text(
        """
    <!DOCTYPE html>
    <html>
    <head><title>ToVéCo Results Mock</title></head>
    <body>
        <div id="results-content">Results</div>
    </body>
    </html>
    """
    )

    return templates_dir


@pytest.fixture
def mock_static_directory(tmp_path):
    """Create a temporary static directory with mock files."""
    static_dir = tmp_path / "static"
    static_dir.mkdir()

    # Create mock static files
    app_js = static_dir / "app.js"
    app_js.write_text("// Mock JavaScript file")

    style_css = static_dir / "style.css"
    style_css.write_text("/* Mock CSS file */")

    return static_dir


# Performance testing fixtures
@pytest.fixture
def performance_vote_data():
    """Generate vote data optimized for performance testing."""
    return TestDataGenerator.generate_bulk_votes(50, "random")


@pytest.fixture
def stress_test_data():
    """Generate data for stress testing."""
    return TestDataGenerator.generate_bulk_votes(200, "random")


# Export commonly used test data for easy import
SAMPLE_VOTES = TestScenarios.small_voting_session()
EDGE_CASES = TestDataGenerator.generate_edge_case_data()
INVALID_DATA = TestDataGenerator.generate_invalid_vote_data()


# Utility functions for test data validation
def validate_vote_data(vote_data: dict[str, Any]) -> bool:
    """Validate that vote data has the correct structure."""
    if not isinstance(vote_data, dict):
        return False

    required_fields = ["voter_name", "ratings"]
    if not all(field in vote_data for field in required_fields):
        return False

    if not isinstance(vote_data["voter_name"], str):
        return False

    if not isinstance(vote_data["ratings"], dict):
        return False

    # Check rating values
    for logo, rating in vote_data["ratings"].items():
        if not isinstance(logo, str) or not isinstance(rating, int):
            return False
        if rating < -2 or rating > 2:
            return False
        if not logo.startswith("toveco") or not logo.endswith(".png"):
            return False

    return True


def calculate_expected_results(votes: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate expected results for test validation."""
    if not votes:
        return {"summary": {}, "total_voters": 0}

    logo_totals = {}
    logo_counts = {}

    for vote in votes:
        for logo, rating in vote["ratings"].items():
            if logo not in logo_totals:
                logo_totals[logo] = 0
                logo_counts[logo] = 0
            logo_totals[logo] += rating
            logo_counts[logo] += 1

    summary = {}
    for logo in logo_totals:
        average = logo_totals[logo] / logo_counts[logo]
        summary[logo] = {
            "average": round(average, 2),
            "total_votes": logo_counts[logo],
            "total_score": logo_totals[logo],
        }

    # Add rankings
    sorted_logos = sorted(summary.items(), key=lambda x: x[1]["average"], reverse=True)
    for rank, (_logo, stats) in enumerate(sorted_logos, 1):
        stats["ranking"] = rank

    return {"summary": dict(sorted_logos), "total_voters": len(votes)}


if __name__ == "__main__":
    # Demo the fixture capabilities
    print("Test Data Fixtures Demo")
    print("=" * 40)

    # Generate sample data
    print("\n1. Sample Vote:")
    sample = TestDataGenerator.generate_vote_submission()
    print(json.dumps(sample, indent=2))

    print("\n2. Edge Case Examples:")
    edge_cases = TestDataGenerator.generate_edge_case_data()
    for i, case in enumerate(edge_cases[:3]):
        print(f"   Case {i + 1}: {case['voter_name']}")

    print("\n3. Small Voting Session Results:")
    small_session = TestScenarios.small_voting_session()
    expected = calculate_expected_results(small_session)
    print(f"   Total voters: {expected['total_voters']}")
    print(f"   Logos evaluated: {len(expected['summary'])}")

    # Top 3 logos
    top_logos = sorted(
        expected["summary"].items(), key=lambda x: x[1]["average"], reverse=True
    )[:3]
    for rank, (logo, stats) in enumerate(top_logos, 1):
        print(f"   #{rank}: {logo} (avg: {stats['average']})")
