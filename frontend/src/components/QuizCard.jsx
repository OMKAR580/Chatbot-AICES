import { formatTopicLabel } from "../utils/topic";

export default function QuizCard({
  quiz,
  selectedAnswers,
  isSubmitting,
  onCancel,
  onSelectAnswer,
  onSubmit,
}) {
  if (!quiz?.questions?.length) {
    return null;
  }

  const answeredCount = quiz.questions.filter((_, index) => selectedAnswers[index]).length;
  const canSubmit = answeredCount === quiz.questions.length && !isSubmitting;

  return (
    <article className="panel mt-5 overflow-hidden border-ocean/15 bg-canvas/82">
      <div className="flex flex-col gap-4 border-b border-ocean/10 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-ocean/70">
            Adaptive Quiz
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-white">
            {formatTopicLabel(quiz.topic, { fallback: "Current topic", strict: true })} check-in
          </h3>
          <p className="mt-2 text-sm text-slate-300">
            Answer every question, then AICES will update your learner profile.
          </p>
        </div>

        <div className="rounded-2xl border border-ocean/18 bg-ocean/10 px-4 py-3 text-sm font-semibold text-ocean">
          {answeredCount}/{quiz.questions.length} answered
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        {quiz.questions.map((question, questionIndex) => (
          <section
            key={`${question.question}-${questionIndex}`}
            className="interactive-surface rounded-[20px] border border-ocean/12 bg-canvas/68 p-4 shadow-soft"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              Question {questionIndex + 1}
            </p>
            <h4 className="mt-2 text-base font-semibold leading-7 text-white">
              {question.question}
            </h4>

            <div className="mt-4 grid gap-2">
              {question.options.map((option) => {
                const isSelected = selectedAnswers[questionIndex] === option;

                return (
                  <button
                    key={option}
                    className={[
                      "rounded-[18px] border px-4 py-3 text-left text-sm font-medium transition-all duration-300 ease-out active:scale-[0.97]",
                      isSelected
                        ? "border-ocean/40 bg-ocean/12 text-ocean shadow-[0_0_10px_rgba(0,150,255,0.3)]"
                        : "border-ocean/10 bg-ink/70 text-slate-200 hover:scale-[1.02] hover:border-ocean/28 hover:text-white",
                    ].join(" ")}
                    onClick={() => onSelectAnswer(questionIndex, option)}
                    type="button"
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      <div className="flex flex-col gap-3 border-t border-ocean/10 bg-canvas/70 px-5 py-4 sm:flex-row sm:justify-end">
        <button
          className="neon-button rounded-[20px] border border-ocean/12 bg-ink/70 px-5 py-3 text-sm font-semibold text-slate-300 hover:border-ocean/30 hover:text-white"
          disabled={isSubmitting}
          onClick={onCancel}
          type="button"
        >
          Close Quiz
        </button>

        <button
          className="neon-button rounded-[20px] border border-ocean/30 bg-ocean px-5 py-3 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
          disabled={!canSubmit}
          onClick={onSubmit}
          type="button"
        >
          {isSubmitting ? "Evaluating..." : "Submit Quiz"}
        </button>
      </div>
    </article>
  );
}
