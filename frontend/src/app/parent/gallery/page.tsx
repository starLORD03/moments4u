"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface Child {
  id: string;
  full_name: string;
  date_of_birth: string | null;
}

export default function GalleryPage() {
  const router = useRouter();
  const [children, setChildren] = useState<Child[]>([]);
  const [selectedChild, setSelectedChild] = useState<Child | null>(null);
  const [gallery, setGallery] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [page, setPage] = useState(1);

  // Load children on mount
  useEffect(() => {
    async function loadChildren() {
      try {
        const res = await api.gallery.myChildren();
        setChildren(res.children || []);
        if (res.children?.length > 0) {
          setSelectedChild(res.children[0]);
        }
      } catch (err) {
        console.error("Failed to load children:", err);
      } finally {
        setLoading(false);
      }
    }
    loadChildren();
  }, []);

  // Load gallery when child changes
  useEffect(() => {
    if (!selectedChild) return;

    async function loadGallery() {
      setGalleryLoading(true);
      try {
        const res = await api.gallery.childPhotos(selectedChild!.id, page);
        setGallery(res);
      } catch (err) {
        console.error("Failed to load gallery:", err);
      } finally {
        setGalleryLoading(false);
      }
    }
    loadGallery();
  }, [selectedChild, page]);

  if (loading) {
    return (
      <div className="loading-screen" style={{ minHeight: "40vh" }}>
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  if (children.length === 0) {
    return (
      <div className="slide-up">
        <div className="empty-state">
          <div className="icon">👶</div>
          <h2 className="font-semibold" style={{ fontSize: "1.25rem", marginBottom: 8 }}>
            No children linked yet
          </h2>
          <p className="text-secondary" style={{ marginBottom: "var(--space-lg)" }}>
            Ask your playgroup admin to link your child to your account.
          </p>
          <button
            onClick={() => router.push("/parent/onboarding")}
            className="btn btn-primary"
          >
            Set Up Face Recognition
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="slide-up">
      {/* Child selector (if multiple children) */}
      {children.length > 1 && (
        <div
          className="flex gap-sm"
          style={{
            marginBottom: "var(--space-lg)",
            overflowX: "auto",
            paddingBottom: 4,
          }}
        >
          {children.map((child) => (
            <button
              key={child.id}
              onClick={() => {
                setSelectedChild(child);
                setPage(1);
              }}
              className={`btn ${
                selectedChild?.id === child.id ? "btn-primary" : "btn-secondary"
              }`}
              style={{ whiteSpace: "nowrap", flexShrink: 0 }}
            >
              👶 {child.full_name}
            </button>
          ))}
        </div>
      )}

      {/* Gallery header */}
      {selectedChild && (
        <div style={{ marginBottom: "var(--space-lg)" }}>
          <h1
            className="font-display"
            style={{ fontSize: "1.5rem", fontWeight: 700 }}
          >
            {selectedChild.full_name}&apos;s Moments
          </h1>
          {gallery?.pagination && (
            <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
              {gallery.pagination.total} photo{gallery.pagination.total !== 1 ? "s" : ""}
            </p>
          )}
        </div>
      )}

      {/* Gallery loading */}
      {galleryLoading ? (
        <div className="loading-screen" style={{ minHeight: "30vh" }}>
          <div className="spinner spinner-lg" />
        </div>
      ) : !gallery?.timeline?.length ? (
        <div className="empty-state">
          <div className="icon">📷</div>
          <h3 className="font-semibold" style={{ marginBottom: 4 }}>
            No photos yet
          </h3>
          <p className="text-sm text-secondary">
            Photos will appear here once your child&apos;s face is matched.
          </p>
          <button
            onClick={() => router.push("/parent/onboarding")}
            className="btn btn-accent"
            style={{ marginTop: "var(--space-md)" }}
          >
            Register Face →
          </button>
        </div>
      ) : (
        <>
          {/* Timeline */}
          {gallery.timeline.map((day: any) => (
            <div key={day.date} className="timeline-day">
              <div className="timeline-day-header">
                📅{" "}
                {new Date(day.date + "T00:00:00").toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                })}
              </div>
              <div className="photo-grid stagger">
                {day.photos.map((photo: any) => (
                  <div key={photo.id} className="photo-card">
                    <img
                      src={photo.thumbnail_url || photo.image_url}
                      alt="Child's moment"
                      loading="lazy"
                    />
                    <div className="overlay">
                      <span style={{ fontSize: "0.6875rem" }}>
                        {photo.captured_at
                          ? new Date(photo.captured_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : ""}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Expiry notice */}
          <div
            className="card"
            style={{
              marginTop: "var(--space-lg)",
              background: "var(--color-primary-50)",
              borderColor: "var(--color-primary-200)",
              textAlign: "center",
            }}
          >
            <p className="text-sm">
              ⏳ Photos are automatically deleted after <strong>7 days</strong>.
              Download any photos you&apos;d like to keep!
            </p>
          </div>

          {/* Pagination */}
          {gallery.pagination && gallery.pagination.total_pages > 1 && (
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
                Page {page} of {gallery.pagination.total_pages}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page >= gallery.pagination.total_pages}
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
