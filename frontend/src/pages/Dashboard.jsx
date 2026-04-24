import { useEffect, useState } from "react";

import DashboardSummary from "../components/DashboardSummary";
import ProgressCard from "../components/ProgressCard";
import RecommendationCard from "../components/RecommendationCard";
import {
  getApiErrorMessage,
  getChatHistory,
  getProgress,
  getRecommendations,
} from "../services/api";
import { formatTopicLabel } from "../utils/topic";
import { readStoredLanguage, writeStoredLanguage } from "../utils/userPrefs";

const DEFAULT_USER_ID = import.meta.env.VITE_AICES_USER_ID || "user_001";

function label(value) {
  return formatTopicLabel(value, { fallback: "Beginner" });
}

function formatActivityTime(value) {
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

export default function Dashboard() {
  const [progressData, setProgressData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [history, setHistory] = useState([]);
  const [preferredLanguage, setPreferredLanguage] = useState(() => readStoredLanguage());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setError("");
    setIsLoading(true);

    try {
      const [progressResult, recommendationResult, historyResult] = await Promise.allSettled([
        getProgress(DEFAULT_USER_ID),
        getRecommendations(DEFAULT_USER_ID),
        getChatHistory(DEFAULT_USER_ID),
      ]);

      const progress = progressResult.status === "fulfilled" ? progressResult.value : null;
      const recommendationData =
        recommendationResult.status === "fulfilled" ? recommendationResult.value : null;
      const historyData = historyResult.status === "fulfilled" ? historyResult.value : null;
      const resolvedLanguage = progress?.preferred_language || readStoredLanguage();

      setProgressData(progress);
      setRecommendations(recommendationData?.recommended_topics || []);
      setHistory(historyData?.history || []);
      setPreferredLanguage(resolvedLanguage);
      if (resolvedLanguage) {
        writeStoredLanguage(resolvedLanguage);
      }

      if (!progress && !recommendationData && !historyData) {
        throw progressResult.reason || new Error("Failed to load dashboard data.");
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const weakTopics = progressData?.weak_topics || [];
  const topicProgress = progressData?.topic_progress || [];
  const recentScores = progressData?.recent_scores || [];
  const recentActivity = history.slice(0, 4);

  return (
    <section className="space-y-6">
      <div className="panel overflow-hidden">
        <div className="grid gap-6 px-6 py-8 lg:grid-cols-[1.35fr,0.85fr] lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ocean/70">
              Dashboard
            </p>
            <h2 className="mt-3 text-3xl font-semibold leading-tight text-white sm:text-4xl">
              Your learning dashboard
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
              Review your progress, revisit weak areas, and see what AICES thinks
              you should study next.
            </p>
          </div>

          <div className="panel-muted flex flex-col justify-between gap-5 p-5">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
                Current Learner
              </p>
              <p className="mt-2 text-3xl font-semibold text-ocean">
                {label(progressData?.current_level)}
              </p>
              <p className="mt-2 text-sm text-slate-400">
                {DEFAULT_USER_ID} studying in {preferredLanguage || "Not set yet"}
              </p>
            </div>

            <button
              className="neon-button rounded-[20px] border border-ocean/30 bg-ocean px-5 py-3 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-55 disabled:hover:translate-y-0"
              disabled={isLoading}
              onClick={loadDashboard}
              type="button"
            >
              {isLoading ? "Refreshing..." : "Refresh Dashboard"}
            </button>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      <DashboardSummary
        currentLevel={progressData?.current_level}
        preferredLanguage={preferredLanguage}
        recentScores={recentScores}
        topicCount={topicProgress.length}
        weakTopicCount={weakTopics.length}
      />

      <div className="grid gap-5 xl:grid-cols-[1fr,0.9fr]">
        <section className="panel p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
                Recommended Next Topics
              </p>
              <h3 className="mt-2 text-2xl font-semibold text-white">
                Smart practice path
              </h3>
            </div>
            <span className="rounded-full border border-ocean/18 bg-ocean/10 px-4 py-2 text-sm font-semibold text-ocean">
              {recommendations.length || 0} suggestions
            </span>
          </div>

          {recommendations.length ? (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {recommendations.map((topic, index) => (
                <RecommendationCard key={topic} index={index} topic={topic} />
              ))}
            </div>
          ) : (
            <p className="mt-5 rounded-[24px] border border-ocean/10 bg-canvas/70 px-5 py-5 text-sm leading-7 text-slate-400">
              Recommendations appear after AICES has enough chat and quiz activity
              to understand what needs the most practice.
            </p>
          )}
        </section>

        <section className="panel p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
            Recent Activity
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-white">
            Chat memory snapshot
          </h3>

          {recentActivity.length ? (
            <div className="mt-5 space-y-3">
              {recentActivity.map((item, index) => (
                <article
                  key={`${item.created_at}-${index}`}
                  className="interactive-surface rounded-[20px] border border-ocean/10 bg-canvas/68 px-4 py-3 shadow-soft"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold text-white">
                      {formatTopicLabel(item.topic, { fallback: "Topic", strict: true })}
                    </p>
                    <span className="text-xs font-semibold text-slate-500">
                      {formatActivityTime(item.created_at)}
                    </span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-400">
                    {item.user_message}
                  </p>
                </article>
              ))}
            </div>
          ) : (
            <p className="mt-5 rounded-[24px] border border-ocean/10 bg-canvas/70 px-5 py-5 text-sm leading-7 text-slate-400">
              No chat memory yet. Use the chat page to create your first saved
              adaptive explanation.
            </p>
          )}
        </section>
      </div>

      <div className="grid gap-5 lg:grid-cols-[0.9fr,1.1fr]">
        <article className="panel p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
            Weak Topics
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-white">
            Concepts needing revision
          </h3>

          {weakTopics.length ? (
            <div className="mt-5 flex flex-wrap gap-2">
              {weakTopics.map((topic) => (
                <span
                  key={topic}
                  className="rounded-full border border-orange-400/20 bg-orange-500/10 px-4 py-2 text-sm font-semibold text-orange-200 shadow-soft"
                >
                  {label(topic)}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-5 text-sm leading-7 text-slate-400">
              No weak topics yet. Take a quiz from the chat page to generate
              diagnostic signals.
            </p>
          )}
        </article>

        <article className="panel p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
            Recent Scores
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-white">
            Last quiz attempts
          </h3>

          {recentScores.length ? (
            <div className="mt-5 flex items-end gap-3">
              {recentScores.map((score, index) => (
                <div
                  key={`${score}-${index}`}
                  className="flex flex-1 flex-col items-center gap-2"
                >
                  <div className="flex h-32 w-full items-end rounded-[18px] bg-ink/75 p-2 shadow-soft">
                    <div
                      className="w-full origin-bottom rounded-[14px] bg-gradient-to-t from-ocean via-sky-400 to-cyan-300 shadow-[0_0_10px_rgba(0,150,255,0.3)]"
                      style={{
                        height: `${Math.max(8, Math.min(100, score))}%`,
                        animation: "progressReveal 0.8s ease-out",
                      }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-white">{score}%</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-5 text-sm leading-7 text-slate-400">
              Your recent score chart will appear after the first submitted quiz.
            </p>
          )}
        </article>
      </div>

      <div>
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ocean/70">
              Mastery By Topic
            </p>
            <h3 className="mt-2 text-2xl font-semibold text-white">
              Concept progress cards
            </h3>
          </div>
        </div>

        {topicProgress.length ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {topicProgress.map((progress) => (
              <ProgressCard
                key={progress.topic}
                masteryPercent={progress.mastery_percent}
                topic={progress.topic}
                weakPoints={progress.weak_points}
              />
            ))}
          </div>
        ) : (
          <div className="panel p-6 text-sm leading-7 text-slate-400">
            No topic mastery records yet. Use "Quiz Me" in chat to create the
            first concept progress entry.
          </div>
        )}
      </div>
    </section>
  );
}
