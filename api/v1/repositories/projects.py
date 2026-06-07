import datetime
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_projects(db: Session, *, tenant_key: str):
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              project_id,
              name,
              industry,
              category,
              status,
              created_by,
              created_at,
              updated_at
            FROM monitoring_projects
            WHERE tenant_key = :tenant_key
            ORDER BY updated_at DESC, id DESC
            """
        ),
        {"tenant_key": tenant_key},
    ).mappings().all()


def get_project(db: Session, *, tenant_key: str, project_id: str):
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              project_id,
              name,
              industry,
              category,
              status,
              created_by,
              created_at,
              updated_at
            FROM monitoring_projects
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
            LIMIT 1
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).mappings().first()


def create_project(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    name: str,
    industry: str | None,
    category: str | None,
    status: str,
    created_by: int | None,
    now: datetime.datetime,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO monitoring_projects (
              tenant_key,
              project_id,
              name,
              industry,
              category,
              status,
              created_by,
              created_at,
              updated_at
            )
            VALUES (
              :tenant_key,
              :project_id,
              :name,
              :industry,
              :category,
              :status,
              :created_by,
              :now,
              :now
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "name": name,
            "industry": industry,
            "category": category,
            "status": status,
            "created_by": created_by,
            "now": now,
        },
    )


def list_project_brands(db: Session, *, tenant_key: str, project_id: str):
    return db.execute(
        text(
            """
            SELECT
              brand_id,
              brand_name,
              role,
              aliases,
              status,
              created_at,
              updated_at
            FROM project_brands
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
            ORDER BY
              CASE role
                WHEN 'target' THEN 1
                WHEN 'competitor' THEN 2
                ELSE 3
              END,
              brand_name ASC,
              id ASC
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).mappings().all()


def get_project_brand(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    brand_id: str,
    role: str,
):
    return db.execute(
        text(
            """
            SELECT
              brand_id,
              brand_name,
              role,
              aliases,
              status,
              created_at,
              updated_at
            FROM project_brands
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND brand_id = :brand_id
              AND role = :role
            LIMIT 1
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "brand_id": brand_id,
            "role": role,
        },
    ).mappings().first()


def upsert_project_brand(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    brand_id: str,
    brand_name: str,
    role: str,
    aliases: list[str],
    status: str,
    now: datetime.datetime,
) -> None:
    aliases_json = json.dumps(aliases, ensure_ascii=False)
    existing = get_project_brand(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        brand_id=brand_id,
        role=role,
    )
    if existing:
        db.execute(
            text(
                """
                UPDATE project_brands
                SET brand_name = :brand_name,
                    aliases = :aliases,
                    status = :status,
                    updated_at = :now
                WHERE tenant_key = :tenant_key
                  AND project_id = :project_id
                  AND brand_id = :brand_id
                  AND role = :role
                """
            ),
            {
                "tenant_key": tenant_key,
                "project_id": project_id,
                "brand_id": brand_id,
                "brand_name": brand_name,
                "role": role,
                "aliases": aliases_json,
                "status": status,
                "now": now,
            },
        )
        return

    db.execute(
        text(
            """
            INSERT INTO project_brands (
              tenant_key,
              project_id,
              brand_id,
              brand_name,
              role,
              aliases,
              status,
              created_at,
              updated_at
            )
            VALUES (
              :tenant_key,
              :project_id,
              :brand_id,
              :brand_name,
              :role,
              :aliases,
              :status,
              :now,
              :now
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "brand_id": brand_id,
            "brand_name": brand_name,
            "role": role,
            "aliases": aliases_json,
            "status": status,
            "now": now,
        },
    )


def list_prompt_sets(db: Session, *, tenant_key: str, project_id: str):
    return db.execute(
        text(
            """
            SELECT
              prompt_set_id,
              version,
              name,
              status,
              created_at,
              updated_at
            FROM prompt_sets
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
            ORDER BY version DESC, id DESC
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).mappings().all()


def get_prompt_set(
    db: Session,
    *,
    tenant_key: str,
    prompt_set_id: str,
):
    return db.execute(
        text(
            """
            SELECT
              prompt_set_id,
              version,
              name,
              status,
              created_at,
              updated_at
            FROM prompt_sets
            WHERE tenant_key = :tenant_key
              AND prompt_set_id = :prompt_set_id
            LIMIT 1
            """
        ),
        {"tenant_key": tenant_key, "prompt_set_id": prompt_set_id},
    ).mappings().first()


def upsert_prompt_set(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    prompt_set_id: str,
    version: int,
    name: str | None,
    status: str,
    now: datetime.datetime,
) -> None:
    existing = get_prompt_set(db, tenant_key=tenant_key, prompt_set_id=prompt_set_id)
    if existing:
        db.execute(
            text(
                """
                UPDATE prompt_sets
                SET version = :version,
                    name = :name,
                    status = :status,
                    updated_at = :now
                WHERE tenant_key = :tenant_key
                  AND prompt_set_id = :prompt_set_id
                """
            ),
            {
                "tenant_key": tenant_key,
                "prompt_set_id": prompt_set_id,
                "version": version,
                "name": name,
                "status": status,
                "now": now,
            },
        )
        return

    db.execute(
        text(
            """
            INSERT INTO prompt_sets (
              tenant_key,
              project_id,
              prompt_set_id,
              version,
              name,
              status,
              created_at,
              updated_at
            )
            VALUES (
              :tenant_key,
              :project_id,
              :prompt_set_id,
              :version,
              :name,
              :status,
              :now,
              :now
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "prompt_set_id": prompt_set_id,
            "version": version,
            "name": name,
            "status": status,
            "now": now,
        },
    )


def get_prompt_item(
    db: Session,
    *,
    tenant_key: str,
    prompt_set_id: str,
    prompt_item_id: str,
):
    return db.execute(
        text(
            """
            SELECT
              prompt_item_id,
              keyword,
              query_content,
              status,
              sort_order,
              created_at,
              updated_at
            FROM prompt_items
            WHERE tenant_key = :tenant_key
              AND prompt_set_id = :prompt_set_id
              AND prompt_item_id = :prompt_item_id
            LIMIT 1
            """
        ),
        {
            "tenant_key": tenant_key,
            "prompt_set_id": prompt_set_id,
            "prompt_item_id": prompt_item_id,
        },
    ).mappings().first()


def upsert_prompt_item(
    db: Session,
    *,
    tenant_key: str,
    prompt_set_id: str,
    prompt_item_id: str,
    keyword: str,
    query_content: str,
    status: str,
    sort_order: int,
    now: datetime.datetime,
) -> None:
    existing = get_prompt_item(
        db,
        tenant_key=tenant_key,
        prompt_set_id=prompt_set_id,
        prompt_item_id=prompt_item_id,
    )
    if existing:
        db.execute(
            text(
                """
                UPDATE prompt_items
                SET keyword = :keyword,
                    query_content = :query_content,
                    status = :status,
                    sort_order = :sort_order,
                    updated_at = :now
                WHERE tenant_key = :tenant_key
                  AND prompt_set_id = :prompt_set_id
                  AND prompt_item_id = :prompt_item_id
                """
            ),
            {
                "tenant_key": tenant_key,
                "prompt_set_id": prompt_set_id,
                "prompt_item_id": prompt_item_id,
                "keyword": keyword,
                "query_content": query_content,
                "status": status,
                "sort_order": sort_order,
                "now": now,
            },
        )
        return

    db.execute(
        text(
            """
            INSERT INTO prompt_items (
              tenant_key,
              prompt_set_id,
              prompt_item_id,
              keyword,
              query_content,
              status,
              sort_order,
              created_at,
              updated_at
            )
            VALUES (
              :tenant_key,
              :prompt_set_id,
              :prompt_item_id,
              :keyword,
              :query_content,
              :status,
              :sort_order,
              :now,
              :now
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "prompt_set_id": prompt_set_id,
            "prompt_item_id": prompt_item_id,
            "keyword": keyword,
            "query_content": query_content,
            "status": status,
            "sort_order": sort_order,
            "now": now,
        },
    )


def list_prompt_items(db: Session, *, tenant_key: str, prompt_set_id: str):
    return db.execute(
        text(
            """
            SELECT
              prompt_item_id,
              keyword,
              query_content,
              status,
              sort_order,
              created_at,
              updated_at
            FROM prompt_items
            WHERE tenant_key = :tenant_key
              AND prompt_set_id = :prompt_set_id
            ORDER BY sort_order ASC, id ASC
            """
        ),
        {"tenant_key": tenant_key, "prompt_set_id": prompt_set_id},
    ).mappings().all()


def mapping_to_dict(row: Any) -> dict[str, Any]:
    return dict(row)
