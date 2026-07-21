"use client";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/**
 * Upload a single file directly to Supabase Storage via a signed PUT URL.
 *
 * Flow:
 *  1. POST /marker/submissions/upload-url  → { signed_url, photo_path }
 *  2. PUT file bytes to signed_url
 *  3. Return photo_path for the caller to persist
 */
export async function uploadFile(file: File): Promise<string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  // 1. Get signed upload URL
  const urlRes = await fetch(`${API}/marker/submissions/upload-url`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      content_type: file.type || "image/jpeg",
      filename: file.name,
    }),
  });

  if (!urlRes.ok) {
    throw new Error(`Failed to get upload URL: ${urlRes.status}`);
  }

  const { signed_url, photo_path } = (await urlRes.json()) as {
    signed_url: string;
    photo_path: string;
  };

  // 2. PUT the file directly to Supabase Storage
  const uploadRes = await fetch(signed_url, {
    method: "PUT",
    headers: { "Content-Type": file.type || "image/jpeg" },
    body: file,
  });

  if (!uploadRes.ok) {
    throw new Error(`Failed to upload file: ${uploadRes.status}`);
  }

  // 3. Return the storage path for the caller to persist
  return photo_path;
}

export function useSignedUpload() {
  return { uploadFile };
}
