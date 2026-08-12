import { useEffect, useRef, useState } from "react";
import {
  explainAudioUrl,
  fetchExplanation,
  type Explanation,
  type ExplainTarget,
} from "../../data/api";
import { useRail } from "./rail";

/* Point at a thing, hear what it means.
 *
 * The words are never audio alone: the script renders the moment it arrives,
 * and the voice reads exactly that text — the backend rebuilds both from one
 * derivation, so they cannot disagree. While an entry is being spoken, the
 * rail pins that entry's crop: the voice and the page point at the same cell.
 *
 * The Audio element is created inside the click's own call stack and reused
 * for every play after it. That is deliberate: Safari unlocks playback per
 * element per gesture, and an element created after an `await` never unlocks. */

type Phase = "idle" | "fetching" | "speaking" | "error";
type Lang = "en" | "ta";

const VOICE_DOWN =
  "The voice did not answer. The words above still stand — try the sound again in a moment.";

export function ExplainControl({
  target,
  label = "Explain aloud",
}: {
  target: ExplainTarget;
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  const [lang, setLang] = useState<Lang>("en");
  const [phase, setPhase] = useState<Phase>("idle");
  const [script, setScript] = useState<Explanation | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rail = useRail();

  // A voice that outlives its card would keep talking over the next tab.
  useEffect(
    () => () => {
      audioRef.current?.pause();
    },
    [],
  );

  const stop = () => {
    audioRef.current?.pause();
    setPhase("idle");
  };

  async function speakIn(nextLang: Lang) {
    audioRef.current ??= new Audio();
    const audio = audioRef.current;
    audio.pause();
    setOpen(true);
    setLang(nextLang);
    setPhase("fetching");
    setProblem(null);
    // Which step failed decides the sentence: a dead voice still leaves the
    // words on screen; a failed fetch has nothing to leave.
    let fetched: Explanation | null = null;
    try {
      fetched = await fetchExplanation(target, nextLang);
      setScript(fetched);
      audio.src = explainAudioUrl(fetched);
      audio.onended = () => setPhase("idle");
      audio.onerror = () => {
        setPhase("error");
        setProblem(VOICE_DOWN);
      };
      await audio.play();
      setPhase("speaking");
      if ("entryId" in target) {
        rail.show({ kind: "entry", entryId: target.entryId, close: true });
      }
    } catch (e) {
      setPhase("error");
      setProblem(fetched ? VOICE_DOWN : e instanceof Error ? e.message : String(e));
    }
  }

  if (!open) {
    return (
      <button className="link" type="button" onClick={() => void speakIn(lang)}>
        {label}
      </button>
    );
  }

  return (
    <div className="explain" role="region" aria-label="Explained in plain words">
      <div className="explain-head">
        <p className="kicker">Said plainly</p>
        <div className="seg" role="group" aria-label="Language">
          <button
            type="button"
            className={`seg-btn${lang === "en" ? " seg-on" : ""}`}
            aria-pressed={lang === "en"}
            onClick={() => void speakIn("en")}
          >
            English
          </button>
          <button
            type="button"
            className={`seg-btn${lang === "ta" ? " seg-on" : ""}`}
            aria-pressed={lang === "ta"}
            onClick={() => void speakIn("ta")}
          >
            தமிழ்
          </button>
        </div>
        <button
          type="button"
          className="link"
          onClick={() => {
            stop();
            setOpen(false);
          }}
        >
          ✕ Close
        </button>
      </div>

      {script ? (
        <p
          className={`explain-text${script.lang === "ta" ? " tamil" : ""}`}
          lang={script.lang === "ta" ? "ta" : "en"}
        >
          {script.text}
        </p>
      ) : null}

      {phase === "fetching" ? <p className="meta">Preparing the voice…</p> : null}
      {phase === "error" && problem ? <p className="explain-problem">{problem}</p> : null}

      <div className="explain-actions">
        {phase === "speaking" ? (
          <button className="btn btn--ghost" type="button" onClick={stop}>
            ◼ Stop
          </button>
        ) : (
          <button
            className="btn btn--ghost"
            type="button"
            disabled={phase === "fetching"}
            onClick={() => void speakIn(lang)}
          >
            {phase === "fetching" ? "Preparing…" : "▶ Play again"}
          </button>
        )}
      </div>
    </div>
  );
}
