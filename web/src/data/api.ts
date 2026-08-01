import { queryOptions } from "@tanstack/react-query";
import type { CaseSummary, DerivedView, GraphLayout } from "./types";

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

/* These three mirror database rows, so they carry the column names — not the
 * shape of the request that wrote them. All three were declared here as
 * something tidier than what the server actually sends (`key` for
 * `finding_key`, `value` for `old_value`/`new_value`, `page_num` for
 * `page_from`/`page_to`), and `reviews` was declared an array when it is an
 * object keyed by finding. None of it broke, only because no screen reads
 * them yet — which is precisely how the coverage bands were wrong for as long
 * as they were. A type that has never been checked against the wire is a
 * comment. */

/** One row of the append-only `reviews` table. */
export interface ReviewRow {
  id: number;
  case_id: number;
  finding_key: string;
  state: string;
  note: string | null;
  actor: string | null;
  created_at: string | null;
}

/** One row of the append-only `corrections` table, joined to its entry. */
export interface Correction {
  id: number;
  entry_id: number;
  field: string;
  old_value: string | null;
  new_value: string | null;
  actor: string | null;
  created_at: string | null;
  sr_no: number | null;
  ec_id: number | null;
}

/** A run of pages that came back unreadable. A range, not a single page. */
export interface UnreadPages {
  id: number;
  ec_id: number;
  page_from: number | null;
  page_to: number | null;
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
  /** finding_key → the latest review. An object, not an array. */
  reviews: Record<string, ReviewRow>;
  /** finding_key → every review ever recorded against it, newest first. */
  review_by_key: Record<string, ReviewRow[]>;
  corrections: Correction[];
  unread: UnreadPages[];
  graph: GraphLayout;
  cost: CostPayload;
}

export interface StatusResponse {
  id: number;
  status: string;
  status_detail: string | null;
  processing: boolean;
  pages_total: number | null;
}

/* What the app itself accepts, matching pipeline.accept_upload. Checked here
   too so an oversized file gets the app's own sentence immediately instead of
   being uploaded in full and then refused. */
export const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;

/* A body this app never produced.
 *
 * In production /api is proxied to the Python app by the platform's routing
 * layer, and that layer answers some requests itself — an oversized upload, a
 * cold backend, a gateway timeout — with an HTML error page. Calling .json()
 * on that threw a SyntaxError about an unexpected "<", which is not a sentence
 * anybody can act on. */
function notOurs(url: string, status: number, body: string): Error {
  if (status === 413)
    return new Error(
      "That file was too large for the connection between this page and the " +
        "reader. A lighter scan, or one certificate at a time, should go through.",
    );
  if (status === 502 || status === 503 || status === 504)
    return new Error(
      "The reader did not answer in time. It may still be starting up — " +
        "try again in a moment.",
    );
  const detail = body.trim().startsWith("<") ? "" : ` ${body.slice(0, 200)}`;
  return new Error(`${url} responded ${status}.${detail}`);
}

async function parse<T>(url: string, res: Response): Promise<T> {
  const text = await res.text();
  if (!res.ok) throw notOurs(url, res.status, text);
  try {
    return unwrap<T>(url, JSON.parse(text));
  } catch (e) {
    if (e instanceof ApiRejection || (e instanceof Error && e.name !== "SyntaxError")) throw e;
    throw notOurs(url, res.status, text);
  }
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  return parse<T>(url, res);
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
  return parse<T>(url, res);
}

export type OnProgress = (pctOrNull: number | null) => void;

/* Uploads go through XHR, everything else through fetch.
 *
 * Not a preference: fetch cannot report how much of a request body has been
 * sent, so with fetch the only honest progress indicator is a spinner. On a
 * scanned bundle over a phone connection the difference between "37%" and a
 * spinner is the difference between waiting and reloading the page.
 *
 * `onProgress(null)` means the browser could not measure it — the request is
 * in flight but the total is unknown, which is a different thing from 0%. */
function postFile<T>(url: string, form: FormData, onProgress?: OnProgress): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.responseType = "text";

    if (onProgress) {
      xhr.upload.onprogress = (e) =>
        onProgress(e.lengthComputable ? Math.round((e.loaded / e.total) * 100) : null);
    }

    xhr.onload = () => {
      const text = xhr.responseText ?? "";
      if (xhr.status < 200 || xhr.status >= 300) {
        reject(notOurs(url, xhr.status, text));
        return;
      }
      try {
        resolve(unwrap<T>(url, JSON.parse(text)));
      } catch (e) {
        if (e instanceof ApiRejection || (e instanceof Error && e.name !== "SyntaxError"))
          reject(e);
        else reject(notOurs(url, xhr.status, text));
      }
    };
    xhr.onerror = () =>
      reject(new Error("The certificate did not reach the reader. Check the connection."));
    xhr.onabort = () => reject(new Error("The upload was stopped."));
    xhr.ontimeout = () => reject(new Error("The upload timed out before it finished."));

    xhr.send(form);
  });
}

/** The app's own sentence, before a byte leaves the browser. */
function tooLarge(file: File): ApiRejection | null {
  if (file.size <= MAX_UPLOAD_BYTES) return null;
  return new ApiRejection(
    `That file is ${Math.round(file.size / 1_048_576)} MB, and we can take up to 50 MB. ` +
      `A lighter scan, or one certificate at a time, should go through.`,
  );
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

export function uploadCertificate(file: File, onProgress?: OnProgress) {
  const rejected = tooLarge(file);
  if (rejected) return Promise.reject(rejected);
  const form = new FormData();
  form.append("file", file);
  return postFile<{ case_id: number }>("/api/upload", form, onProgress);
}

export function startSample(key: string) {
  return post<{ case_id: number }>(`/api/sample/${encodeURIComponent(key)}`);
}

/* The certificate that closes a gap joins THIS case rather than starting a new
   one. `requestKey` records which gap it was answering, so afterwards the case
   can say what this document settled. */
export function addDocument(input: {
  caseId: string;
  file: File;
  requestKey?: string;
  onProgress?: OnProgress;
}) {
  const rejected = tooLarge(input.file);
  if (rejected) return Promise.reject(rejected);
  const form = new FormData();
  form.append("file", input.file);
  form.append("request_key", input.requestKey ?? "");
  return postFile<{ case_id: number }>(
    `/api/case/${encodeURIComponent(input.caseId)}/documents`,
    form,
    input.onProgress,
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
