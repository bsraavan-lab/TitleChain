import { queryOptions } from "@tanstack/react-query";
import type { CaseSummary, DerivedView } from "./types";

/* All URLs are relative: the app and the API are served on one origin. */

export class ApiRejection extends Error {
  constructor(public detail: string) {
    super(detail);
    this.name = "ApiRejection";
  }
}

/* The backend answers a refusal with HTTP 200 and a reason in the body, because
   the reason is a sentence to render where the file was dropped rather than a
   status code the client has to translate back into one. Unwrapping it here —
   not at each call site — is what stops a refusal being mistaken for a success
   and navigating to /case/undefined. */
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

export interface CaseResponse {
  case: CaseMeta;
  view: DerivedView;
  reviews: ReviewState[];
  review_by_key: Record<string, ReviewState>;
  corrections: Correction[];
  unread: UnreadPage[];
  graph: unknown;
  cost: unknown;
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

/* One request per case. Every tab is a view of one derivation; fetching per tab
   would let the checklist and the chain disagree about one certificate. */
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

export function saveReview(input: {
  case_id: number;
  key: string;
  state: string;
  note?: string | null;
}) {
  return post<{ ok: boolean }>("/api/review", undefined, input);
}

export function saveCorrection(input: { entry_id: number; field: string; value: string }) {
  return post<{ ok: boolean; case_id: number }>("/api/correct", undefined, input);
}

/* Images are plain URLs, not JSON. Provenance does not need an envelope. */

export const pageImageUrl = (ecId: number, pageNum: number) => `/page/${ecId}/${pageNum}.png`;
export const cropImageUrl = (entryId: number) => `/crop/${entryId}.png`;
