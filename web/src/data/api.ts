import { queryOptions } from "@tanstack/react-query";
import type { CaseSummary, DerivedView } from "./types";

/* All URLs are relative: the app and the API are served on one origin. */

export class ApiRejection extends Error {
  constructor(public detail: string) {
    super(detail);
    this.name = "ApiRejection";
  }
}

function unwrap<T>(url: string, body: unknown): T {
  const b = body as { error?: string; detail?: string } | null;
  if (b && typeof b === "object" && typeof b.error === "string") {
    if (b.error === "rejected") throw new ApiRejection(b.detail ?? b.error);
    throw new Error(b.detail ?? `${url}: ${b.error}`);
  }
  return body as T;
}

export interface CaseMeta {
  id: number;
  status: string;
  status_detail: string | null;
  processing: boolean;
  pages_total: number | null;
}

export interface ReviewState {
  key: string;
  state: string;
  note: string | null;
}

export interface Correction {
  entry_id: number;
  field: string;
  value: string;
}

export interface UnreadPage {
  ec_id: number;
  page_num: number;
  reason: string | null;
}

/* What a case cost. Mirrors the dataclasses in app/cost.py.
 *
 * Those carry computed @property values — `ran`, `tokens`, `quantity`,
 * `configured`, `priced` — and a dataclass property does not survive
 * serialisation, so none of them are here. They are recomputed in
 * TabWhatItCost from the same fields the Python computes them from; the rule
 * is that neither side may invent a number the other would not produce. */

export interface RateCard {
  source: string | null;
  retrieved: string | null;
  currency: string;
  per_page: Record<string, number>;
  per_million_tokens: Record<string, Record<string, number>>;
  per_character: Record<string, number>;
}

export interface CostLine {
  stage: string;
  label: string;
  unit: string;
  models: string[];
  calls: number;
  cached_calls: number;
  pages: number;
  tokens_in: number;
  tokens_out: number;
  chars: number;
  ms: number;
  /** null means no rate is configured for this line — never a zero. */
  amount: number | null;
  cached_saving: number | null;
}

export interface CostReport {
  lines: CostLine[];
  total: number | null;
  cached_saving: number | null;
  calls: number;
  cached_calls: number;
  pages: number;
  tokens: number;
  wall_ms: number;
  rates: RateCard;
  /** What the estimate was computed from. Shown, because an estimate that does
      not say what it is based on is a guess wearing a suit. */
  basis: string;
  estimated: boolean;
}

export interface LedgerRow {
  id: number;
  stage: string | null;
  model: string | null;
  ladder_rung: string | null;
  pages: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  chars: number | null;
  cached: number | null;
  ms: number | null;
}

export interface CostPayload {
  estimate: CostReport;
  actual: CostReport;
  ledger: LedgerRow[];
}

export interface CaseResponse {
  case: CaseMeta;
  view: DerivedView;
  reviews: ReviewState[];
  review_by_key: Record<string, ReviewState>;
  corrections: Correction[];
  unread: UnreadPage[];
  graph: unknown;
  cost: CostPayload;
}

export interface StatusResponse {
  id: number;
  status: string;
  status_detail: string | null;
  processing: boolean;
  pages_total: number | null;
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`${url} responded ${res.status}`);
  return unwrap<T>(url, await res.json());
}

async function post<T>(url: string, body?: BodyInit, json?: unknown): Promise<T> {
  const init: RequestInit = { method: "POST" };
  if (json === undefined) {
    if (body !== undefined) init.body = body;
  } else {
    init.body = JSON.stringify(json);
    init.headers = { "Content-Type": "application/json" };
  }
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${url} responded ${res.status}`);
  return unwrap<T>(url, await res.json());
}

/* Reads */

export const casesQuery = () =>
  queryOptions({
    queryKey: ["cases"],
    queryFn: () => get<{ cases: CaseSummary[] }>("/api/cases").then((r) => r.cases),
  });

export interface SampleOption {
  key: string;
  label: string;
}

export const samplesQuery = () =>
  queryOptions({
    queryKey: ["samples"],
    queryFn: () => get<{ samples: SampleOption[] }>("/api/samples").then((r) => r.samples),
  });

export const caseQuery = (caseId: string) =>
  queryOptions({
    queryKey: ["case", caseId],
    queryFn: () => get<CaseResponse>(`/api/case/${encodeURIComponent(caseId)}`),
  });

export const caseStatusQuery = (caseId: string) =>
  queryOptions({
    queryKey: ["case-status", caseId],
    queryFn: () => get<StatusResponse>(`/api/case/${encodeURIComponent(caseId)}/status`),
    refetchInterval: 2000,
  });

/* Writes */

export function uploadCertificate(file: File) {
  const form = new FormData();
  form.append("file", file);
  return post<{ case_id: number }>("/api/upload", form);
}

export function startSample(key: string) {
  return post<{ case_id: number }>(`/api/sample/${encodeURIComponent(key)}`);
}

/* The certificate that closes a gap joins THIS case rather than starting a new
   one. `requestKey` records which gap it was answering, so afterwards the case
   can say what this document settled. */
export function addDocument(input: { caseId: string; file: File; requestKey?: string }) {
  const form = new FormData();
  form.append("file", input.file);
  form.append("request_key", input.requestKey ?? "");
  return post<{ case_id: number }>(
    `/api/case/${encodeURIComponent(input.caseId)}/documents`,
    form,
  );
}

export function saveReview(input: {
  case_id: number;
  key: string;
  state: string;
  note?: string | null;
}) {
  return post<{ ok: boolean }>("/api/review", undefined, input);
}

/* Returns the case id because an entry knows which case it belongs to and the
   caller should not have to — and the caller has to re-read the case anyway: a
   correction moves the meters and the checklist, not just the cell. */
export function saveCorrection(input: { entry_id: number; field: string; value: string }) {
  return post<{ ok: boolean; case_id: number }>("/api/correct", undefined, input);
}

/* Images are plain URLs, not JSON. */

export const pageImageUrl = (ecId: number, pageNum: number) => `/page/${ecId}/${pageNum}.png`;
export const cropImageUrl = (entryId: number) => `/crop/${entryId}.png`;
