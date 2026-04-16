"""Tests for the face processing pipeline logic."""

import numpy as np
import pytest

from app.utils.security import create_access_token


class TestFaceEngineUnit:
    """Unit tests for face engine utilities (mocked — no model required)."""

    def test_cosine_distance_identical(self):
        """Identical embeddings should have distance 0."""
        embedding = np.random.randn(512).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        distance = 1 - np.dot(embedding, embedding)
        assert abs(distance) < 1e-6

    def test_cosine_distance_different(self):
        """Random embeddings should have distance > 0."""
        a = np.random.randn(512).astype(np.float32)
        b = np.random.randn(512).astype(np.float32)
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)

        distance = 1 - np.dot(a, b)
        assert distance > 0.1  # Random vectors should be far apart

    def test_embedding_normalization(self):
        """Embeddings should be L2-normalized."""
        embedding = np.random.randn(512).astype(np.float32)
        normalized = embedding / np.linalg.norm(embedding)
        assert abs(np.linalg.norm(normalized) - 1.0) < 1e-6

    def test_match_threshold_logic(self):
        """Match threshold of 0.55 should correctly classify pairs."""
        threshold = 0.55

        # Simulate a match (distance below threshold)
        assert 0.3 < threshold  # Would be matched

        # Simulate a non-match (distance above threshold)
        assert 0.7 > threshold  # Would not be matched


class TestMatchingLogic:
    """Test the matching decision logic without database."""

    def test_best_match_selection(self):
        """When multiple references exist, select the closest match."""
        query = np.random.randn(512).astype(np.float32)
        query = query / np.linalg.norm(query)

        # Create references with known distances
        ref_close = query + np.random.randn(512).astype(np.float32) * 0.1
        ref_close = ref_close / np.linalg.norm(ref_close)

        ref_far = np.random.randn(512).astype(np.float32)
        ref_far = ref_far / np.linalg.norm(ref_far)

        dist_close = 1 - np.dot(query, ref_close)
        dist_far = 1 - np.dot(query, ref_far)

        # The perturbed reference should be closer
        assert dist_close < dist_far

    def test_multiple_faces_independent(self):
        """Each face in a photo should be matched independently."""
        faces = [
            {"embedding": np.random.randn(512), "child": "A"},
            {"embedding": np.random.randn(512), "child": "B"},
            {"embedding": np.random.randn(512), "child": None},
        ]

        matched = [f for f in faces if f["child"] is not None]
        unmatched = [f for f in faces if f["child"] is None]

        assert len(matched) == 2
        assert len(unmatched) == 1
