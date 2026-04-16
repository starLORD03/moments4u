"use client";

import { useState, useRef, useCallback } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

export default function CapturePage() {
  const { user } = useAuth();
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles).filter((f) =>
      f.type.startsWith("image/")
    );
    setFiles((prev) => [...prev, ...fileArray]);

    // Generate previews
    fileArray.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviews((prev) => [...prev, reader.result as string]);
      };
      reader.readAsDataURL(file);
    });
  }, []);

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (!files.length || !user?.playgroup_id) return;

    setUploading(true);
    setError("");
    setResult(null);

    try {
      const res = await api.photos.upload(user.playgroup_id, files);
      setResult(res);
      setFiles([]);
      setPreviews([]);
    } catch (err: any) {
      setError(err.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="slide-up">
      <h1
        className="font-display"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "var(--space-lg)" }}
      >
        📸 Capture Moments
      </h1>

      {/* Camera + File Input (hidden) */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        onChange={(e) => e.target.files && handleFiles(e.target.files)}
        style={{ display: "none" }}
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        onChange={(e) => e.target.files && handleFiles(e.target.files)}
        style={{ display: "none" }}
      />

      {/* Quick actions */}
      <div className="flex gap-md" style={{ marginBottom: "var(--space-lg)" }}>
        <button
          onClick={() => cameraInputRef.current?.click()}
          className="btn btn-primary btn-lg"
          style={{ flex: 1 }}
        >
          📷 Take Photo
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="btn btn-secondary btn-lg"
          style={{ flex: 1 }}
        >
          📁 Gallery
        </button>
      </div>

      {/* Drop zone */}
      {files.length === 0 && (
        <div
          className={`upload-area ${dragging ? "dragging" : ""}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (e.dataTransfer.files) handleFiles(e.dataTransfer.files);
          }}
        >
          <div className="icon">📷</div>
          <p className="font-semibold" style={{ fontSize: "1.125rem", marginBottom: 4 }}>
            Drag photos here
          </p>
          <p className="text-sm text-secondary">
            or tap to select from camera / gallery
          </p>
          <p className="text-sm text-muted" style={{ marginTop: 8 }}>
            JPEG, PNG, HEIC, WebP — up to 10 MB each
          </p>
        </div>
      )}

      {/* Preview grid */}
      {previews.length > 0 && (
        <div style={{ marginTop: "var(--space-lg)" }}>
          <div className="flex items-center justify-between" style={{ marginBottom: "var(--space-md)" }}>
            <p className="font-semibold">
              {files.length} photo{files.length !== 1 ? "s" : ""} selected
            </p>
            <button
              onClick={() => { setFiles([]); setPreviews([]); }}
              className="btn btn-secondary"
              style={{ padding: "4px 12px", fontSize: "0.8125rem" }}
            >
              Clear All
            </button>
          </div>

          <div className="photo-grid stagger">
            {previews.map((src, i) => (
              <div key={i} className="photo-card">
                <img src={src} alt={`Photo ${i + 1}`} />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(i);
                  }}
                  style={{
                    position: "absolute",
                    top: 6,
                    right: 6,
                    width: 28,
                    height: 28,
                    borderRadius: "50%",
                    background: "rgba(0,0,0,0.6)",
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.875rem",
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>

          {/* Upload button */}
          <button
            onClick={handleUpload}
            className="btn btn-accent btn-lg"
            disabled={uploading}
            style={{ width: "100%", marginTop: "var(--space-lg)" }}
          >
            {uploading ? (
              <>
                <span className="spinner" style={{ width: 20, height: 20, borderWidth: 2, borderTopColor: "white" }} />
                Uploading...
              </>
            ) : (
              `Upload ${files.length} Photo${files.length !== 1 ? "s" : ""}`
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div
          style={{
            marginTop: "var(--space-md)",
            background: "rgba(239, 68, 68, 0.08)",
            color: "var(--color-danger-500)",
            padding: "var(--space-sm) var(--space-md)",
            borderRadius: "var(--border-radius-md)",
            fontSize: "0.875rem",
          }}
        >
          {error}
        </div>
      )}

      {/* Upload result */}
      {result && (
        <div className="card fade-in" style={{ marginTop: "var(--space-lg)" }}>
          <div className="flex items-center gap-sm" style={{ marginBottom: "var(--space-md)" }}>
            <span style={{ fontSize: "1.5rem" }}>✅</span>
            <h3 className="font-semibold">Upload Complete</h3>
          </div>
          <p className="text-sm text-secondary">
            {result.uploaded?.length || 0} photo{(result.uploaded?.length || 0) !== 1 ? "s" : ""} uploaded
            successfully. Face processing is running in the background.
          </p>
          {result.failed?.length > 0 && (
            <div style={{ marginTop: "var(--space-sm)" }}>
              <p className="text-sm" style={{ color: "var(--color-danger-500)" }}>
                {result.failed.length} failed:
              </p>
              {result.failed.map((f: any, i: number) => (
                <p key={i} className="text-sm text-muted">
                  {f.filename}: {f.error}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
