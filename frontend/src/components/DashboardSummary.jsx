function label(value) {
  if (!value) {
    return "Beginner";
  }

  return value.charAt(0).toUpperCase() + value.slice(1);
}

function averageScore(scores) {
  if (!scores?.length) {
    return 0;
  }

  return Math.round(scores.reduce((total, score) => total + score, 0) / scores.length);
}

export default function DashboardSummary({
  currentLevel,
  preferredLanguage,
  recentScores,
  topicCount,
  weakTopicCount,
}) {
  const avgScore = averageScore(recentScores);

  const cards = [
    {
      label: "Learner Level",
      value: label(currentLevel),
      detail: "Updates after quiz evaluation",
      tone: "from-ocean to-sky-400",
    },
    {
      label: "Language",
      value: preferredLanguage || "Hinglish",
      detail: "Used for explanations and quizzes",
      tone: "from-ember to-orange-300",
    },
    {
      label: "Avg Recent Score",
      value: recentScores?.length ? `${avgScore}%` : "No quiz yet",
      detail: `${recentScores?.length || 0} recent attempts tracked`,
      tone: "from-moss to-emerald-300",
    },
    {
      label: "Focus Areas",
      value: `${weakTopicCount || 0}`,
      detail: `${topicCount || 0} topics with progress data`,
      tone: "from-ink to-slate-500",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <article
          key={card.label}
          className="interactive-surface overflow-hidden rounded-[20px] border border-ocean/12 bg-canvas/68 shadow-soft"
        >
          <div className={`h-2 bg-gradient-to-r ${card.tone}`} />
          <div className="bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01))] p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              {card.label}
            </p>
            <p className="mt-3 text-2xl font-semibold text-white">{card.value}</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">{card.detail}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
