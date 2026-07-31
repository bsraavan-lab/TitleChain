export function Loading({ what }: { what: string }) {
  return (
    <p className="loadline" role="status">
      Reading {what}…
    </p>
  );
}

export function LoadError({
  what,
  error,
  onRetry,
}: {
  what: string;
  error: unknown;
  onRetry: () => void;
}) {
  const detail = error instanceof Error ? error.message : String(error);
  return (
    <div className="loaderr" role="alert">
      <p className="loadline">
        {what} could not be loaded. Nothing was lost — no document, finding or case was changed.
      </p>
      <p className="row-reason mono">{detail}</p>
      <p>
        <button type="button" className="quiet-link" onClick={onRetry}>
          Try again
        </button>
      </p>
    </div>
  );
}
