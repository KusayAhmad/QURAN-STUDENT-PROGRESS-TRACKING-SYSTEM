"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuthStore } from "@/store/auth";

const NAV: { href: string; label: string }[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/students", label: "Students" },
];

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);

  const handleLogout = () => {
    clear();
    router.replace("/login");
  };

  return (
    <header className="qp-header">
      <div className="qp-header-inner">
        <Link href="/dashboard" className="qp-brand">
          Quran Progress
        </Link>
        <nav className="qp-nav">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={active ? "qp-nav-link active" : "qp-nav-link"}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="qp-user">
          {user ? (
            <>
              <span className="qp-user-name">
                {user.name} <span className="qp-role">{user.role}</span>
              </span>
              <button className="qp-btn-ghost" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
