# Directive: Photo Upload Pipeline

## Goal
Handle photo uploads from teachers: validate, store in S3, save metadata, and queue face processing.

## Inputs
- One or more image files (JPEG, PNG, HEIC, WebP)
- `playgroup_id` — which playgroup these photos belong to
- `uploaded_by` — authenticated teacher's user ID
- Optional: `captured_at` timestamp override

## Flow

1. **Auth check** — Verify JWT, role must be `teacher`
2. **Playgroup check** — Teacher must belong to the specified playgroup
3. **Validate files** — Max 20 files, each ≤10MB, allowed MIME types only
4. **Upload to S3** — Key format: `{playgroup_id}/{year}/{month}/{uuid}.enc`
5. **Save to PostgreSQL** — Photo record with `status=processing`, `expires_at=NOW()+7d`
6. **Queue Celery task** — `process_photo_faces.delay(photo_id)`
7. **Return response** — List of uploaded photos with signed thumbnail URLs

## Tools/Scripts
- `backend/app/routers/photos.py` — API endpoint
- `backend/app/services/photo_service.py` — Business logic
- `backend/app/utils/s3.py` — S3 client wrapper

## Outputs
- Photos stored in S3 with encrypted keys
- Photo metadata in PostgreSQL
- Face processing task queued

## Edge Cases
- **HEIC format**: Convert to JPEG before processing (Pillow + pillow-heif)
- **Duplicate uploads**: Idempotent by photo UUID (no dedup by content hash — too expensive)
- **S3 upload failure**: Return in `failed` array, don't block other uploads
- **Large batch**: 20 files × 10MB = 200MB max. Nginx/ALB body limit must accommodate.
- **Network interruption**: Client should implement retry with idempotency key
