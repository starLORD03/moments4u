"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

export default function UploadsPage() {
  const [photos, setPhotos] = useState<any[]>([]);
  const [pagination, setPagination] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const fetchUploads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.photos.myUploads(page, 20);
      setPhotos(res.photos || []);
      setPagination(res.pagination);
    } catch (err) {
      console.error("Failed to load uploads:", err);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchUploads();
  }, [fetchUploads]);

  const handleDelete = async (photoId: string) => {
    if (!confirm("Delete this photo? This cannot be undone.")) return;
    try {
      await api.photos.delete(photoId);
      setPhotos((prev) => prev.filter((p) => p.id !== photoId));
    } catch (err: any) {
      alert(err.detail || "Delete failed");
    }
  };

  const statusBadge = (status: string) => {
    const classes: Record<string, string> = {
      ready: "badge badge-success",
      processing: "badge badge-processing",
      failed: "badge badge-warning",
    };
    const labels: Record<string, string> = {
      ready: "✓ Ready",
      processing: "⏳ Processing",
      failed: "⚠ Failed",
    };
    return <span className={classes[status] || "badge"}>{labels[status] || status}</span>;
  };

  return (
    <div className="slide-up">
      <div className="flex items-center justify-between" style={{ marginBottom: "var(--space-lg)" }}>
        <h1
          className="font-display"
          style={{ fontSize: "1.5rem", fontWeight: 700 }}
        >
          📋 My Uploads
        </h1>
        {pagination && (
          <span className="text-sm text-secondary">
            {pagination.total} photo{pagination.total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {loading ? (
        <div className="loading-screen" style={{ minHeight: "40vh" }}>
          <div className="spinner spinner-lg" />
        </div>
      ) : photos.length === 0 ? (
        <div className="empty-state">
          <div className="icon">📷</div>
          <p className="font-semibold" style={{ fontSize: "1.125rem" }}>
            No uploads yet
          </p>
          <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
            Head to the Capture tab to take some photos!
          </p>
        </div>
      ) : (
        <>
          <div className="photo-grid stagger">
            {photos.map((photo) => (
              <div key={photo.id} className="photo-card" style={{ position: "relative" }}>
                {photo.thumbnail_url ? (
                  <img src={photo.thumbnail_url} alt="Uploaded photo" loading="lazy" />
                ) : (
                  <div
                    className="flex items-center justify-center"
                    style={{
                      width: "100%",
                      height: "100%",
                      background: "var(--color-gray-100)",
                      color: "var(--text-muted)",
                      fontSize: "2rem",
                    }}
                  >
                    📷
                  </div>
                )}
                <div className="overlay">
                  <div className="flex items-center justify-between">
                    {statusBadge(photo.status)}
                    {photo.face_count > 0 && (
                      <span style={{ fontSize: "0.6875rem" }}>
                        👤 {photo.face_count}
                      </span>
                    )}
                  </div>
                </div>
                {/* Delete button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(photo.id);
                  }}
                  title="Delete photo"
                  style={{
                    position: "absolute",
                    top: 6,
                    right: 6,
                    width: 26,
                    height: 26,
                    borderRadius: "50%",
                    background: "rgba(0,0,0,0.5)",
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.75rem",
                    opacity: 0,
                    transition: "opacity var(--transition-fast)",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = "0")}
                >
                  🗑
                </button>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div
              className="flex items-center justify-center gap-md"
              style={{ marginTop: "var(--space-xl)" }}
            >
              <button
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                ← Prev
              </button>
              <span className="text-sm text-secondary">
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page >= pagination.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
