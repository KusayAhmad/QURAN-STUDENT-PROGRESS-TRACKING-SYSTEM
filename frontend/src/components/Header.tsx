"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { LangSwitcher } from "@/components/LangSwitcher";
import { NotificationBell } from "@/components/NotificationBell";
import { useT } from "@/lib/useT";
import { useAuthStore } from "@/store/auth";

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const t = useT();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);

  const NAV: { href: string; labelKey: Parameters<typeof t>[0]; adminOnly?: boolean }[] = [
    { href: "/dashboard", labelKey: "nav.dashboard" },
    { href: "/students", labelKey: "nav.students" },
    { href: "/matrix", labelKey: "nav.matrix" },
    { href: "/classes", labelKey: "nav.classes" },
    { href: "/admin/users", labelKey: "nav.users", adminOnly: true },
    { href: "/admin/audit-logs", labelKey: "nav.auditLogs", adminOnly: true },
    { href: "/admin/import", labelKey: "nav.import", adminOnly: true },
  ];

  const handleLogout = () => {
    clear();
    router.replace("/login");
  };

  return (
    <header className="qp-header">
      <div className="qp-header-inner">
        <Link href="/dashboard" className="qp-brand">
          {t("app.title")}
        </Link>
        <nav className="qp-nav">
          {NAV.filter((n) => !n.adminOnly || user?.role === "ADMIN").map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={active ? "qp-nav-link active" : "qp-nav-link"}
              >
                {t(item.labelKey)}
              </Link>
            );
          })}
        </nav>
        <div className="qp-user">
          {user ? (
            <>
              <NotificationBell />
              <LangSwitcher />
              <span className="qp-user-name">
                {user.name} <span className="qp-role">{user.role}</span>
              </span>
              <button className="qp-btn-ghost" onClick={handleLogout}>
                {t("nav.logout")}
              </button>
            </>
          ) : (
            <LangSwitcher />
          )}
        </div>
      </div>
    </header>
  );
}
