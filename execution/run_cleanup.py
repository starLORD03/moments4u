"""
run_cleanup.py — Manually trigger the photo cleanup job.

Use this for emergencies or testing. In production, the Celery Beat
scheduler runs this automatically at 2 AM UTC daily.

Usage:
    python execution/run_cleanup.py              # Dry run (shows what would be deleted)
    python execution/run_cleanup.py --execute     # Actually delete

Reads DATABASE_URL_SYNC, S3_* from .env
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import text

# Load environment
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "moments4u-photos")


def get_expired_photos(conn) -> list[dict]:
    """Find all photos past their expiry date."""
    now = datetime.now(timezone.utc)
    result = conn.execute(text("""
        SELECT p.id, p.s3_key, p.s3_thumbnail_key, p.playgroup_id,
               p.expires_at, p.face_count,
               ARRAY_AGG(f.s3_crop_key) FILTER (WHERE f.s3_crop_key IS NOT NULL) as face_crops
        FROM photos p
        LEFT JOIN faces f ON f.photo_id = p.id
        WHERE p.expires_at <= :now
        GROUP BY p.id
    """), {"now": now})

    photos = []
    for row in result:
        s3_keys = [row.s3_key]
        if row.s3_thumbnail_key:
            s3_keys.append(row.s3_thumbnail_key)
        if row.face_crops:
            s3_keys.extend(row.face_crops)

        photos.append({
            "id": row.id,
            "s3_keys": s3_keys,
            "playgroup_id": row.playgroup_id,
            "expires_at": row.expires_at,
            "face_count": row.face_count,
        })

    return photos


def delete_from_s3(keys: list[str]):
    """Delete objects from S3/MinIO."""
    import boto3

    s3_client = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION", "us-east-1"),
    )

    # Batch delete (max 1000 per request)
    deleted = 0
    for i in range(0, len(keys), 1000):
        batch = keys[i : i + 1000]
        objects = [{"Key": k} for k in batch]
        s3_client.delete_objects(
            Bucket=S3_BUCKET,
            Delete={"Objects": objects, "Quiet": True},
        )
        deleted += len(batch)

    return deleted


def delete_from_db(conn, photo_ids: list):
    """Delete photo records (faces cascade)."""
    if not photo_ids:
        return 0

    # Convert to strings for the query
    id_list = [str(pid) for pid in photo_ids]
    conn.execute(text(
        "DELETE FROM photos WHERE id = ANY(:ids)"
    ), {"ids": id_list})
    conn.commit()
    return len(id_list)


def main():
    parser = argparse.ArgumentParser(description="moments4u photo cleanup")
    parser.add_argument("--execute", action="store_true", help="Actually delete (default: dry run)")
    args = parser.parse_args()

    print("=" * 50)
    print("moments4u — Photo Cleanup")
    print(f"Mode: {'🔴 EXECUTE' if args.execute else '🟡 DRY RUN'}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    engine = sa.create_engine(DATABASE_URL)

    with engine.connect() as conn:
        expired = get_expired_photos(conn)

        if not expired:
            print("\n✅ No expired photos found. Nothing to do.")
            return

        # Summary
        total_s3_keys = sum(len(p["s3_keys"]) for p in expired)
        print(f"\n📋 Found {len(expired)} expired photos")
        print(f"   S3 objects to delete: {total_s3_keys}")
        print(f"   Total faces: {sum(p['face_count'] or 0 for p in expired)}")

        # Show details
        for p in expired[:10]:  # Show first 10
            print(f"   • {p['id']} — expired {p['expires_at']} — {len(p['s3_keys'])} S3 objects")
        if len(expired) > 10:
            print(f"   ... and {len(expired) - 10} more")

        if not args.execute:
            print("\n🟡 DRY RUN — no changes made.")
            print("   Run with --execute to delete.")
            return

        # Execute deletion
        print("\n🗑️  Deleting from S3...")
        all_keys = [k for p in expired for k in p["s3_keys"]]
        s3_deleted = delete_from_s3(all_keys)
        print(f"   ✅ Deleted {s3_deleted} S3 objects")

        print("🗑️  Deleting from database...")
        photo_ids = [p["id"] for p in expired]
        db_deleted = delete_from_db(conn, photo_ids)
        print(f"   ✅ Deleted {db_deleted} photo records (faces cascaded)")

        print(f"\n✅ Cleanup complete!")

    engine.dispose()


if __name__ == "__main__":
    main()
