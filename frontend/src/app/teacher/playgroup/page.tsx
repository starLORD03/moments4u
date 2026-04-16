"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

export default function PlaygroupPage() {
  const { user } = useAuth();
  const [playgroup, setPlaygroup] = useState<any>(null);
  const [children, setChildren] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.playgroup_id) return;

    async function load() {
      try {
        const [pg, ch] = await Promise.all([
          api.playgroups.get(user!.playgroup_id!),
          api.playgroups.children(user!.playgroup_id!),
        ]);
        setPlaygroup(pg);
        setChildren(ch.children || []);
      } catch (err) {
        console.error("Failed to load playgroup:", err);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [user]);

  if (loading) {
    return (
      <div className="loading-screen" style={{ minHeight: "40vh" }}>
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  return (
    <div className="slide-up">
      <h1
        className="font-display"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "var(--space-lg)" }}
      >
        👥 Playgroup
      </h1>

      {/* Playgroup info */}
      {playgroup && (
        <div className="card" style={{ marginBottom: "var(--space-lg)" }}>
          <h2 className="font-semibold" style={{ fontSize: "1.125rem" }}>
            {playgroup.name}
          </h2>
          {playgroup.description && (
            <p className="text-sm text-secondary" style={{ marginTop: 4 }}>
              {playgroup.description}
            </p>
          )}
        </div>
      )}

      {/* Children list */}
      <h3
        className="font-semibold"
        style={{ marginBottom: "var(--space-md)", fontSize: "1rem" }}
      >
        Children ({children.length})
      </h3>

      {children.length === 0 ? (
        <div className="empty-state">
          <p className="text-secondary">No children registered yet.</p>
        </div>
      ) : (
        <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
          {children.map((child) => (
            <div
              key={child.id}
              className="card flex items-center gap-md"
              style={{ padding: "var(--space-md)" }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, var(--color-primary-100), var(--color-accent-100))",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1.25rem",
                  flexShrink: 0,
                }}
              >
                👶
              </div>
              <div>
                <p className="font-semibold">{child.full_name}</p>
                {child.date_of_birth && (
                  <p className="text-sm text-secondary">
                    Born: {new Date(child.date_of_birth).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
