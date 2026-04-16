"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

/**
 * Root page — redirects based on user role:
 * - Not logged in → /login
 * - Teacher → /teacher/capture
 * - Parent → /parent/gallery
 * - Admin → /teacher/capture (same as teacher + admin features)
 */
export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!user) {
      router.replace("/login");
      return;
    }

    switch (user.role) {
      case "teacher":
      case "admin":
        router.replace("/teacher/capture");
        break;
      case "parent":
        router.replace("/parent/gallery");
        break;
      default:
        router.replace("/login");
    }
  }, [user, isLoading, router]);

  return (
    <div className="loading-screen">
      <div className="spinner spinner-lg" />
      <p className="text-secondary">Loading moments4u...</p>
    </div>
  );
}
