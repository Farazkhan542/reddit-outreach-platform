import PortalShell from "@/components/PortalShell";

const links = [
  { href: "/admin", label: "Overview" },
  { href: "/admin/review", label: "Review queue" },
  { href: "/admin/leads", label: "Leads" },
  { href: "/admin/config", label: "Niche config" },
  { href: "/admin/team", label: "Team" },
  { href: "/admin/approval", label: "API approval" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <PortalShell title="Outreach · Admin" links={links}>
      {children}
    </PortalShell>
  );
}
