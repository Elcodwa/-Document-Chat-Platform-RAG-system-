"""
Creates a demo tenant with an admin user and two pre-configured database
connections (pointing at the sample "demo_business" data seeded into the
Postgres and MySQL containers by infra/postgres/init and infra/mysql/init)
so you have something to explore immediately after `docker compose up`,
without manually typing in connection details first.

Usage (from your host machine, once the stack is running):

    docker compose exec backend python scripts/seed_demo_data.py

Safe to run more than once - it skips creating anything that already
exists.
"""
import sys

from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.encryption import encrypt_value
from core.security import hash_password
from models.database_connection import DatabaseConnection
from models.tenant import Tenant
from models.user import User
from repositories.tenant_repo import TenantRepository
from repositories.user_repo import UserRepository
from services.database.connection_tester import test_connection
from services.database.schema_discovery import sync_schema

DEMO_TENANT_CODE = "demo"
DEMO_TENANT_NAME = "Demo Company"
DEMO_ADMIN_EMAIL = "demo@example.com"
DEMO_ADMIN_PASSWORD = "demo12345"


def seed(db: Session) -> None:
    tenant_repo = TenantRepository(db)
    user_repo = UserRepository(db)

    tenant = tenant_repo.get_by_code(DEMO_TENANT_CODE)
    if tenant is None:
        import uuid

        tenant = Tenant(id=uuid.uuid4(), name=DEMO_TENANT_NAME, code=DEMO_TENANT_CODE)
        db.add(tenant)
        db.flush()
        print(f"Created tenant '{DEMO_TENANT_NAME}' ({tenant.id})")
    else:
        print(f"Tenant '{DEMO_TENANT_NAME}' already exists, reusing it.")

    admin = user_repo.get_by_email(tenant.id, DEMO_ADMIN_EMAIL)
    if admin is None:
        import uuid

        admin = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=DEMO_ADMIN_EMAIL,
            full_name="Demo Admin",
            password_hash=hash_password(DEMO_ADMIN_PASSWORD),
            is_tenant_admin=True,
        )
        db.add(admin)
        db.flush()
        print(f"Created admin user: {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")
    else:
        print(f"Admin user {DEMO_ADMIN_EMAIL} already exists, reusing it.")

    db.commit()

    _seed_connection(
        db,
        tenant,
        admin,
        name="Demo Postgres (sample e-commerce data)",
        database_type="postgresql",
        host="postgres",
        port=5432,
        database_name="demo_business",
        username="postgres",
        password="postgres",
    )
    _seed_connection(
        db,
        tenant,
        admin,
        name="Demo MySQL (sample product catalog)",
        database_type="mysql",
        host="mysql",
        port=3306,
        database_name="demo_business",
        username="root",
        password="root",
    )

    print("\nDone. Log in at http://localhost:3000 with:")
    print(f"  email:    {DEMO_ADMIN_EMAIL}")
    print(f"  password: {DEMO_ADMIN_PASSWORD}")


def _seed_connection(db: Session, tenant, admin, *, name, database_type, host, port, database_name, username, password):
    from repositories.connection_repo import ConnectionRepository

    repo = ConnectionRepository(db)
    existing = repo.get_by_name(tenant.id, name)
    if existing is not None:
        print(f"Connection '{name}' already exists, reusing it.")
        connection = existing
    else:
        import uuid

        connection = DatabaseConnection(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            created_by=admin.id,
            name=name,
            database_type=database_type,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            encrypted_password=encrypt_value(password),
        )
        db.add(connection)
        db.commit()
        print(f"Created connection '{name}'.")

    result = test_connection(connection)
    print(f"  test connection -> {result.success}: {result.message}")
    if result.success:
        sync_result = sync_schema(db, connection)
        print(f"  synced schema -> {sync_result.table_count} tables, {sync_result.column_count} columns")


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed(session)
    except Exception as exc:  # noqa: BLE001
        print(f"Seeding failed: {exc}", file=sys.stderr)
        raise
    finally:
        session.close()
