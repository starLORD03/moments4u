"""
setup_db.py — Initialize the moments4u database.

Creates the database, enables required extensions (pgvector, uuid-ossp),
and runs all Alembic migrations.

Usage:
    python execution/setup_db.py

Reads DATABASE_URL_SYNC from .env
"""

import os
import sys
import subprocess
from pathlib import Path

from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import text

# Load environment
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL_SYNC not set in .env")
    sys.exit(1)


def create_extensions(engine: sa.Engine):
    """Enable required PostgreSQL extensions."""
    extensions = ["vector", "uuid-ossp"]
    with engine.connect() as conn:
        for ext in extensions:
            try:
                conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}"'))
                conn.commit()
                print(f"  ✅ Extension '{ext}' enabled")
            except Exception as e:
                print(f"  ⚠️  Extension '{ext}' failed: {e}")
                conn.rollback()


def run_migrations():
    """Run Alembic migrations."""
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    alembic_ini = backend_dir / "alembic.ini"

    if not alembic_ini.exists():
        print("  ⚠️  alembic.ini not found — skipping migrations.")
        print("     Run 'alembic init alembic' in backend/ first.")
        return

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  ✅ Migrations applied successfully")
        if result.stdout.strip():
            print(f"     {result.stdout.strip()}")
    else:
        print(f"  ❌ Migration failed:\n{result.stderr}")


def main():
    print("=" * 50)
    print("moments4u — Database Setup")
    print("=" * 50)

    print(f"\n📦 Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

    engine = sa.create_engine(DATABASE_URL)

    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  ✅ Connected to PostgreSQL: {version[:60]}...")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        print("     Is PostgreSQL running? Check DATABASE_URL_SYNC in .env")
        sys.exit(1)

    # Enable extensions
    print("\n🔧 Enabling extensions...")
    create_extensions(engine)

    # Run migrations
    print("\n📐 Running migrations...")
    run_migrations()

    print("\n✅ Database setup complete!")
    engine.dispose()


if __name__ == "__main__":
    main()
