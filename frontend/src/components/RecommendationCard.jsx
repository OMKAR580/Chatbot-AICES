import { formatTopicLabel } from "../utils/topic";

export default function RecommendationCard({ index, onSelect, topic }) {
  return (
    <article className="interactive-surface group rounded-[20px] border border-ocean/12 bg-canvas/68 p-4 shadow-soft">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[16px] border border-ocean/15 bg-mist/80 text-sm font-semibold text-ocean transition-all duration-300 group-hover:bg-ocean group-hover:text-ink">
          {index + 1}
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
            Next Topic
          </p>
          <h4 className="mt-1 text-lg font-semibold leading-6 text-white">
            {formatTopicLabel(topic, { fallback: "Topic" })}
          </h4>

          {onSelect ? (
            <button
              className="neon-button mt-4 rounded-full border border-ocean/20 bg-ocean/10 px-4 py-2 text-sm font-semibold text-ocean hover:bg-ocean hover:text-ink"
              onClick={() => onSelect(topic)}
              type="button"
            >
              Practice in chat
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
