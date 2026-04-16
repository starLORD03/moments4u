"use client";

import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useEffect } from "react";

export default function TeacherLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && (!user || !["teacher", "admin"].includes(user.role))) {
      router.replace("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return (
      <div className="loading-screen">
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  const navItems = [
    { href: "/teacher/capture", label: "Capture", icon: "📸" },
    { href: "/teacher/uploads", label: "Uploads", icon: "📋" },
    { href: "/teacher/playgroup", label: "Playgroup", icon: "👥" },
  ];

  return (
    <div className="page-content">
      {/* Header */}
      <header className="header">
        <div className="container flex items-center justify-between">
          <div>
            <span className="header-title">moments4u</span>
            <span className="text-sm text-secondary" style={{ marginLeft: 8 }}>
              Teacher
            </span>
          </div>
          <div className="flex items-center gap-md">
            <span className="text-sm text-secondary">{user.full_name}</span>
            <button
              onClick={logout}
              className="btn btn-secondary"
              style={{ padding: "6px 12px", fontSize: "0.8125rem" }}
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container" style={{ paddingTop: "var(--space-lg)" }}>
        {children}
      </main>

      {/* Bottom Nav */}
      <nav className="nav">
        {navItems.map((item) => (
          <button
            key={item.href}
            onClick={() => router.push(item.href)}
            className={`nav-item ${pathname === item.href ? "active" : ""}`}
          >
            <span style={{ fontSize: "1.25rem" }}>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
