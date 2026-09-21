"""Docker Container Builds & Compose Configuration Tests (CHIP DEP-11 / TC-DEP-01, TC-DEP-02).

Validates multi-stage Dockerfiles, non-root user configuration, system dependencies,
and Docker Compose service topology, networking, and health check dependencies.
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_backend_dockerfile_syntax_and_structure() -> None:
    """Verify backend Dockerfile defines multi-stage build and non-root execution (TC-DEP-01)."""
    dockerfile_path = PROJECT_ROOT / "backend" / "Dockerfile"
    assert dockerfile_path.exists(), "backend/Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage validation
    assert "AS builder" in content, "Backend Dockerfile must declare a builder stage"
    assert "AS runtime" in content, "Backend Dockerfile must declare a runtime stage"

    # Non-root user validation
    assert "useradd" in content and "appuser" in content, "Backend Dockerfile must create appuser"
    assert "USER appuser" in content, "Backend Dockerfile must switch to USER appuser"

    # Essential system runtimes
    assert "poppler-utils" in content, "Poppler must be installed for PDF rasterization"
    assert "libgl1" in content or "opencv" in content, (
        "OpenCV graphic dependencies must be installed"
    )

    # Entrypoint and ports
    assert "EXPOSE 8000" in content, "Backend must expose port 8000"
    assert "entrypoint.sh" in content, "Backend must execute entrypoint script"
    assert "HEALTHCHECK" in content, "Backend Dockerfile must define a HEALTHCHECK"


def test_frontend_dockerfile_syntax_and_structure() -> None:
    """Verify frontend Dockerfile defines multi-stage build to Nginx Alpine (TC-DEP-01)."""
    dockerfile_path = PROJECT_ROOT / "frontend" / "Dockerfile"
    assert dockerfile_path.exists(), "frontend/Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage validation
    assert "node:" in content and "AS builder" in content, "Frontend must use Node in builder stage"
    assert "nginx:" in content and "AS runtime" in content, (
        "Frontend must use Nginx in runtime stage"
    )
    assert "npm run build" in content, "Frontend must build production assets"
    assert "COPY --from=builder /app/dist" in content, "Static dist files must be copied to Nginx"
    assert "EXPOSE 80" in content, "Frontend container must expose port 80"
    assert "HEALTHCHECK" in content, "Frontend Dockerfile must define a HEALTHCHECK"


def test_frontend_nginx_configuration() -> None:
    """Verify frontend Nginx configuration supports SPA routing and caching (FR-DEP-01)."""
    nginx_conf = PROJECT_ROOT / "frontend" / "nginx.conf"
    assert nginx_conf.exists(), "frontend/nginx.conf must exist"

    content = nginx_conf.read_text(encoding="utf-8")
    assert "try_files $uri $uri/ /index.html;" in content, "SPA fallback routing must be configured"
    assert "gzip on;" in content, "Gzip compression must be enabled"
    assert "Cache-Control" in content, "Cache control headers must be specified"


def test_docker_compose_structure_and_services() -> None:
    """Verify Docker Compose orchestrates all 4 core services with health checks (TC-DEP-02)."""
    compose_path = PROJECT_ROOT / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    assert "db" in services, "PostgreSQL service 'db' must be configured"
    assert "redis" in services, "Redis service 'redis' must be configured"
    assert "backend" in services, "Backend service 'backend' must be configured"
    assert "frontend" in services, "Frontend service 'frontend' must be configured"

    # Database health check
    db_hc = services["db"].get("healthcheck", {})
    assert "pg_isready" in " ".join(db_hc.get("test", [])), (
        "Database healthcheck must use pg_isready"
    )

    # Redis health check
    redis_hc = services["redis"].get("healthcheck", {})
    assert "ping" in " ".join(redis_hc.get("test", [])), "Redis healthcheck must use redis-cli ping"

    # Backend depends on db and redis health
    backend_deps = services["backend"].get("depends_on", {})
    assert "db" in backend_deps and "redis" in backend_deps, "Backend must depend on db and redis"
    assert backend_deps["db"].get("condition") == "service_healthy", (
        "Backend must wait for db service_healthy"
    )
    assert backend_deps["redis"].get("condition") == "service_healthy", (
        "Backend must wait for redis service_healthy"
    )

    # Frontend depends on backend
    frontend_deps = services["frontend"].get("depends_on", {})
    assert "backend" in frontend_deps, "Frontend must depend on backend"
    assert frontend_deps["backend"].get("condition") == "service_healthy", (
        "Frontend must wait for backend service_healthy"
    )

    # Named persistent volumes
    volumes = compose_data.get("volumes", {})
    assert "postgres_data" in volumes, "postgres_data persistent volume must be defined"
    assert "redis_data" in volumes, "redis_data persistent volume must be defined"
    assert "storage_data" in volumes, "storage_data persistent volume must be defined"


def test_docker_compose_production_override() -> None:
    """Verify production Docker Compose defines reverse proxy gateway and isolates ports.

    Covers (FR-DEP-02, TC-DEP-02).
    """
    prod_path = PROJECT_ROOT / "docker-compose.prod.yml"
    assert prod_path.exists(), "docker-compose.prod.yml must exist"

    with open(prod_path, "r", encoding="utf-8") as f:
        prod_data = yaml.safe_load(f)

    services = prod_data.get("services", {})
    assert "gateway" in services, "Production compose must declare edge gateway service"

    gateway = services["gateway"]
    assert "80:80" in gateway.get("ports", []), "Gateway must map port 80"
    assert "443:443" in gateway.get("ports", []), "Gateway must map port 443"

    # Verify db and redis have empty ports list (not directly exposed externally)
    assert services["db"].get("ports") == [], "Production DB must not expose public host ports"
    assert services["redis"].get("ports") == [], (
        "Production Redis must not expose public host ports"
    )
    assert services["backend"].get("ports") == [], (
        "Production Backend must not expose public host ports directly"
    )
