"""
seed_data.py — Seed the database with test data for development.

Creates sample playgroups, users (admin, teachers, parents), and children.
Does NOT create photos — use the app to upload those.

Usage:
    python execution/seed_data.py

Reads DATABASE_URL_SYNC from .env
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import date

from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import text
from passlib.context import CryptContext

# Load environment
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL_SYNC not set in .env")
    sys.exit(1)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def main():
    print("=" * 50)
    print("moments4u — Seed Development Data")
    print("=" * 50)

    engine = sa.create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # ── Playgroup ──
        pg_id = uuid.uuid4()
        conn.execute(text("""
            INSERT INTO playgroups (id, name, description)
            VALUES (:id, :name, :desc)
            ON CONFLICT DO NOTHING
        """), {
            "id": str(pg_id),
            "name": "Sunshine Playgroup",
            "desc": "A friendly playgroup for ages 2-5",
        })
        print(f"✅ Playgroup: Sunshine Playgroup ({pg_id})")

        # ── Admin ──
        admin_id = uuid.uuid4()
        conn.execute(text("""
            INSERT INTO users (id, email, password_hash, full_name, role, playgroup_id)
            VALUES (:id, :email, :pw, :name, 'admin', :pg_id)
            ON CONFLICT (email) DO NOTHING
        """), {
            "id": str(admin_id),
            "email": "admin@moments4u.test",
            "pw": hash_password("admin123"),
            "name": "Admin User",
            "pg_id": str(pg_id),
        })
        print(f"✅ Admin: admin@moments4u.test / admin123")

        # ── Teachers ──
        teacher_ids = []
        for i, name in enumerate(["Sarah Teacher", "Mike Teacher"], 1):
            tid = uuid.uuid4()
            teacher_ids.append(tid)
            email = f"teacher{i}@moments4u.test"
            conn.execute(text("""
                INSERT INTO users (id, email, password_hash, full_name, role, playgroup_id)
                VALUES (:id, :email, :pw, :name, 'teacher', :pg_id)
                ON CONFLICT (email) DO NOTHING
            """), {
                "id": str(tid),
                "email": email,
                "pw": hash_password("teacher123"),
                "name": name,
                "pg_id": str(pg_id),
            })
            print(f"✅ Teacher: {email} / teacher123")

        # ── Children ──
        children = [
            ("Emma Smith", date(2022, 3, 15)),
            ("Liam Johnson", date(2021, 8, 22)),
            ("Sophia Williams", date(2023, 1, 10)),
        ]
        child_ids = []
        for name, dob in children:
            cid = uuid.uuid4()
            child_ids.append(cid)
            conn.execute(text("""
                INSERT INTO children (id, full_name, date_of_birth, playgroup_id)
                VALUES (:id, :name, :dob, :pg_id)
                ON CONFLICT DO NOTHING
            """), {
                "id": str(cid),
                "name": name,
                "dob": dob.isoformat(),
                "pg_id": str(pg_id),
            })
            print(f"✅ Child: {name} ({cid})")

        # ── Parents (one per child for simplicity) ──
        for i, (child_name, child_id) in enumerate(zip(
            [c[0] for c in children], child_ids
        ), 1):
            pid = uuid.uuid4()
            last_name = child_name.split()[-1]
            email = f"parent.{last_name.lower()}@moments4u.test"
            conn.execute(text("""
                INSERT INTO users (id, email, password_hash, full_name, role, playgroup_id)
                VALUES (:id, :email, :pw, :name, 'parent', :pg_id)
                ON CONFLICT (email) DO NOTHING
            """), {
                "id": str(pid),
                "email": email,
                "pw": hash_password("parent123"),
                "name": f"Parent {last_name}",
                "pg_id": str(pg_id),
            })

            conn.execute(text("""
                INSERT INTO parent_children (parent_id, child_id)
                VALUES (:pid, :cid)
                ON CONFLICT DO NOTHING
            """), {"pid": str(pid), "cid": str(child_id)})

            print(f"✅ Parent: {email} / parent123 → {child_name}")

        conn.commit()

    print("\n✅ Seed data complete!")
    print("\nTest accounts:")
    print("  Admin:   admin@moments4u.test / admin123")
    print("  Teacher: teacher1@moments4u.test / teacher123")
    print("  Parent:  parent.smith@moments4u.test / parent123")

    engine.dispose()


if __name__ == "__main__":
    main()
