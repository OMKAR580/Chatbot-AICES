import { formatTopicLabel } from "../utils/topic";

function label(value) {
  return formatTopicLabel(value, { fallback: "None" });
}

function scoreTone(score) {
  if (score > 70) {
    return "text-emerald-200 bg-emerald-500/10 border-emerald-400/20";
  }

  if (score >= 40) {
    return "text-ocean bg-ocean/10 border-ocean/20";
  }

  return "text-orange-200 bg-orange-500/10 border-orange-400/20";
}

function normalizeAnswer(value) {
  return (value || "").trim().toLowerCase();
}

export default function ScoreCard({
  result,
  topic,
  review,
  onRetry,
  isRetrying = false,
}) {
  if (!result) {
    return null;
  }

  return (
    <article className="panel mt-5 overflow-hidden bg-canvas/82">
      <div className="grid gap-5 px-5 py-5 lg:grid-cols-[0.8fr,1.2fr]">
        <div className={`interactive-surface rounded-[20px] border p-5 ${scoreTone(result.score_percent)}`}>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] opacity-70">
            Quiz Score
          </p>
          <p className="mt-3 text-5xl font-semibold text-white">{result.score_percent}%</p>
          <p className="mt-3 text-sm font-medium">
            {result.correct_answers}/{result.total_questions} correct on {topic}
          </p>
        </div>

        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-ocean/16 bg-ocean/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-ocean">
              New Level: {label(result.new_level)}
            </span>
            {result.weak_area && result.weak_area !== "none" ? (
              <span className="rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-orange-200">
                Weak Area: {label(result.weak_area)}
              </span>
            ) : (
              <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">
                No major weak area
              </span>
            )}
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
              AICES Feedback
            </p>
            <p className="mt-2 text-sm leading-7 text-slate-300">{result.feedback}</p>
          </div>
        </div>
      </div>

      {review?.questions?.length ? (
        <div className="border-t border-ocean/10 bg-canvas/68 px-5 py-5">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
                Quiz Review
              </p>
              <h3 className="mt-2 text-xl font-semibold text-white">
                Review {formatTopicLabel(review.topic, { fallback: "This topic", strict: true })}
              </h3>
            </div>

            <button
              className="neon-button rounded-[18px] border border-ocean/24 bg-ocean/12 px-4 py-2.5 text-sm font-semibold text-ocean disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isRetrying}
              onClick={onRetry}
              type="button"
            >
              {isRetrying ? "Preparing..." : "Retry Quiz"}
            </button>
          </div>

          <div className="space-y-4">
            {review.questions.map((question, index) => {
              const selectedAnswer = question.selected_answer;
              const correctAnswer = question.correct_answer;
              const isCorrect = normalizeAnswer(selectedAnswer) === normalizeAnswer(correctAnswer);

              return (
                <section
                  key={`${question.question}-${index}`}
                  className={[
                    "interactive-surface rounded-[20px] border p-4 shadow-soft",
                    isCorrect
                      ? "border-emerald-400/20 bg-emerald-500/8"
                      : "border-orange-400/20 bg-orange-500/8",
                  ].join(" ")}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                      Question {index + 1}
                    </span>
                    <span
                      className={[
                        "rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em]",
                        isCorrect
                          ? "border border-emerald-400/20 bg-emerald-500/10 text-emerald-200"
                          : "border border-orange-400/20 bg-orange-500/10 text-orange-200",
                      ].join(" ")}
                    >
                      {isCorrect ? "Correct" : "Incorrect"}
                    </span>
                  </div>

                  <h4 className="mt-3 text-base font-semibold leading-7 text-white">
                    {question.question}
                  </h4>

                  <div className="mt-4 grid gap-2">
                    {question.options.map((option) => {
                      const isSelected = normalizeAnswer(selectedAnswer) === normalizeAnswer(option);
                      const isCorrectOption = normalizeAnswer(correctAnswer) === normalizeAnswer(option);

                      return (
                        <div
                          key={option}
                          className={[
                            "rounded-[16px] border px-4 py-3 text-sm leading-6",
                            isCorrectOption
                              ? "border-emerald-400/25 bg-emerald-500/12 text-emerald-100"
                              : isSelected
                                ? "border-orange-400/25 bg-orange-500/12 text-orange-100"
                                : "border-ocean/10 bg-ink/70 text-slate-300",
                          ].join(" ")}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span>{option}</span>
                            {isCorrectOption ? (
                              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">
                                Correct
                              </span>
                            ) : null}
                            {!isCorrectOption && isSelected ? (
                              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-orange-200">
                                Your choice
                              </span>
                            ) : null}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        </div>
      ) : null}
    </article>
  );
}
