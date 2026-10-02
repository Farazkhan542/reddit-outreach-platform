import PortalShell from "@/components/PortalShell";

const links = [
  { href: "/member", label: "My review queue" },
  { href: "/member/leads", label: "Leads" },
];

export default function MemberLayout({ children }: { children: React.ReactNode }) {
  return (
    <PortalShell title="Outreach" links={links}>
      {children}
    </PortalShell>
  );
}
