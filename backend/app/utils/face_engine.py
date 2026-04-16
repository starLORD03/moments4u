"""
Face detection and embedding engine — wraps insightface (ArcFace + RetinaFace).

This is a singleton: the model is loaded once and reused across requests.
The buffalo_l model includes both face detection (RetinaFace) and
recognition (ArcFace) in a single pipeline.
"""

import io
import logging
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class FaceEngine:
    """
    Singleton wrapper around insightface for face detection + embedding.

    Usage:
        engine = FaceEngine()
        faces = engine.detect_and_embed(image_bytes)
    """

    _instance: Optional["FaceEngine"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            from insightface.app import FaceAnalysis

            self.app = FaceAnalysis(
                name="buffalo_l",
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            self._initialized = True
            logger.info("FaceEngine initialized with buffalo_l model")
        except Exception as e:
            logger.error(f"Failed to initialize FaceEngine: {e}")
            raise

    def detect_and_embed(
        self,
        image_bytes: bytes,
        min_confidence: float = 0.6,
        min_face_size: int = 50,
    ) -> list[dict]:
        """
        Detect faces and generate embeddings from raw image bytes.

        Args:
            image_bytes: Raw image file bytes (JPEG, PNG, etc.)
            min_confidence: Minimum detection confidence (0-1). Default: 0.6
            min_face_size: Minimum face width/height in pixels. Default: 50

        Returns:
            List of dicts, each containing:
                - bbox: [x1, y1, x2, y2] bounding box coordinates
                - confidence: float detection score
                - embedding: np.ndarray of shape (512,), L2-normalized
                - crop: PIL.Image of the cropped face with padding
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(img)

        faces = self.app.get(img_array)

        results = []
        for face in faces:
            # Filter by confidence
            if face.det_score < min_confidence:
                continue

            # Calculate bounding box dimensions
            bbox = face.bbox.astype(int)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            # Filter tiny faces
            if w < min_face_size or h < min_face_size:
                continue

            # Crop face with 20% padding for better context
            pad_x = int(w * 0.2)
            pad_y = int(h * 0.2)
            crop_box = (
                max(0, bbox[0] - pad_x),
                max(0, bbox[1] - pad_y),
                min(img.width, bbox[2] + pad_x),
                min(img.height, bbox[3] + pad_y),
            )
            crop = img.crop(crop_box)

            results.append({
                "bbox": bbox.tolist(),
                "confidence": float(face.det_score),
                "embedding": face.normed_embedding,  # L2-normalized, shape (512,)
                "crop": crop,
            })

        logger.info(f"Detected {len(results)} faces (from {len(faces)} candidates)")
        return results

    def get_single_embedding(
        self,
        image_bytes: bytes,
        min_confidence: float = 0.7,
    ) -> np.ndarray | None:
        """
        Extract embedding from a photo expected to contain a single face.
        Used for registering a child's reference face.

        Args:
            image_bytes: Raw image bytes.
            min_confidence: Higher threshold for reference photos.

        Returns:
            512-dim embedding or None if no suitable face found.
        """
        faces = self.detect_and_embed(image_bytes, min_confidence=min_confidence)

        if not faces:
            return None

        # If multiple faces, return the largest (most prominent)
        if len(faces) > 1:
            faces.sort(key=lambda f: f["bbox"][2] * f["bbox"][3], reverse=True)

        return faces[0]["embedding"]
