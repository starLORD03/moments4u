/**
 * API client — typed fetch wrapper for the moments4u backend.
 *
 * Handles JWT token management, automatic refresh, and error handling.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (token) {
    localStorage.setItem("access_token", token);
  } else {
    localStorage.removeItem("access_token");
  }
}

export function getAccessToken(): string | null {
  if (accessToken) return accessToken;
  if (typeof window !== "undefined") {
    accessToken = localStorage.getItem("access_token");
  }
  return accessToken;
}

async function refreshToken(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) return null;
    const data = await res.json();
    setAccessToken(data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // --- MOCK MODE FOR UI PREVIEW (Backend is offline) ---
  console.log("Mock API Intercept:", path);
  await new Promise((r) => setTimeout(r, 500)); // Simulate latency
  
  if (path.includes("/auth/refresh")) return null as any;
  
  if (path.includes("/auth/me")) {
    const t = getAccessToken();
    if (!t) throw new ApiError(401, "No token");
    const role = t.startsWith("teacher") ? "teacher" : "parent";
    return { id: "u123", email: "tester@mock.com", full_name: "Demo " + role, role, playgroup_id: "pg123" } as any;
  }
  if (path.includes("/auth/login") || path.includes("/auth/register")) {
    const bd = options.body ? JSON.parse(options.body as string) : { role: "parent", email: "test@mock.com" };
    const role = bd.role || "parent";
    return { access_token: `${role}_fake_token`, user: { id: "u1", email: bd.email, full_name: bd.full_name || "Demo " + role, role, playgroup_id: "pg123" } } as any;
  }
  if (path.includes("/auth/logout")) {
    return {} as any;
  }
  if (path.includes("/gallery/my-children")) {
    return { children: [{ id: "c1", full_name: "Mock Child", date_of_birth: "2020-01-01" }] } as any;
  }
  if (path.includes("/playgroups/pg123/children")) {
    return { children: [{ id: "c1", full_name: "Mock Child" }, { id: "c2", full_name: "Emma S." }] } as any;
  }
  if (path.includes("/playgroups/pg123")) {
    return { id: "pg123", name: "Sunshine Playgroup", description: "UI Demo Mock Data" } as any;
  }
  if (path.includes("/photos/my-uploads")) {
    return { photos: [], pagination: { page: 1, limit: 20, total: 0, total_pages: 1 } } as any;
  }
  if (path.includes("/gallery/children/")) {
    return { child: { id: "c1", full_name: "Mock Child" }, timeline: [], pagination: { page: 1, limit: 20, total: 0, total_pages: 1 } } as any;
  }
  if (path.includes("/faces/register-child")) {
    return { matched_photos_count: 3 } as any;
  }
  if (path.includes("/photos/upload")) {
    return { uploaded: [{ id: "p1", status: "processing", thumbnail_url: null }], failed: [] } as any;
  }
  
  throw new ApiError(404, "Mock route not found: " + path);
}

// ── Typed API methods ──

export const api = {
  auth: {
    register: (data: {
      email: string;
      password: string;
      full_name: string;
      role: string;
      playgroup_id?: string;
    }) =>
      apiFetch("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    login: (email: string, password: string) =>
      apiFetch("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),

    logout: () =>
      apiFetch("/api/v1/auth/logout", { method: "POST" }),

    me: () => apiFetch("/api/v1/auth/me"),
  },

  photos: {
    upload: (playgroup_id: string, files: File[]) => {
      const formData = new FormData();
      formData.append("playgroup_id", playgroup_id);
      files.forEach((f) => formData.append("files", f));
      return apiFetch("/api/v1/photos/upload", {
        method: "POST",
        body: formData,
      });
    },

    myUploads: (page = 1, limit = 20, date?: string) => {
      const params = new URLSearchParams({ page: String(page), limit: String(limit) });
      if (date) params.set("date", date);
      return apiFetch(`/api/v1/photos/my-uploads?${params}`);
    },

    delete: (photoId: string) =>
      apiFetch(`/api/v1/photos/${photoId}`, { method: "DELETE" }),
  },

  gallery: {
    childPhotos: (
      childId: string,
      page = 1,
      limit = 20,
      dateFrom?: string,
      dateTo?: string
    ) => {
      const params = new URLSearchParams({ page: String(page), limit: String(limit) });
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      return apiFetch(`/api/v1/gallery/children/${childId}?${params}`);
    },

    myChildren: () => apiFetch("/api/v1/gallery/my-children"),
  },

  faces: {
    registerChild: (childId: string, photo: File) => {
      const formData = new FormData();
      formData.append("child_id", childId);
      formData.append("photo", photo);
      return apiFetch("/api/v1/faces/register-child", {
        method: "POST",
        body: formData,
      });
    },

    unmatched: (playgroupId: string, page = 1) =>
      apiFetch(`/api/v1/faces/unmatched?playgroup_id=${playgroupId}&page=${page}`),

    assign: (faceId: string, childId: string) =>
      apiFetch(`/api/v1/faces/${faceId}/assign`, {
        method: "POST",
        body: JSON.stringify({ child_id: childId }),
      }),
  },

  playgroups: {
    get: (id: string) => apiFetch(`/api/v1/playgroups/${id}`),
    children: (id: string) => apiFetch(`/api/v1/playgroups/${id}/children`),
    members: (id: string) => apiFetch(`/api/v1/playgroups/${id}/members`),
  },
};
