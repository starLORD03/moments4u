"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState<string>("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function loadChildren() {
      try {
        const res = await api.gallery.myChildren();
        setChildren(res.children || []);
        if (res.children?.length > 0) {
          setSelectedChild(res.children[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadChildren();
  }, []);

  const handleFileChange = (file: File) => {
    setPhoto(file);
    setResult(null);
    setError("");
    const reader = new FileReader();
    reader.onloadend = () => setPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleSubmit = async () => {
    if (!selectedChild || !photo) return;

    setSubmitting(true);
    setError("");
    setResult(null);

    try {
      const res = await api.faces.registerChild(selectedChild, photo);
      setResult(res);
    } catch (err: any) {
      setError(err.detail || "Face registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen" style={{ minHeight: "40vh" }}>
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  return (
    <div className="slide-up" style={{ maxWidth: 500, margin: "0 auto" }}>
      <h1
        className="font-display"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}
      >
        👶 Face Recognition Setup
      </h1>
      <p className="text-secondary" style={{ marginBottom: "var(--space-xl)" }}>
        Upload a clear, well-lit photo of your child&apos;s face. We&apos;ll use it to
        automatically find their photos from playgroup activities.
      </p>

      {/* Step 1: Select child */}
      <div style={{ marginBottom: "var(--space-lg)" }}>
        <label className="label">1. Select your child</label>
        {children.length === 0 ? (
          <p className="text-sm text-secondary">
            No children linked to your account. Contact your playgroup admin.
          </p>
        ) : (
          <select
            className="input"
            value={selectedChild}
            onChange={(e) => setSelectedChild(e.target.value)}
          >
            {children.map((child) => (
              <option key={child.id} value={child.id}>
                {child.full_name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Step 2: Upload photo */}
      <div style={{ marginBottom: "var(--space-lg)" }}>
        <label className="label">2. Upload a clear face photo</label>

        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture="user"
          onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
          style={{ display: "none" }}
        />

        {!preview ? (
          <div
            className="upload-area"
            onClick={() => fileRef.current?.click()}
            style={{ padding: "var(--space-2xl) var(--space-lg)" }}
          >
            <div style={{ fontSize: "2.5rem", marginBottom: "var(--space-sm)" }}>🤳</div>
            <p className="font-semibold">Take a selfie or upload a photo</p>
            <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
              Front-facing, well-lit, no sunglasses
            </p>
          </div>
        ) : (
          <div style={{ position: "relative" }}>
            <div
              style={{
                borderRadius: "var(--border-radius-lg)",
                overflow: "hidden",
                aspectRatio: "1",
                maxWidth: 300,
                margin: "0 auto",
                boxShadow: "var(--shadow-lg)",
              }}
            >
              <img
                src={preview}
                alt="Face preview"
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </div>
            <button
              onClick={() => {
                setPhoto(null);
                setPreview("");
              }}
              className="btn btn-secondary"
              style={{
                display: "block",
                margin: "var(--space-md) auto 0",
                fontSize: "0.875rem",
              }}
            >
              Choose Different Photo
            </button>
          </div>
        )}
      </div>

      {/* Tips */}
      <div
        className="card"
        style={{
          marginBottom: "var(--space-lg)",
          background: "var(--color-accent-50)",
          borderColor: "var(--color-accent-200)",
        }}
      >
        <p className="font-semibold text-sm" style={{ marginBottom: "var(--space-sm)" }}>
          💡 Tips for best results:
        </p>
        <ul
          className="text-sm text-secondary"
          style={{ paddingLeft: "var(--space-md)", display: "flex", flexDirection: "column", gap: 4 }}
        >
          <li>Use a front-facing photo with good lighting</li>
          <li>Avoid sunglasses, masks, or heavy shadows</li>
          <li>One face per photo works best</li>
          <li>You can register 3-5 photos for better accuracy</li>
        </ul>
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        className="btn btn-accent btn-lg"
        disabled={!selectedChild || !photo || submitting}
        style={{ width: "100%" }}
      >
        {submitting ? (
          <>
            <span className="spinner" style={{ width: 20, height: 20, borderWidth: 2, borderTopColor: "white" }} />
            Analyzing Face...
          </>
        ) : (
          "Register Face 🔍"
        )}
      </button>

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

      {/* Success */}
      {result && (
        <div
          className="card fade-in"
          style={{
            marginTop: "var(--space-lg)",
            background: "rgba(34, 197, 94, 0.05)",
            borderColor: "var(--color-success-400)",
          }}
        >
          <div className="flex items-center gap-sm" style={{ marginBottom: "var(--space-sm)" }}>
            <span style={{ fontSize: "1.5rem" }}>🎉</span>
            <h3 className="font-semibold">Face Registered!</h3>
          </div>
          <p className="text-sm text-secondary">
            We found <strong>{result.matched_photos_count}</strong> existing photo
            {result.matched_photos_count !== 1 ? "s" : ""} matching your child.
          </p>
          <button
            onClick={() => router.push("/parent/gallery")}
            className="btn btn-primary"
            style={{ marginTop: "var(--space-md)" }}
          >
            View Gallery →
          </button>
        </div>
      )}
    </div>
  );
}
