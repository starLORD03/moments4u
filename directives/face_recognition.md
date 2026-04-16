# Directive: Face Recognition Pipeline

## Goal
Detect faces in uploaded photos, generate embeddings, and match faces to known children.

## Inputs
- `photo_id` — UUID of the uploaded photo
- Photo bytes from S3

## Pipeline

### Step 1: Download image from S3
- Use the S3 key from the photo record

### Step 2: Face Detection (RetinaFace via insightface)
- Model: `buffalo_l`
- Detection size: 640×640
- Filter: confidence ≥ 0.6, face size ≥ 50×50px

### Step 3: Face Cropping
- Crop each detected face with 20% padding
- Save crop to S3: `faces/{playgroup_id}/{photo_id}/{face_id}.jpg`

### Step 4: Embedding Generation (ArcFace)
- 512-dimensional L2-normalized embedding per face
- Generated as part of insightface pipeline (no separate step)

### Step 5: Similarity Search (pgvector)
```sql
SELECT child_id, embedding <=> :query_embedding AS distance
FROM child_reference_faces
WHERE child_id IN (SELECT id FROM children WHERE playgroup_id = :pg_id)
ORDER BY embedding <=> :query_embedding
LIMIT 1
```
- Match threshold: distance < 0.55 (cosine distance)
- Lower distance = better match

### Step 6: Save Results
- Create `face` record with embedding, bbox, match status
- Update photo: `status=ready`, `face_count=N`

### Step 7: Notifications (optional)
- If matched, queue push notification to parent(s)

## Tools/Scripts
- `backend/app/utils/face_engine.py` — insightface wrapper (singleton)
- `backend/app/tasks/face_processing.py` — Celery task
- `backend/app/services/face_service.py` — Business logic

## Outputs
- Face records in PostgreSQL with embeddings
- Face crops in S3
- Photo status updated to `ready`

## Key Parameters
| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | `buffalo_l` | Best accuracy/speed ratio |
| Embedding dim | 512 | ArcFace standard |
| Match threshold | 0.55 | Tuned for children — they change fast |
| Min confidence | 0.6 | Filters noise |
| Min face size | 50×50 | Below this, embeddings are unreliable |
| Ref faces/child | 3-5 | Multiple angles improve recall |

## Edge Cases
- **No faces detected**: Set `face_count=0`, status still `ready`
- **Multiple faces**: Each processed independently, photo may appear in multiple galleries
- **Twins/siblings**: May cross-match. Teacher can manually correct via admin UI
- **New child (no refs)**: Saved as `unmatched`. Retroactively matched when parent registers
- **Blurry/dark photo**: Low detection confidence → face skipped
- **Partial occlusion**: RetinaFace handles well; if confidence < 0.6, skipped
- **insightface model not downloaded**: First run auto-downloads ~300MB. Allow network access.

## Learnings
- (Add learnings here as the pipeline is tested in production)
