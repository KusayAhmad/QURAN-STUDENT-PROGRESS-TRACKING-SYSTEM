"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { useAuthStore } from "@/store/auth";

/**
 * Client-side route guard. If there is no access token in the auth store,
 * push the user to /login. Renders nothing during the redirect to avoid a
 * flash of authenticated-only content.
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!accessToken) {
      router.replace("/login");
    }
  }, [accessToken, router]);

  if (!accessToken) return null;
  return <>{children}</>;
}
