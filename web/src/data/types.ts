export type Outcome = "FAIL" | "REVIEW" | "NOT_EVALUABLE" | "PASS" | "NOT_APPLICABLE";

export interface RuleInput {
  label: string;
  value: string | null;
  source_entry_id: number | null;
}

export interface PageRef {
  ec_id: number;
  page_num: number;
}

export interface RuleRun {
  rule_id: string;
  key: string;
  outcome: Outcome;
  title: string;
  message: string;
  reason: string | null;
  severity: "blocking" | "material" | "advisory" | null;
  inputs: RuleInput[];
  evidence_entry_ids: number[];
  pages: PageRef[];
  implemented: boolean;
  rulebook_version: string;
}

export interface Tick {
  year: number;
  label: string;
  inside: boolean;
}

/* One certificate's own window on the shared ruler.
 *
 * These were `from_year` / `to_year` here and `start_year` / `end_year` in
 * `CoverageBand` (app/models.py), so every band read `undefined`, every
 * position computed to NaN, and the browser dropped `left: NaN%` — the bands
 * have never drawn. The names now match the wire, and the years are optional
 * because a certificate with an unreadable search period has neither. */
export interface Band {
  label: string;
  start_year: number | null;
  end_year: number | null;
  ec_id: number | null;
}

export interface Coverage {
  /* Optional on the Python side, and genuinely absent on a certificate whose
     search period is blank — the `- - -` case R7 exists to catch. */
  start_year: number | null;
  end_year: number | null;
  axis_min: number;
  axis_max: number;
  ticks: Tick[];
  bands: Band[];
  /** null = not evaluable, which is not the same as false. */
  sufficient: boolean | null;
  headline: string;
  detail: string;
  required_from: number | null;
  required_to: number | null;
}

/* The chain drawing. Geometry is computed by app/layout.py — x is the year,
 * y is a greedy lane — and arrives here as numbers; this side only draws.
 *
 * What is NOT on the wire, because Pydantic does not serialise @property:
 * `GraphNode.label`, `GraphNode.title` and `GraphEdge.path`. The first two are
 * plain reads off `doc_no`; the path is recomputed in ChainGraph from the four
 * endpoints. Same trap the cost types carry a note about in data/api.ts. */
export type NodeShape = "square" | "diamond" | "bar" | "slash" | "ring" | "circle";

export interface GraphNode {
  doc_no: string;
  year: number | null;
  nature: string | null;
  kind: string | null;
  shape: NodeShape;
  entry_id: number | null;
  ec_id: number | null;
  ec_label: string | null;
  x: number;
  y: number;
  examined: boolean;
  cancelled: boolean;
  corrected: boolean;
  open_encumbrance: boolean;
}

export interface GraphEdge {
  kind: string;
  resolved: boolean;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface YearTick {
  year: number;
  x: number;
}

export interface GraphLayout {
  width: number;
  height: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  ticks: YearTick[];
  undated: string[];
}

export interface Completeness {
  links_named: number;
  links_examined: number;
  span_from: number;
  span_to: number;
  years_required: number;
  years_covered: number;
  review_total: number;
  review_done: number;
  corrections: number;
  unread_pages: number;
  documents: number;
  requests_open: number;
}

export interface Gate {
  id: string;
  label: string;
  passed: boolean;
  tab: string;
}

export interface Party {
  name_native: string;
  role_marker: string | null;
  name_roman: string | null;
}

export interface PRNumber {
  doc_no: string;
  year: number;
}

export interface Entry {
  sr_no: number;
  doc_no: string | null;
  doc_year: number | null;
  date_execution: string | null;
  date_presentation: string | null;
  date_registration: string | null;
  nature: string | null;
  executants: Party[];
  claimants: Party[];
  volume_page: string | null;
  consideration_value: string | null;
  market_value: string | null;
  pr_numbers: PRNumber[];
  remarks: string | null;
  db_id: number | null;
}

export interface ECHeader {
  sro: string | null;
  village: string | null;
  survey_details: string[];
  search_period_start: string | null;
  search_period_end: string | null;
  issue_date: string | null;
  declared_entry_count: number | null;
}

export interface ECDoc {
  ec_id: number;
  label: string;
  filename: string;
  header: ECHeader;
  entries: Entry[];
  page_count: number;
  fulfils_request_key: string | null;
}

export interface Edge {
  from_entry_id: number | null;
  to_doc_no: string;
  to_year: number | null;
  edge_type: "PR_PARENT" | "CANCELS" | "SUCCESSION";
  resolved_entry_id: number | null;
  label: string | null;
}

export interface ChainNode {
  doc_no: string;
  year: number | null;
  nature: string | null;
  entry_id: number | null;
  cancelled_by: string | null;
  children: ChainNode[];
}

export interface DocRequest {
  key: string;
  kind: string;
  because: string;
  closes: string[];
  sro: string | null;
  village: string | null;
  survey_nos: string[];
  date_from: string | null;
  date_to: string | null;
  doc_no: string | null;
  superseded_by: string | null;
  alternative: string | null;
}

export interface DerivedView {
  coverage: Coverage;
  completeness: Completeness;
  readiness: { gates: Gate[] };
  runs: RuleRun[];
  edges: Edge[];
  chain: ChainNode[];
  docs: ECDoc[];
  requests: DocRequest[];
  rulebook_version: string;
  order: {
    sro: string | null;
    village: string | null;
    survey_nos: string[];
    date_from: string | null;
    date_to: string | null;
  };
}

export const OUTCOME_GLYPH: Record<Outcome, string> = {
  FAIL: "▲",
  REVIEW: "⚑",
  NOT_EVALUABLE: "○",
  PASS: "✓",
  NOT_APPLICABLE: "⊘",
};

export const OUTCOME_TONE: Record<Outcome, string> = {
  FAIL: "seal",
  REVIEW: "stamp",
  NOT_EVALUABLE: "stamp",
  PASS: "fee",
  NOT_APPLICABLE: "muted",
};

export const OUTCOME_WORD: Record<Outcome, string> = {
  FAIL: "Failed",
  REVIEW: "To review",
  NOT_EVALUABLE: "Couldn't check",
  PASS: "Passed",
  NOT_APPLICABLE: "Not applicable",
};

export interface CaseSummary {
  id: number;
  property_key: string | null;
  status: string;
  status_detail: string | null;
  processing: boolean;
  header: ECHeader | null;
  coverage: Coverage | null;
  open_count: number | null;
}
