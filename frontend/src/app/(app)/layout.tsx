import type { ReactNode } from "react";

import { AuthGuard } from "@/components/AuthGuard";
import { Header } from "@/components/Header";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <div className="qp-shell">
        <Header />
        <main className="qp-main">{children}</main>
      </div>
    </AuthGuard>
  );
}
