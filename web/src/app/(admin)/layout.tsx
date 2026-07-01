"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStudent } from "@/lib/auth";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const student = useStudent();

  useEffect(() => {
    if (student && !student.is_admin) {
      router.replace("/dashboard");
    }
  }, [student, router]);

  // While loading (student is null) or if admin, render children
  if (student === null) {
    return null; // loading state — prevents flash of content
  }

  if (!student.is_admin) {
    return null; // redirect in progress
  }

  return <div className="mx-auto max-w-5xl px-4 py-6">{children}</div>;
}
