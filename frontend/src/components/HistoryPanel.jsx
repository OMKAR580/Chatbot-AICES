import { formatTopicLabel } from "../utils/topic";

function formatDate(value) {
  if (!value) {
    return "Recent";
  }

  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}

export default function HistoryPanel({ activeTopic, history, isLoading, onSelect }) {
  return (
    <section className="panel p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
            Recent Chats
          </p>
          <h3 className="mt-1 text-lg font-semibold text-white">Pick up where you left off</h3>
        </div>

        {isLoading ? (
          <span className="rounded-full border border-ocean/15 bg-mist/80 px-3 py-1.5 text-xs font-semibold text-slate-300">
            Loading
          </span>
        ) : null}
      </div>

      {history.length ? (
        <div className="chat-scrollbar mt-4 max-h-[360px] space-y-2 overflow-y-auto pr-1">
          {history.map((item, index) => {
            const isActive = activeTopic?.toLowerCase() === item.topic?.toLowerCase();

            return (
              <button
                key={`${item.created_at}-${index}`}
                className={[
                  "sidebar-item w-full rounded-[20px] border px-4 py-3.5 text-left",
                  isActive
                    ? "sidebar-item-active border-ocean/42 bg-ocean/14 text-ocean"
                    : "border-ocean/10 bg-canvas/60 text-slate-300",
                ].join(" ")}
                onClick={() => onSelect(item)}
                type="button"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold">
                    {formatTopicLabel(item.topic, { fallback: "Topic", strict: true })}
                  </span>
                  <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400">
                    {item.language}
                  </span>
                </div>
                <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">
                  {item.user_message}
                </p>
                <p className="mt-2 text-[11px] font-medium text-slate-500">
                  {formatDate(item.created_at)}
                </p>
              </button>
            );
          })}
        </div>
      ) : (
        <p className="mt-4 rounded-[22px] border border-ocean/10 bg-canvas/65 px-4 py-4 text-sm leading-6 text-slate-400">
          No saved chats yet. Ask one concept and your recent tutor sessions will appear here.
        </p>
      )}
    </section>
  );
}
