import { useEffect, useRef } from "react";

import ActionButtons from "./ActionButtons";
import MessageBubble from "./MessageBubble";

export default function ChatBox({
  error,
  inputValue,
  isLoading,
  language,
  learnerLevel,
  mode,
  messages,
  onAction,
  onInputChange,
  onSend,
  onQuizCountChange,
  quizCount,
  topic,
}) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const currentLevel = learnerLevel
    ? learnerLevel.charAt(0).toUpperCase() + learnerLevel.slice(1)
    : "Adapting";
  const currentMode = mode
    ? mode.charAt(0).toUpperCase() + mode.slice(1)
    : "Auto";
  const canSend = inputValue.trim().length > 0 && !isLoading;

  return (
    <section className="panel flex min-h-[78vh] flex-col overflow-hidden">
      <div className="border-b border-ocean/10 px-5 py-4 sm:px-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Tutor Chat</h2>
            <p className="mt-1 text-sm leading-6 text-slate-300">
              Ask one concept at a time. Try "Explain array in depth with code in Java"
              or "Teach recursion simply".
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-sm">
            <span className="rounded-full border border-ocean/20 bg-ocean/10 px-3 py-2 font-medium text-ocean shadow-[0_0_10px_rgba(0,150,255,0.14)]">
              Current topic: <span className="font-semibold">{topic || "No topic yet"}</span>
            </span>
            <span className="rounded-full border border-ocean/10 bg-canvas/68 px-3 py-2 font-medium text-slate-300 shadow-soft">
              {currentLevel}
            </span>
            <span className="rounded-full border border-ocean/10 bg-canvas/68 px-3 py-2 font-medium text-slate-300 shadow-soft">
              {language || "Language not set"}
            </span>
            <span className="rounded-full border border-ocean/10 bg-canvas/68 px-3 py-2 font-medium text-slate-300 shadow-soft">
              Tutor view: {currentMode}
            </span>
          </div>
        </div>
      </div>

      <div className="chat-scrollbar flex-1 overflow-y-auto bg-white/[0.02] px-4 py-7 sm:px-6">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-5">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {isLoading ? (
            <div className="flex justify-start">
              <div className="max-w-[88%] rounded-[22px] rounded-bl-md border border-ocean/16 bg-canvas/82 px-6 py-5 shadow-soft sm:max-w-[78%]">
                <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                  AICES
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-ocean/80" />
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-ocean/50 [animation-delay:120ms]" />
                  <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-ocean/30 [animation-delay:240ms]" />
                </div>
              </div>
            </div>
          ) : null}

          <div ref={endRef} />
        </div>
      </div>

      <div className="border-t border-ocean/10 bg-canvas/70 px-4 py-4 sm:px-6">
        <div className="mx-auto w-full max-w-4xl">
          {error ? (
            <div className="mb-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          ) : null}

          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              onSend();
            }}
          >
            <div className="flex flex-col gap-3">
              <textarea
                className="min-h-[92px] flex-1 resize-none rounded-[22px] border border-ocean/18 bg-ink/78 px-5 py-4 text-[15px] leading-7 text-slate-100 shadow-soft outline-none transition-all duration-300 ease-out placeholder:text-slate-500 focus:border-ocean/50 focus:ring-4 focus:ring-ocean/12 focus:shadow-[0_0_10px_rgba(0,150,255,0.3)]"
                disabled={isLoading}
                onChange={(event) => onInputChange(event.target.value)}
                placeholder="Ask a concept question, for example: Explain linked list step by step with code in Python"
                rows={3}
                value={inputValue}
              />

              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <ActionButtons
                  disabled={isLoading || !topic || topic === "No topic yet"}
                  onAction={onAction}
                  onQuizCountChange={onQuizCountChange}
                  quizCount={quizCount}
                />

                <button
                  className="neon-button rounded-[20px] border border-ocean/26 bg-ocean/92 px-6 py-3 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-55 disabled:hover:translate-y-0"
                  disabled={!canSend}
                  type="submit"
                >
                  {isLoading ? "Thinking..." : "Send"}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
