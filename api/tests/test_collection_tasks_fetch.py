from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import collection_tasks
from api.v1.routes.query_jobs import verify_executor
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"


@pytest.fixture()
def collection_task_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        raw_connection = conn.connection.driver_connection
        raw_connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _client(db_session, *, executor_id="exec_a"):
    app = FastAPI()
    app.include_router(collection_tasks.router, prefix="/api/v1/collection-tasks")
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[verify_executor] = lambda: executor_id
    return TestClient(app)


def _seed_base(session: Session):
    now = datetime(2026, 6, 7, 8, 0, 0, tzinfo=UTC)
    for tenant_key, tenant_name, project_id, prompt_set_id in (
        ("tn_a", "Tenant A", "proj_a", "prompt_set_a"),
        ("tn_b", "Tenant B", "proj_b", "prompt_set_b"),
    ):
        session.execute(
            text(
                """
                INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
                VALUES (:tenant_key, :tenant_name, 'active', :now, :now)
                """
            ),
            {"tenant_key": tenant_key, "tenant_name": tenant_name, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO monitoring_projects
                  (tenant_key, project_id, name, industry, category, status, created_at, updated_at)
                VALUES
                  (:tenant_key, :project_id, :project_id, 'education', 'k12', 'active', :now, :now)
                """
            ),
            {
                "tenant_key": tenant_key,
                "project_id": project_id,
                "now": now,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO prompt_sets
                  (
                    tenant_key,
                    project_id,
                    prompt_set_id,
                    version,
                    name,
                    status,
                    created_at,
                    updated_at
                  )
                VALUES
                  (
                    :tenant_key,
                    :project_id,
                    :prompt_set_id,
                    1,
                    :prompt_set_id,
                    'active',
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "project_id": project_id,
                "prompt_set_id": prompt_set_id,
                "now": now,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO prompt_items
                  (
                    tenant_key,
                    prompt_set_id,
                    prompt_item_id,
                    keyword,
                    query_content,
                    status,
                    created_at,
                    updated_at
                  )
                VALUES
                  (
                    :tenant_key,
                    :prompt_set_id,
                    :prompt_item_id,
                    'math',
                    '数学培训哪家好',
                    'active',
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "prompt_set_id": prompt_set_id,
                "prompt_item_id": f"prompt_item_{tenant_key}",
                "now": now,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO collection_jobs
                  (
                    tenant_key,
                    collection_job_id,
                    project_id,
                    prompt_set_id,
                    status,
                    window_start,
                    window_end,
                    expected_task_count,
                    created_at,
                    updated_at
                  )
                VALUES
                  (
                    :tenant_key,
                    :collection_job_id,
                    :project_id,
                    :prompt_set_id,
                    'pending',
                    :window_start,
                    :window_end,
                    2,
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "collection_job_id": f"collection_job_{tenant_key}",
                "project_id": project_id,
                "prompt_set_id": prompt_set_id,
                "window_start": now - timedelta(hours=1),
                "window_end": now + timedelta(hours=1),
                "now": now,
            },
        )

    for executor_id in ("exec_a", "exec_b", "exec_old"):
        session.execute(
            text(
                """
                INSERT INTO executors
                  (executor_id, name, status, ip_address, api_key, created_at, updated_at)
                VALUES
                  (:executor_id, :executor_id, 'active', '127.0.0.1', :executor_id, :now, :now)
                """
            ),
            {"executor_id": executor_id, "now": now},
        )
    session.flush()


def _seed_task(
    session: Session,
    *,
    task_id: str,
    tenant_key: str = "tn_a",
    status: str = "pending",
    lease_owner: str | None = None,
    lease_until: datetime | None = None,
    run_index: int = 1,
):
    now = datetime(2026, 6, 7, 8, 0, 0, tzinfo=UTC)
    prompt_set_id = "prompt_set_a" if tenant_key == "tn_a" else "prompt_set_b"
    project_id = "proj_a" if tenant_key == "tn_a" else "proj_b"
    session.execute(
        text(
            """
            INSERT INTO collection_tasks
              (
                tenant_key,
                collection_task_id,
                collection_job_id,
                project_id,
                prompt_set_id,
                prompt_item_id,
                platform,
                query_content,
                run_index,
                status,
                lease_owner,
                lease_until,
                attempt_count,
                max_attempts,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :task_id,
                :collection_job_id,
                :project_id,
                :prompt_set_id,
                :prompt_item_id,
                'deepseek',
                :query_content,
                :run_index,
                :status,
                :lease_owner,
                :lease_until,
                0,
                3,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "task_id": task_id,
            "collection_job_id": f"collection_job_{tenant_key}",
            "project_id": project_id,
            "prompt_set_id": prompt_set_id,
            "prompt_item_id": f"prompt_item_{tenant_key}",
            "query_content": f"{tenant_key}:{task_id}",
            "run_index": run_index,
            "status": status,
            "lease_owner": lease_owner,
            "lease_until": lease_until,
            "now": now,
        },
    )
    session.flush()


def _fetch(client: TestClient, *, executor_id="exec_a", tenant_key="tn_a", lease_seconds=120):
    return client.get(
        "/api/v1/collection-tasks/fetch",
        params={
            "executor_id": executor_id,
            "tenant_key": tenant_key,
            "lease_seconds": lease_seconds,
        },
    )


def test_fetch_claims_pending_task_with_lease(collection_task_session):
    _seed_base(collection_task_session)
    _seed_task(collection_task_session, task_id="task_1")
    collection_task_session.commit()
    client = _client(collection_task_session, executor_id="exec_a")

    response = _fetch(client, executor_id="exec_a")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["count"] == 1
    assert body["task"]["collection_task_id"] == "task_1"
    assert body["task"]["status"] == "reserved"
    assert body["task"]["lease_owner"] == "exec_a"
    assert body["task"]["lease_until"] is not None

    row = collection_task_session.execute(
        text(
            """
            SELECT status, lease_owner, lease_until
            FROM collection_tasks
            WHERE collection_task_id = 'task_1'
            """
        )
    ).one()
    assert row.status == "reserved"
    assert row.lease_owner == "exec_a"
    assert row.lease_until is not None


def test_fetches_do_not_claim_the_same_task_twice(collection_task_session):
    _seed_base(collection_task_session)
    _seed_task(collection_task_session, task_id="task_1", run_index=1)
    _seed_task(collection_task_session, task_id="task_2", run_index=2)
    collection_task_session.commit()

    first_response = _fetch(
        _client(collection_task_session, executor_id="exec_a"),
        executor_id="exec_a",
    )
    second_response = _fetch(
        _client(collection_task_session, executor_id="exec_b"),
        executor_id="exec_b",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["task"]["collection_task_id"] == "task_1"
    assert second_response.json()["task"]["collection_task_id"] == "task_2"


def test_fetch_skips_task_with_active_lease_owned_by_another_executor(
    collection_task_session,
):
    _seed_base(collection_task_session)
    _seed_task(
        collection_task_session,
        task_id="task_reserved",
        status="reserved",
        lease_owner="exec_a",
        lease_until=datetime.now(UTC) + timedelta(minutes=10),
    )
    collection_task_session.commit()
    client = _client(collection_task_session, executor_id="exec_b")

    response = _fetch(client, executor_id="exec_b")

    assert response.status_code == 200
    assert response.json() == {"success": True, "count": 0, "task": None}

    row = collection_task_session.execute(
        text(
            """
            SELECT status, lease_owner
            FROM collection_tasks
            WHERE collection_task_id = 'task_reserved'
            """
        )
    ).one()
    assert row.status == "reserved"
    assert row.lease_owner == "exec_a"


def test_fetch_reclaims_task_after_lease_expires(collection_task_session):
    _seed_base(collection_task_session)
    _seed_task(
        collection_task_session,
        task_id="task_expired",
        status="reserved",
        lease_owner="exec_old",
        lease_until=datetime.now(UTC) - timedelta(seconds=1),
    )
    collection_task_session.commit()
    client = _client(collection_task_session, executor_id="exec_b")

    response = _fetch(client, executor_id="exec_b")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["task"]["collection_task_id"] == "task_expired"
    assert body["task"]["lease_owner"] == "exec_b"

    row = collection_task_session.execute(
        text(
            """
            SELECT status, lease_owner, lease_until
            FROM collection_tasks
            WHERE collection_task_id = 'task_expired'
            """
        )
    ).one()
    assert row.status == "reserved"
    assert row.lease_owner == "exec_b"
    assert row.lease_until is not None


def test_fetch_filters_by_tenant_key(collection_task_session):
    _seed_base(collection_task_session)
    _seed_task(collection_task_session, task_id="task_a", tenant_key="tn_a")
    _seed_task(collection_task_session, task_id="task_b", tenant_key="tn_b")
    collection_task_session.commit()
    client = _client(collection_task_session, executor_id="exec_a")

    response = _fetch(client, executor_id="exec_a", tenant_key="tn_b")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["task"]["tenant_key"] == "tn_b"
    assert response.json()["task"]["collection_task_id"] == "task_b"
