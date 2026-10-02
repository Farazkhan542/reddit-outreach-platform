"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { clearToken } from "@/lib/api";

export default function PortalShell({
  title,
  links,
  children,
}: {
  title: string;
  links: { href: string; label: string }[];
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="shell">
      <nav className="sidebar">
        <h1>{title}</h1>
        {links.map((l) => (
          <Link key={l.href} href={l.href} className={pathname === l.href ? "active" : ""}>
            {l.label}
          </Link>
        ))}
        <div className="spacer" />
        <button
          onClick={() => {
            clearToken();
            router.push("/login");
          }}
        >
          Sign out
        </button>
      </nav>
      <main>{children}</main>
    </div>
  );
}
