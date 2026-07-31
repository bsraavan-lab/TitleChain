import { Link } from "@tanstack/react-router";

export function SiteNav({ caseId = "1" }: { caseId?: string }) {
  return (
    <nav className="sitenav" aria-label="Screens">
      <Link to="/" className="sitenav-link" activeProps={{ className: "sitenav-link is-on" }}>
        Home
      </Link>
      <Link
        to="/case/$caseId"
        params={{ caseId }}
        className="sitenav-link"
        activeProps={{ className: "sitenav-link is-on" }}
      >
        Case
      </Link>
      <Link
        to="/case/$caseId/working"
        params={{ caseId }}
        className="sitenav-link"
        activeProps={{ className: "sitenav-link is-on" }}
      >
        Working
      </Link>
      <Link
        to="/case/$caseId/refusal"
        params={{ caseId }}
        className="sitenav-link"
        activeProps={{ className: "sitenav-link is-on" }}
      >
        Refusal
      </Link>
      <Link
        to="/report/$caseId"
        params={{ caseId }}
        className="sitenav-link"
        activeProps={{ className: "sitenav-link is-on" }}
      >
        Report
      </Link>
      <Link to="/system" className="sitenav-link" activeProps={{ className: "sitenav-link is-on" }}>
        System
      </Link>
    </nav>
  );
}
