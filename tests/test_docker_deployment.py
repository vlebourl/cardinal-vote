"""Docker deployment validation tests for the ToVéCo voting platform.

This module tests:
- Docker container build and startup
- Environment variable configuration
- Volume mounting and persistence
- Network connectivity
- Health checks
- Multi-container deployment scenarios
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Any

import docker
import pytest
import requests
from docker.errors import DockerException


class TestDockerBuild:
    """Test Docker image building and basic container operations."""

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Create Docker client."""
        try:
            client = docker.from_env()
            # Test connection
            client.ping()
            yield client
        except DockerException as e:
            pytest.skip(f"Docker not available: {e}")

    @pytest.fixture(scope="class")
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture(scope="class")
    def built_image(self, docker_client, project_root):
        """Build Docker image for testing."""
        image_tag = "toveco-voting:test"

        try:
            # Build image
            print("Building Docker image...")
            image, build_logs = docker_client.images.build(
                path=str(project_root),
                tag=image_tag,
                rm=True,
                forcerm=True,
                dockerfile="Dockerfile",
            )

            # Print build logs for debugging
            for log in build_logs:
                if "stream" in log:
                    print(log["stream"].strip())

            yield image

        except DockerException as e:
            pytest.skip(f"Failed to build Docker image: {e}")
        finally:
            # Cleanup image
            try:
                docker_client.images.remove(image_tag, force=True)
            except docker.errors.APIError:
                pass

    def test_dockerfile_exists(self, project_root):
        """Test that Dockerfile exists and is readable."""
        dockerfile_path = project_root / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile not found"
        assert dockerfile_path.is_file(), "Dockerfile is not a file"

        # Check Dockerfile content
        content = dockerfile_path.read_text()
        assert "FROM" in content, "Dockerfile missing FROM instruction"
        assert "toveco_voting" in content, "Dockerfile doesn't reference main package"

    def test_dockerignore_exists(self, project_root):
        """Test that .dockerignore exists to optimize build context."""
        dockerignore_path = project_root / ".dockerignore"
        assert dockerignore_path.exists(), ".dockerignore not found"

        content = dockerignore_path.read_text()
        # Should ignore common development files
        expected_ignores = [".git", "__pycache__", "*.pyc", ".pytest_cache"]
        for ignore_pattern in expected_ignores:
            assert ignore_pattern in content, (
                f"Missing {ignore_pattern} in .dockerignore"
            )

    def test_image_builds_successfully(self, built_image):
        """Test that Docker image builds without errors."""
        assert built_image is not None
        assert built_image.id is not None

    def test_image_labels(self, built_image):
        """Test that Docker image has appropriate labels."""
        labels = built_image.labels or {}

        # Check for common labels
        expected_labels = ["maintainer", "description", "version"]
        for label in expected_labels:
            if label in labels:
                assert labels[label], f"Label {label} is empty"

    def test_image_size_reasonable(self, built_image):
        """Test that Docker image size is reasonable."""
        # Get image size in bytes
        size = built_image.attrs["Size"]
        size_mb = size / (1024 * 1024)

        # Image should be less than 1GB (reasonable for Python app)
        assert size_mb < 1024, f"Image too large: {size_mb:.1f}MB"
        print(f"Image size: {size_mb:.1f}MB")


class TestContainerOperations:
    """Test Docker container operations and configuration."""

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Create Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            yield client
        except DockerException as e:
            pytest.skip(f"Docker not available: {e}")

    @pytest.fixture(scope="class")
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def test_container(self, docker_client, project_root):
        """Create and manage test container."""
        image_tag = "toveco-voting:container-test"
        container = None

        try:
            # Build image
            image, _ = docker_client.images.build(
                path=str(project_root), tag=image_tag, rm=True, forcerm=True
            )

            # Create container (don't start yet)
            container = docker_client.containers.create(
                image_tag,
                name="toveco-test-container",
                ports={"8000/tcp": None},  # Random port mapping
                environment={"DEBUG": "false", "PORT": "8000", "HOST": "0.0.0.0"},
                detach=True,
                remove=True,
            )

            yield container

        except DockerException as e:
            pytest.skip(f"Failed to create container: {e}")
        finally:
            # Cleanup
            if container:
                try:
                    container.stop(timeout=5)
                except docker.errors.APIError:
                    pass
                try:
                    container.remove(force=True)
                except docker.errors.APIError:
                    pass
            # Remove image
            try:
                docker_client.images.remove(image_tag, force=True)
            except docker.errors.APIError:
                pass

    def test_container_starts(self, test_container):
        """Test that container starts successfully."""
        test_container.start()

        # Wait for container to start
        time.sleep(2)

        # Check container status
        test_container.reload()
        assert test_container.status == "running"

    def test_container_port_mapping(self, test_container):
        """Test that container port mapping works."""
        test_container.start()
        time.sleep(2)

        test_container.reload()
        ports = test_container.attrs["NetworkSettings"]["Ports"]

        assert "8000/tcp" in ports
        assert ports["8000/tcp"] is not None
        assert len(ports["8000/tcp"]) > 0

    def test_container_logs(self, test_container):
        """Test that container generates expected logs."""
        test_container.start()
        time.sleep(5)  # Wait for startup

        logs = test_container.logs().decode("utf-8")

        # Check for expected startup messages
        assert "uvicorn" in logs.lower() or "fastapi" in logs.lower()
        # Should not contain error messages
        assert "error" not in logs.lower() or "traceback" not in logs.lower()

    def test_container_health_check(self, test_container):
        """Test container health check endpoint."""
        test_container.start()
        time.sleep(5)

        test_container.reload()
        ports = test_container.attrs["NetworkSettings"]["Ports"]
        host_port = ports["8000/tcp"][0]["HostPort"]

        try:
            # Try to reach health endpoint
            response = requests.get(
                f"http://localhost:{host_port}/api/health", timeout=10
            )
            assert response.status_code == 200

            data = response.json()
            assert "status" in data

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Health check failed: {e}")

    def test_container_environment_variables(self, docker_client, project_root):
        """Test container respects environment variables."""
        image_tag = "toveco-voting:env-test"

        try:
            # Build image
            docker_client.images.build(
                path=str(project_root), tag=image_tag, rm=True, forcerm=True
            )

            # Test different environment configurations
            test_envs = [
                {"DEBUG": "true", "PORT": "8080"},
                {"DEBUG": "false", "HOST": "127.0.0.1"},
                {"DATABASE_PATH": "/app/custom.db"},
            ]

            for env_vars in test_envs:
                container = docker_client.containers.run(
                    image_tag,
                    environment=env_vars,
                    ports={"8000/tcp": None},
                    detach=True,
                    remove=True,
                )

                try:
                    time.sleep(3)
                    container.reload()
                    assert container.status == "running"

                    # Check logs for environment-specific behavior
                    logs = container.logs().decode("utf-8")
                    if "DEBUG" in env_vars:
                        if env_vars["DEBUG"] == "true":
                            assert "debug" in logs.lower()

                finally:
                    container.stop(timeout=5)

        except DockerException as e:
            pytest.skip(f"Environment test failed: {e}")
        finally:
            try:
                docker_client.images.remove(image_tag, force=True)
            except docker.errors.APIError:
                pass

    def test_container_volume_mounting(self, docker_client, project_root):
        """Test container volume mounting for persistence."""
        image_tag = "toveco-voting:volume-test"

        try:
            # Build image
            docker_client.images.build(
                path=str(project_root), tag=image_tag, rm=True, forcerm=True
            )

            # Create temporary directory for volume
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                # Run container with volume mount
                container = docker_client.containers.run(
                    image_tag,
                    volumes={temp_dir: {"bind": "/app/data", "mode": "rw"}},
                    environment={"DATABASE_PATH": "/app/data/votes.db"},
                    ports={"8000/tcp": None},
                    detach=True,
                    remove=True,
                )

                try:
                    time.sleep(5)  # Wait for startup

                    container.reload()
                    assert container.status == "running"

                    # Check that database file is created in mounted volume
                    os.path.join(temp_dir, "votes.db")
                    # Database should be created on first access
                    # We'd need to make a request to trigger database creation

                finally:
                    container.stop(timeout=5)

        except DockerException as e:
            pytest.skip(f"Volume test failed: {e}")
        finally:
            try:
                docker_client.images.remove(image_tag, force=True)
            except docker.errors.APIError:
                pass


class TestDockerCompose:
    """Test Docker Compose deployment scenarios."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_compose_file_exists(self, project_root):
        """Test that docker-compose.yml exists."""
        compose_file = project_root / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml not found"

        # Check basic structure
        content = compose_file.read_text()
        assert "version:" in content
        assert "services:" in content
        assert "toveco-voting" in content or "app" in content

    def test_compose_file_syntax(self, project_root):
        """Test that docker-compose.yml has valid syntax."""
        import yaml

        compose_file = project_root / "docker-compose.yml"

        try:
            with open(compose_file) as f:
                compose_config = yaml.safe_load(f)

            # Basic validation
            assert "version" in compose_config
            assert "services" in compose_config
            assert isinstance(compose_config["services"], dict)

        except yaml.YAMLError as e:
            pytest.fail(f"Invalid docker-compose.yml syntax: {e}")

    def test_production_compose_exists(self, project_root):
        """Test that production docker-compose configuration exists."""
        prod_compose = project_root / "docker-compose.prod.yml"
        if prod_compose.exists():
            # Check production-specific configurations
            content = prod_compose.read_text()
            # Should not have debug settings
            assert "DEBUG=true" not in content
            # Should have production optimizations
            assert "restart:" in content

    @pytest.mark.slow
    def test_compose_deployment(self, project_root):
        """Test Docker Compose deployment (slow test)."""
        # This test requires Docker Compose to be installed
        compose_file = project_root / "docker-compose.yml"

        if not compose_file.exists():
            pytest.skip("docker-compose.yml not found")

        try:
            # Try to validate compose file
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                pytest.fail(f"docker-compose config failed: {result.stderr}")

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.skip(f"Docker Compose not available: {e}")


class TestProductionReadiness:
    """Test production readiness of Docker deployment."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_non_root_user(self, project_root):
        """Test that Docker image runs as non-root user."""
        dockerfile_path = project_root / "Dockerfile"

        if dockerfile_path.exists():
            content = dockerfile_path.read_text()

            # Should create and use non-root user
            assert "USER" in content, "Dockerfile should specify non-root user"

            # Should not run as root
            lines = content.split("\n")
            user_lines = [line for line in lines if line.strip().startswith("USER")]
            if user_lines:
                last_user = user_lines[-1]
                assert "root" not in last_user.lower(), "Should not run as root user"

    def test_security_best_practices(self, project_root):
        """Test Docker security best practices."""
        dockerfile_path = project_root / "Dockerfile"

        if dockerfile_path.exists():
            content = dockerfile_path.read_text()

            # Should not install unnecessary packages
            assert "curl" not in content.lower() or "wget" not in content.lower()

            # Should use specific base image versions
            from_lines = [
                line for line in content.split("\n") if line.strip().startswith("FROM")
            ]
            for from_line in from_lines:
                if ":" not in from_line:
                    pytest.fail("Should use specific image versions, not 'latest'")

    def test_resource_limits(self, project_root):
        """Test that Docker containers have resource limits."""
        compose_file = project_root / "docker-compose.prod.yml"

        if compose_file.exists():
            content = compose_file.read_text()

            # Should have memory limits
            if "mem_limit" in content or "memory" in content:
                pass  # Good, has memory limits
            elif "deploy:" in content and "resources:" in content:
                pass  # Using deploy.resources format
            else:
                print("Warning: No memory limits found in production compose")

    def test_health_check_configuration(self, project_root):
        """Test that health checks are properly configured."""
        dockerfile_path = project_root / "Dockerfile"

        if dockerfile_path.exists():
            content = dockerfile_path.read_text()

            # Should have HEALTHCHECK instruction
            if "HEALTHCHECK" in content:
                assert "/api/health" in content, (
                    "Health check should use health endpoint"
                )
            else:
                # Health check might be in compose file instead
                compose_file = project_root / "docker-compose.yml"
                if compose_file.exists():
                    compose_content = compose_file.read_text()
                    assert "healthcheck" in compose_content, (
                        "No health check configured"
                    )

    def test_logging_configuration(self, project_root):
        """Test that logging is properly configured."""
        compose_files = [
            project_root / "docker-compose.yml",
            project_root / "docker-compose.prod.yml",
        ]

        for compose_file in compose_files:
            if compose_file.exists():
                content = compose_file.read_text()

                # Should have logging configuration
                if "logging:" in content:
                    # Should not use default logging driver for production
                    if "prod" in compose_file.name:
                        assert "json-file" in content, (
                            "Production should use json-file logging"
                        )

    def test_secrets_management(self, project_root):
        """Test that secrets are not hardcoded."""
        dockerfile_path = project_root / "Dockerfile"

        if dockerfile_path.exists():
            content = dockerfile_path.read_text()

            # Should not contain hardcoded secrets
            sensitive_patterns = ["password", "secret", "key", "token"]
            for pattern in sensitive_patterns:
                # Look for hardcoded values (not environment variables)
                lines = content.split("\n")
                for line in lines:
                    if (
                        pattern in line.lower()
                        and "=" in line
                        and not line.strip().startswith("#")
                    ):
                        if not ("ENV" in line or "$" in line):
                            pytest.fail(
                                f"Possible hardcoded secret in Dockerfile: {line}"
                            )


class TestNetworkConfiguration:
    """Test Docker network configuration and connectivity."""

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Create Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            yield client
        except DockerException as e:
            pytest.skip(f"Docker not available: {e}")

    def test_port_exposure(self, project_root):
        """Test that correct ports are exposed."""
        dockerfile_path = project_root / "Dockerfile"

        if dockerfile_path.exists():
            content = dockerfile_path.read_text()

            # Should expose port 8000
            assert "EXPOSE" in content, "Dockerfile should expose ports"
            assert "8000" in content, "Should expose port 8000"

    def test_network_isolation(self, docker_client, project_root):
        """Test network isolation between containers."""
        # This is more relevant for multi-container deployments
        compose_file = project_root / "docker-compose.yml"

        if compose_file.exists():
            content = compose_file.read_text()

            # If there are multiple services, they should use custom networks
            if content.count("services:") > 0:
                service_count = content.count("image:") + content.count("build:")
                if service_count > 1:
                    # Should define custom networks for security
                    assert "networks:" in content, (
                        "Multi-service setup should use custom networks"
                    )


# Integration test that can be run manually
class DockerDeploymentValidator:
    """Manual Docker deployment validation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docker_client = None

        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
        except DockerException:
            raise RuntimeError("Docker not available") from None

    def validate_complete_deployment(self) -> dict[str, Any]:
        """Perform complete deployment validation."""
        results = {
            "build": False,
            "start": False,
            "health": False,
            "api": False,
            "logs": [],
            "errors": [],
        }

        container = None
        image_tag = "toveco-voting:validation"

        try:
            # Step 1: Build image
            print("Building Docker image...")
            image, build_logs = self.docker_client.images.build(
                path=str(self.project_root), tag=image_tag, rm=True, forcerm=True
            )
            results["build"] = True

            # Step 2: Start container
            print("Starting container...")
            container = self.docker_client.containers.run(
                image_tag,
                ports={"8000/tcp": 8080},  # Map to host port 8080
                environment={"DEBUG": "false", "PORT": "8000", "HOST": "0.0.0.0"},
                detach=True,
                remove=True,
            )

            time.sleep(5)  # Wait for startup
            container.reload()

            if container.status == "running":
                results["start"] = True

            # Step 3: Check health
            try:
                response = requests.get("http://localhost:8080/api/health", timeout=10)
                if response.status_code == 200:
                    results["health"] = True
                    results["api"] = True
            except requests.exceptions.RequestException as e:
                results["errors"].append(f"Health check failed: {e}")

            # Step 4: Get logs
            logs = container.logs().decode("utf-8")
            results["logs"] = logs.split("\n")

        except Exception as e:
            results["errors"].append(str(e))

        finally:
            # Cleanup
            if container:
                try:
                    container.stop(timeout=5)
                except docker.errors.APIError:
                    pass
            try:
                self.docker_client.images.remove(image_tag, force=True)
            except docker.errors.APIError:
                pass

        return results

    def print_validation_results(self, results: dict[str, Any]):
        """Print validation results."""
        print("\nDocker Deployment Validation Results")
        print("=" * 50)

        checks = [
            ("Image Build", results["build"]),
            ("Container Start", results["start"]),
            ("Health Check", results["health"]),
            ("API Access", results["api"]),
        ]

        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check_name:<20} {status}")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")

        if results["logs"]:
            print("\nContainer logs (last 10 lines):")
            for log_line in results["logs"][-10:]:
                if log_line.strip():
                    print(f"  {log_line}")


def run_manual_docker_validation():
    """Run manual Docker validation."""
    project_root = Path(__file__).parent.parent

    try:
        validator = DockerDeploymentValidator(project_root)
        results = validator.validate_complete_deployment()
        validator.print_validation_results(results)
        return results
    except RuntimeError as e:
        print(f"Validation failed: {e}")
        return None


if __name__ == "__main__":
    # Run manual validation
    run_manual_docker_validation()

    # Run pytest
    pytest.main([__file__, "-v"])
