import LeadsTable from "@/components/LeadsTable";

export default function MemberLeadsPage() {
  return (
    <>
      <h2>Leads</h2>
      <p className="muted">Your assigned leads, plus unclaimed qualified leads you can claim.</p>
      <LeadsTable canClaim />
    </>
  );
}
