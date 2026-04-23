import { formatTopicLabel } from "../utils/topic";

function clampPercent(value) {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return 0;
  }

  return Math.max(0, Math.min(100, numericValue));
}

export default function ProgressCard({ masteryPercent, topic, weakPoints = [] }) {
  const percent = clampPercent(masteryPercent);

  return (
    <article className="panel interactive-surface p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Topic Mastery
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-white">
            {formatTopicLabel(topic, { fallback: "Topic", strict: true })}
          </h3>
        </div>

        <span className="rounded-full border border-ocean/12 bg-canvas/80 px-3 py-2 text-sm font-semibold text-slate-100 shadow-soft">
          {Math.round(percent)}%
        </span>
      </div>

      <div className="mt-5 h-3 overflow-hidden rounded-full bg-ink/80">
        <div
          className="h-full origin-left rounded-full bg-gradient-to-r from-sky-400 via-ocean to-cyan-300 shadow-[0_0_10px_rgba(0,150,255,0.3)] transition-all duration-700 ease-out"
          style={{ width: `${percent}%`, animation: "progressReveal 0.8s ease-out" }}
        />
      </div>

      {weakPoints.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {weakPoints.map((weakPoint) => (
            <span
              key={weakPoint}
              className="rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1.5 text-xs font-semibold text-orange-200"
            >
              {weakPoint}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-400">
          No weak points recorded for this topic yet.
        </p>
      )}
    </article>
  );
}
