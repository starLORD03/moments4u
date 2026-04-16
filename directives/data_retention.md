# Directive: Data Retention & Cleanup

## Goal
Automatically delete photos and associated data after 7 days to comply with privacy policy.

## Schedule
- **Celery Beat**: Daily at 2:00 AM UTC
- Task: `app.tasks.cleanup.cleanup_expired_photos`

## Deletion Order (CRITICAL)
Must follow this exact order to prevent orphaned data:

1. **Collect S3 keys** — originals, thumbnails, face crops
2. **Delete from S3** — batch delete (up to 1000 keys per call)
3. **Delete from PostgreSQL** — `DELETE FROM photos WHERE expires_at <= NOW()`
   - `faces` table CASCADE deletes automatically
4. **Clear Redis cache** — invalidate any cached signed URLs
5. **Audit log** — Record deletion count, timestamp (never delete audit logs)

## Tools/Scripts
- `backend/app/tasks/cleanup.py` — Celery scheduled task
- `execution/run_cleanup.py` — Manual cleanup trigger (for emergencies)

## Inputs
- None (scheduled task reads `expires_at` from database)

## Outputs
- Deleted photos from S3 and PostgreSQL
- Audit log entry with counts

## Edge Cases
- **Partial failure (S3 deleted, DB not)**: Task is idempotent. Re-run will skip already-deleted S3 keys and finish DB cleanup.
- **Large batch (1000+ photos)**: S3 batch delete handles 1000 keys at a time. Loop in batches.
- **Photo still being processed**: Don't delete photos with `status=processing` even if expired — wait for next cycle.
- **Race condition with active viewer**: Signed URLs expire after 1h. If a parent is viewing a photo that gets deleted, the URL will 404 gracefully.

## Verification
```sql
-- Check for orphaned data (should return 0)
SELECT COUNT(*) FROM faces WHERE photo_id NOT IN (SELECT id FROM photos);

-- Check S3 vs DB consistency (run monthly)
-- Compare S3 object count with DB photo count
```

## Learnings
- (Add learnings here as cleanup runs in production)
