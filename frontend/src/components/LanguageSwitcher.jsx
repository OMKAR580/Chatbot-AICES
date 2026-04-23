const languages = ["English", "Hindi", "Hinglish"];

export default function LanguageSwitcher({ disabled, isUpdating, onChange, value }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
            Language
          </p>
          <p className="mt-1 text-sm text-slate-300">
            Tutor replies and quizzes will follow this preference.
          </p>
        </div>

        {isUpdating ? (
          <span className="rounded-full border border-ocean/15 bg-ocean/10 px-3 py-1.5 text-xs font-semibold text-ocean">
            Saving
          </span>
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        {languages.map((language) => {
          const isActive = value === language;

          return (
            <button
              key={language}
              className={[
                "neon-button rounded-[18px] px-3 py-2.5 text-sm font-semibold",
                isActive
                  ? "border border-ocean/30 bg-ocean text-ink"
                  : "border border-ocean/12 bg-canvas/70 text-slate-300 hover:text-white",
              ].join(" ")}
              disabled={disabled || isUpdating || isActive}
              onClick={() => onChange(language)}
              type="button"
            >
              {language}
            </button>
          );
        })}
      </div>
    </div>
  );
}
