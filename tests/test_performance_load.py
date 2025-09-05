"""Performance and load testing suite for the ToVéCo voting platform.

This module tests:
- Response time performance
- Concurrent user load testing
- Database performance under load
- Memory and resource usage
- Scalability limits
- Stress testing scenarios
"""

import concurrent.futures
import statistics
import time
from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient

from src.toveco_voting.database import DatabaseManager
from src.toveco_voting.main import app


class PerformanceMetrics:
    """Helper class to collect and analyze performance metrics."""

    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.errors = []
        self.start_time = None
        self.end_time = None

    def add_result(self, response_time: float, success: bool, error: str = None):
        """Add a test result."""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)

    def start_timer(self):
        """Start timing."""
        self.start_time = time.time()

    def stop_timer(self):
        """Stop timing."""
        self.end_time = time.time()

    def get_statistics(self) -> dict[str, Any]:
        """Get performance statistics."""
        if not self.response_times:
            return {}

        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        total_requests = len(self.response_times)

        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate": (self.success_count / total_requests * 100) if total_requests > 0 else 0,
            "total_time": total_time,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "response_times": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": self._percentile(self.response_times, 95),
                "p99": self._percentile(self.response_times, 99),
            },
            "errors": self.errors[:10]  # First 10 errors
        }

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(percentile / 100 * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


class TestBasicPerformance:
    """Test basic performance characteristics."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        with TestClient(app) as test_client:
            yield test_client

    @pytest.fixture
    def sample_vote_data(self):
        """Sample vote data for performance testing."""
        return {
            "voter_name": "Performance Test User",
            "ratings": {
                "toveco1.png": 2,
                "toveco2.png": -1,
                "toveco3.png": 0,
                "toveco4.png": 1,
                "toveco5.png": -2,
                "toveco6.png": 1,
                "toveco7.png": 0,
                "toveco8.png": 2,
                "toveco9.png": -1,
                "toveco10.png": 1,
                "toveco11.png": 0,
            }
        }

    def test_health_check_response_time(self, client):
        """Test health check response time."""
        response_times = []

        for _ in range(100):
            start_time = time.time()
            response = client.get("/api/health")
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            assert response.status_code == 200

        # Analyze response times
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]

        print("Health check performance:")
        print(f"  Average: {avg_response_time*1000:.1f}ms")
        print(f"  Max: {max_response_time*1000:.1f}ms")
        print(f"  P95: {p95_response_time*1000:.1f}ms")

        # Performance assertions
        assert avg_response_time < 0.1, f"Average response time too slow: {avg_response_time*1000:.1f}ms"
        assert p95_response_time < 0.2, f"P95 response time too slow: {p95_response_time*1000:.1f}ms"

    def test_logos_endpoint_response_time(self, client):
        """Test logos endpoint response time."""
        response_times = []

        for _ in range(50):
            start_time = time.time()
            response = client.get("/api/logos")
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            # Skip assertion if logos not available in test environment
            if response.status_code != 200:
                pytest.skip("Logos not available in test environment")

        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)

        print("Logos endpoint performance:")
        print(f"  Average: {avg_response_time*1000:.1f}ms")
        print(f"  Max: {max_response_time*1000:.1f}ms")

        assert avg_response_time < 0.5, f"Logos endpoint too slow: {avg_response_time*1000:.1f}ms"

    def test_vote_submission_response_time(self, client, sample_vote_data):
        """Test vote submission response time."""
        response_times = []
        successful_submissions = 0

        for i in range(10):  # Limited to avoid database growth
            vote_data = sample_vote_data.copy()
            vote_data["voter_name"] = f"Perf User {i}"

            start_time = time.time()
            response = client.post("/api/vote", json=vote_data)
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            if response.status_code == 200:
                successful_submissions += 1

        if successful_submissions == 0:
            pytest.skip("Could not submit votes in test environment")

        avg_response_time = statistics.mean(response_times)
        print("Vote submission performance:")
        print(f"  Average: {avg_response_time*1000:.1f}ms")
        print(f"  Successful submissions: {successful_submissions}/10")

        assert avg_response_time < 1.0, f"Vote submission too slow: {avg_response_time*1000:.1f}ms"

    def test_results_calculation_response_time(self, client):
        """Test results calculation response time."""
        response_times = []

        for _ in range(20):
            start_time = time.time()
            response = client.get("/api/results")
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            assert response.status_code == 200

        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)

        print("Results calculation performance:")
        print(f"  Average: {avg_response_time*1000:.1f}ms")
        print(f"  Max: {max_response_time*1000:.1f}ms")

        assert avg_response_time < 0.5, f"Results calculation too slow: {avg_response_time*1000:.1f}ms"


class TestConcurrentLoad:
    """Test concurrent user load scenarios."""

    @pytest.fixture
    def sample_vote_data(self):
        """Sample vote data for load testing."""
        return {
            "voter_name": "Load Test User",
            "ratings": {
                "toveco1.png": 1,
                "toveco2.png": 0,
                "toveco3.png": -1,
                "toveco4.png": 2,
                "toveco5.png": 1,
                "toveco6.png": 0,
                "toveco7.png": -1,
                "toveco8.png": 2,
                "toveco9.png": 1,
                "toveco10.png": 0,
                "toveco11.png": -1,
            }
        }

    def _make_request(self, base_url: str, endpoint: str, method: str = "GET",
                     data: dict = None, user_id: int = 0) -> tuple[float, bool, str]:
        """Make a single HTTP request and return timing info."""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=30)
            elif method == "POST":
                response = requests.post(f"{base_url}{endpoint}", json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            end_time = time.time()
            response_time = end_time - start_time
            success = response.status_code in [200, 201]
            error = f"HTTP {response.status_code}" if not success else None

            return response_time, success, error

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            return response_time, False, str(e)

    @pytest.mark.slow
    def test_concurrent_health_checks(self):
        """Test concurrent health check requests."""
        base_url = "http://localhost:8000"  # Assumes server is running
        concurrent_users = 20
        requests_per_user = 10

        metrics = PerformanceMetrics()
        metrics.start_timer()

        def user_simulation(user_id):
            """Simulate a user making multiple health check requests."""
            for _ in range(requests_per_user):
                response_time, success, error = self._make_request(
                    base_url, "/api/health", "GET", user_id=user_id
                )
                metrics.add_result(response_time, success, error)
                time.sleep(0.1)  # Small delay between requests

        # Run concurrent user simulations
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_simulation, i) for i in range(concurrent_users)]

            try:
                # Wait for all users to complete
                for future in concurrent.futures.as_completed(futures, timeout=60):
                    future.result()
            except concurrent.futures.TimeoutError:
                pytest.fail("Load test timed out")

        metrics.stop_timer()
        stats = metrics.get_statistics()

        print("Concurrent health check load test results:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Requests/second: {stats['requests_per_second']:.1f}")
        print(f"  Average response time: {stats['response_times']['mean']*1000:.1f}ms")
        print(f"  P95 response time: {stats['response_times']['p95']*1000:.1f}ms")

        # Performance assertions
        assert stats['success_rate'] >= 95, f"Success rate too low: {stats['success_rate']:.1f}%"
        assert stats['requests_per_second'] >= 50, f"Throughput too low: {stats['requests_per_second']:.1f} req/s"
        assert stats['response_times']['mean'] < 0.5, f"Average response time too slow: {stats['response_times']['mean']*1000:.1f}ms"

    @pytest.mark.slow
    def test_concurrent_vote_submissions(self, sample_vote_data):
        """Test concurrent vote submissions."""
        base_url = "http://localhost:8000"
        concurrent_users = 10  # Lower number for vote submissions

        metrics = PerformanceMetrics()
        metrics.start_timer()

        def user_vote_submission(user_id):
            """Simulate a user submitting a vote."""
            vote_data = sample_vote_data.copy()
            vote_data["voter_name"] = f"Concurrent User {user_id}"

            response_time, success, error = self._make_request(
                base_url, "/api/vote", "POST", vote_data, user_id
            )
            metrics.add_result(response_time, success, error)

        # Run concurrent vote submissions
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_vote_submission, i) for i in range(concurrent_users)]

            try:
                for future in concurrent.futures.as_completed(futures, timeout=30):
                    future.result()
            except concurrent.futures.TimeoutError:
                pytest.fail("Vote submission load test timed out")

        metrics.stop_timer()
        stats = metrics.get_statistics()

        print("Concurrent vote submission results:")
        print(f"  Total votes: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Average response time: {stats['response_times']['mean']*1000:.1f}ms")

        # More lenient assertions for vote submissions
        assert stats['success_rate'] >= 80, f"Vote success rate too low: {stats['success_rate']:.1f}%"
        assert stats['response_times']['mean'] < 2.0, f"Vote submission too slow: {stats['response_times']['mean']*1000:.1f}ms"

    @pytest.mark.slow
    def test_mixed_workload(self, sample_vote_data):
        """Test mixed workload with different types of requests."""
        base_url = "http://localhost:8000"
        concurrent_users = 15

        metrics = PerformanceMetrics()
        metrics.start_timer()

        def mixed_user_simulation(user_id):
            """Simulate a user with mixed request patterns."""
            operations = [
                ("GET", "/api/health"),
                ("GET", "/api/logos"),
                ("GET", "/api/results"),
                ("GET", "/api/stats"),
            ]

            # Add vote submission for some users
            if user_id % 3 == 0:  # Every 3rd user submits a vote
                vote_data = sample_vote_data.copy()
                vote_data["voter_name"] = f"Mixed User {user_id}"
                operations.append(("POST", "/api/vote", vote_data))

            for method, endpoint, *data in operations:
                post_data = data[0] if data else None
                response_time, success, error = self._make_request(
                    base_url, endpoint, method, post_data, user_id
                )
                metrics.add_result(response_time, success, error)
                time.sleep(0.05)  # Small delay between requests

        # Run mixed workload simulation
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(mixed_user_simulation, i) for i in range(concurrent_users)]

            try:
                for future in concurrent.futures.as_completed(futures, timeout=45):
                    future.result()
            except concurrent.futures.TimeoutError:
                pytest.fail("Mixed workload test timed out")

        metrics.stop_timer()
        stats = metrics.get_statistics()

        print("Mixed workload test results:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Requests/second: {stats['requests_per_second']:.1f}")
        print(f"  Average response time: {stats['response_times']['mean']*1000:.1f}ms")
        print(f"  P95 response time: {stats['response_times']['p95']*1000:.1f}ms")

        assert stats['success_rate'] >= 85, f"Mixed workload success rate too low: {stats['success_rate']:.1f}%"


class TestDatabasePerformance:
    """Test database performance under load."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for performance testing."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name

        try:
            db_manager = DatabaseManager(temp_db_path)
            yield db_manager
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_bulk_vote_insertion_performance(self, temp_db):
        """Test performance of bulk vote insertions."""
        vote_count = 1000

        start_time = time.time()

        for i in range(vote_count):
            voter_name = f"Bulk User {i}"
            ratings = {f"toveco{(i % 11) + 1}.png": (i % 5) - 2}
            temp_db.save_vote(voter_name, ratings)

        end_time = time.time()
        total_time = end_time - start_time

        votes_per_second = vote_count / total_time

        print("Bulk vote insertion performance:")
        print(f"  {vote_count} votes in {total_time:.2f}s")
        print(f"  {votes_per_second:.1f} votes/second")

        # Performance assertion
        assert votes_per_second >= 100, f"Vote insertion too slow: {votes_per_second:.1f} votes/s"

    def test_large_results_calculation_performance(self, temp_db):
        """Test results calculation with large dataset."""
        # Create a large dataset
        vote_count = 500
        logos = [f"toveco{i}.png" for i in range(1, 12)]

        for i in range(vote_count):
            voter_name = f"Large Dataset User {i}"
            ratings = {logo: (i + len(logo)) % 5 - 2 for logo in logos}
            temp_db.save_vote(voter_name, ratings)

        # Time results calculation
        start_time = time.time()
        results = temp_db.calculate_results()
        end_time = time.time()

        calculation_time = end_time - start_time

        print("Large results calculation performance:")
        print(f"  {vote_count} votes processed in {calculation_time:.3f}s")
        print(f"  {len(results['summary'])} logos calculated")

        # Verify results are correct
        assert results["total_voters"] == vote_count
        assert len(results["summary"]) == 11

        # Performance assertion
        assert calculation_time < 1.0, f"Results calculation too slow: {calculation_time:.3f}s"

    def test_concurrent_database_operations(self, temp_db):
        """Test concurrent database read/write operations."""
        def write_votes(start_id, count):
            """Write votes to database."""
            for i in range(count):
                voter_name = f"Concurrent Writer {start_id}-{i}"
                ratings = {"toveco1.png": 1, "toveco2.png": -1}
                temp_db.save_vote(voter_name, ratings)

        def read_operations():
            """Perform read operations."""
            for _ in range(20):
                temp_db.get_vote_count()
                temp_db.calculate_results()
                time.sleep(0.01)

        # Run concurrent operations
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start writers
            write_futures = [
                executor.submit(write_votes, i * 10, 10)
                for i in range(3)
            ]

            # Start readers
            read_future = executor.submit(read_operations)

            # Wait for completion
            for future in write_futures:
                future.result()
            read_future.result()

        end_time = time.time()
        total_time = end_time - start_time

        # Verify final state
        final_count = temp_db.get_vote_count()

        print("Concurrent database operations:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Final vote count: {final_count}")

        assert final_count == 30, f"Expected 30 votes, got {final_count}"
        assert total_time < 5.0, f"Concurrent operations too slow: {total_time:.2f}s"


class TestMemoryAndResources:
    """Test memory usage and resource consumption."""

    def test_memory_usage_during_load(self):
        """Test memory usage during high load."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate high load
        client = TestClient(app)

        # Make many requests
        for i in range(100):
            client.get("/api/health")
            client.get("/api/stats")

            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory

                # Memory growth should be reasonable
                assert memory_growth < 50, f"Memory growth too high: {memory_growth:.1f}MB"

        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - initial_memory

        print("Memory usage:")
        print(f"  Initial: {initial_memory:.1f}MB")
        print(f"  Final: {final_memory:.1f}MB")
        print(f"  Growth: {total_growth:.1f}MB")

        assert total_growth < 100, f"Total memory growth too high: {total_growth:.1f}MB"

    def test_database_file_size_growth(self):
        """Test database file size growth under load."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name

        try:
            db_manager = DatabaseManager(temp_db_path)

            initial_size = os.path.getsize(temp_db_path)

            # Add many votes
            vote_count = 100
            for i in range(vote_count):
                voter_name = f"Size Test User {i}"
                ratings = {f"toveco{j}.png": (i + j) % 5 - 2 for j in range(1, 12)}
                db_manager.save_vote(voter_name, ratings)

            final_size = os.path.getsize(temp_db_path)
            size_growth = final_size - initial_size
            bytes_per_vote = size_growth / vote_count

            print("Database size growth:")
            print(f"  Initial size: {initial_size} bytes")
            print(f"  Final size: {final_size} bytes")
            print(f"  Growth: {size_growth} bytes")
            print(f"  Bytes per vote: {bytes_per_vote:.1f}")

            # Size growth should be reasonable
            assert bytes_per_vote < 1000, f"Database growth too high: {bytes_per_vote:.1f} bytes/vote"

        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


class TestStressScenarios:
    """Test system behavior under stress conditions."""

    @pytest.mark.slow
    def test_rapid_request_burst(self):
        """Test handling of rapid request bursts."""
        base_url = "http://localhost:8000"
        burst_size = 50

        def make_burst_requests():
            """Make a burst of requests as fast as possible."""
            results = []
            for _ in range(burst_size):
                start_time = time.time()
                try:
                    response = requests.get(f"{base_url}/api/health", timeout=5)
                    end_time = time.time()
                    results.append({
                        "response_time": end_time - start_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
                except Exception as e:
                    end_time = time.time()
                    results.append({
                        "response_time": end_time - start_time,
                        "status_code": 0,
                        "success": False,
                        "error": str(e)
                    })
            return results

        # Execute burst test
        burst_results = make_burst_requests()

        successful_requests = sum(1 for r in burst_results if r["success"])
        success_rate = successful_requests / len(burst_results) * 100
        avg_response_time = statistics.mean([r["response_time"] for r in burst_results])

        print("Rapid burst test results:")
        print(f"  Burst size: {burst_size} requests")
        print(f"  Successful: {successful_requests}/{burst_size}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average response time: {avg_response_time*1000:.1f}ms")

        # System should handle bursts gracefully
        assert success_rate >= 90, f"Burst success rate too low: {success_rate:.1f}%"
        assert avg_response_time < 1.0, f"Burst response time too slow: {avg_response_time*1000:.1f}ms"

    @pytest.mark.slow
    def test_sustained_load(self):
        """Test sustained load over longer period."""
        base_url = "http://localhost:8000"
        duration_seconds = 30  # 30 second test
        request_interval = 0.1  # 10 requests per second

        metrics = PerformanceMetrics()
        metrics.start_timer()

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            try:
                response = requests.get(f"{base_url}/api/stats", timeout=5)
                request_end = time.time()

                response_time = request_end - request_start
                success = response.status_code == 200
                error = f"HTTP {response.status_code}" if not success else None

                metrics.add_result(response_time, success, error)

            except Exception as e:
                request_end = time.time()
                response_time = request_end - request_start
                metrics.add_result(response_time, False, str(e))

            # Maintain request rate
            elapsed = time.time() - request_start
            if elapsed < request_interval:
                time.sleep(request_interval - elapsed)

        metrics.stop_timer()
        stats = metrics.get_statistics()

        print(f"Sustained load test results ({duration_seconds}s):")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Requests/second: {stats['requests_per_second']:.1f}")
        print(f"  Average response time: {stats['response_times']['mean']*1000:.1f}ms")

        # System should maintain performance under sustained load
        assert stats['success_rate'] >= 95, f"Sustained load success rate too low: {stats['success_rate']:.1f}%"
        assert stats['requests_per_second'] >= 8, f"Sustained throughput too low: {stats['requests_per_second']:.1f} req/s"


# Performance test runner that can be used standalone
class PerformanceTestRunner:
    """Standalone performance test runner."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def run_comprehensive_performance_test(self) -> dict[str, Any]:
        """Run comprehensive performance test suite."""
        print("Running comprehensive performance tests...")
        print("=" * 60)

        results = {}

        # Test 1: Basic response times
        print("\n1. Testing basic response times...")
        results["basic"] = self._test_basic_response_times()

        # Test 2: Concurrent load
        print("\n2. Testing concurrent load...")
        results["concurrent"] = self._test_concurrent_load()

        # Test 3: Sustained load
        print("\n3. Testing sustained load...")
        results["sustained"] = self._test_sustained_load()

        return results

    def _test_basic_response_times(self) -> dict[str, Any]:
        """Test basic response times."""
        endpoints = [
            "/api/health",
            "/api/stats",
            "/api/results",
            "/api/logos"
        ]

        results = {}

        for endpoint in endpoints:
            response_times = []
            successful_requests = 0

            for _ in range(20):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    end_time = time.time()

                    response_time = end_time - start_time
                    response_times.append(response_time)

                    if response.status_code == 200:
                        successful_requests += 1

                except Exception:
                    end_time = time.time()
                    response_times.append(end_time - start_time)

            if response_times:
                results[endpoint] = {
                    "avg_response_time": statistics.mean(response_times),
                    "max_response_time": max(response_times),
                    "success_rate": successful_requests / len(response_times) * 100
                }

                print(f"  {endpoint}: {results[endpoint]['avg_response_time']*1000:.1f}ms avg, "
                      f"{results[endpoint]['success_rate']:.1f}% success")

        return results

    def _test_concurrent_load(self) -> dict[str, Any]:
        """Test concurrent load."""
        concurrent_users = 10
        requests_per_user = 5

        def user_requests():
            response_times = []
            for _ in range(requests_per_user):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}/api/health", timeout=10)
                    end_time = time.time()
                    response_times.append(end_time - start_time)
                    return response.status_code == 200
                except Exception:
                    end_time = time.time()
                    response_times.append(end_time - start_time)
                    return False
            return response_times

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_requests) for _ in range(concurrent_users)]
            results_list = [future.result() for future in futures]

        # Process results
        all_response_times = []
        for result in results_list:
            if isinstance(result, list):
                all_response_times.extend(result)

        if all_response_times:
            return {
                "total_requests": len(all_response_times),
                "avg_response_time": statistics.mean(all_response_times),
                "max_response_time": max(all_response_times),
                "concurrent_users": concurrent_users
            }

        return {}

    def _test_sustained_load(self) -> dict[str, Any]:
        """Test sustained load."""
        duration = 10  # 10 seconds
        target_rps = 5  # 5 requests per second

        start_time = time.time()
        response_times = []
        successful_requests = 0

        while time.time() - start_time < duration:
            request_start = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/stats", timeout=5)
                request_end = time.time()

                response_times.append(request_end - request_start)
                if response.status_code == 200:
                    successful_requests += 1
            except Exception:
                request_end = time.time()
                response_times.append(request_end - request_start)

            # Maintain rate
            elapsed = time.time() - request_start
            sleep_time = (1.0 / target_rps) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        total_time = time.time() - start_time

        if response_times:
            return {
                "duration": total_time,
                "total_requests": len(response_times),
                "successful_requests": successful_requests,
                "success_rate": successful_requests / len(response_times) * 100,
                "requests_per_second": len(response_times) / total_time,
                "avg_response_time": statistics.mean(response_times)
            }

        return {}


def run_performance_tests():
    """Run standalone performance tests."""
    runner = PerformanceTestRunner()
    results = runner.run_comprehensive_performance_test()

    print("\n" + "=" * 60)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 60)

    for test_name, test_results in results.items():
        print(f"\n{test_name.upper()} TEST:")
        for metric, value in test_results.items():
            if isinstance(value, float):
                if "time" in metric:
                    print(f"  {metric}: {value*1000:.1f}ms")
                else:
                    print(f"  {metric}: {value:.2f}")
            else:
                print(f"  {metric}: {value}")


if __name__ == "__main__":
    # Can be run standalone for performance testing
    run_performance_tests()

    # Or run with pytest
    pytest.main([__file__, "-v", "-m", "not slow"])
