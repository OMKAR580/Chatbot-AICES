const actions = [
  { key: "short", label: "Short" },
  { key: "detailed", label: "Detailed" },
  { key: "notes", label: "Notes" },
  { key: "code", label: "With Code" },
  { key: "interview", label: "Interview" },
  { key: "quiz", label: "Quiz Me" },
];
const quizCountOptions = [3, 5, 10, 15];

export default function ActionButtons({
  disabled,
  onAction,
  quizCount,
  onQuizCountChange,
}) {
  return (
    <div className="space-y-3">
      <label className="flex max-w-[220px] items-center gap-3 rounded-[18px] border border-ocean/14 bg-canvas/72 px-4 py-3 text-sm text-slate-300 shadow-soft">
        <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
          Select Questions
        </span>
        <select
          className="ml-auto rounded-full border border-ocean/16 bg-ink/80 px-3 py-1.5 text-sm font-semibold text-white outline-none transition-all duration-300 ease-out focus:border-ocean/40 focus:shadow-[0_0_10px_rgba(0,150,255,0.2)]"
          disabled={disabled}
          onChange={(event) => onQuizCountChange(Number(event.target.value))}
          value={quizCount}
        >
          {quizCountOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <div className="flex flex-wrap gap-2">
        {actions.map((action) => (
          <button
            key={action.key}
            className="neon-button rounded-full border border-ocean/18 bg-mist/72 px-4 py-2.5 text-sm font-medium text-slate-100 disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0"
            disabled={disabled}
            onClick={() => onAction(action.key)}
            type="button"
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}
