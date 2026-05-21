from unittest.mock import MagicMock, patch

from api.v1.repositories.connection import get_db
from api.v1.routes import executors
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_executor_client():
    app = FastAPI()
    app.include_router(executors.router, prefix="/api/v1/executors")
    db = MagicMock()
    db.commit.return_value = None
    db.rollback.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_create_executor_requires_platform_admin():
    client = _build_executor_client()

    with patch("api.v1.routes.executors.insert_executor"):
        response = client.post(
            "/api/v1/executors/",
            json={"name": "香港机房-爬虫01", "ip_address": "47.91.22.33"},
        )

    assert response.status_code == 401


def test_list_executors_requires_platform_admin():
    client = _build_executor_client()

    with patch("api.v1.routes.executors.list_executor_records", return_value=[]):
        response = client.get("/api/v1/executors/")

    assert response.status_code == 401


def test_deactivate_executor_requires_platform_admin():
    client = _build_executor_client()

    with patch("api.v1.routes.executors.deactivate_executor_record", return_value=1):
        response = client.delete("/api/v1/executors/exec_test")

    assert response.status_code == 401

