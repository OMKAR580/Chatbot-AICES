import { useEffect, useRef, useState } from "react";

import ChatBox from "../components/ChatBox";
import HistoryPanel from "../components/HistoryPanel";
import LanguageSwitcher from "../components/LanguageSwitcher";
import QuizCard from "../components/QuizCard";
import ScoreCard from "../components/ScoreCard";
import {
  evaluateQuiz,
  generateQuiz,
  getApiErrorMessage,
  getChatHistory,
  getProgress,
  getUserProfile,
  sendChatMessage,
  updateUserLanguage,
} from "../services/api";
import { cleanCoreTopic, formatTopicLabel as formatTopicText } from "../utils/topic";
import { readStoredLanguage, writeStoredLanguage } from "../utils/userPrefs";

const DEFAULT_USER_ID = import.meta.env.VITE_AICES_USER_ID || "user_001";

const starterMessage = {
  id: "starter-message",
  sender: "assistant",
  text:
    "I can teach one concept at a time, go step by step, add code when you need it, and turn the same topic into a quiz whenever you're ready.",
};

const commandPattern =
  /\b(?:please\s+)?(?:explain|teach\s+me|tell\s+me\s+about|describe|define|give(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|show(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|create(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|make(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|generate(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?)\b/gi;
const depthPatterns = [
  /\bin\s+depth\b/i,
  /\bin\s+detail\b/i,
  /\bdetail\b/i,
  /\bdetailed\b/i,
  /\bfull\s+notes\b/i,
  /\bnotes\b/i,
  /\bstep\s+by\s+step\b/i,
  /\bteach\s+me\b/i,
];
const shortPatterns = [/\bshort\b/i, /\bbrief\b/i, /\bquick\b/i, /\bin short\b/i];
const notesPatterns = [
  /\bfull\s+notes\b/i,
  /\bnotes\s+mode\b/i,
  /\bclass\s+notes\b/i,
  /\bstudy\s+notes\b/i,
  /\bnotes\b/i,
];
const interviewPatterns = [/\binterview\b/i, /\bviva\b/i, /\binterview\s+mode\b/i];
const codePatterns = [
  /\bwith\s+code\b/i,
  /\bcode\b/i,
  /\bprogram\b/i,
  /\bimplementation\b/i,
  /\boutput\b/i,
];
const codeLanguagePatterns = [
  {
    label: "Python",
    patterns: [/\bin\s+python\b/i, /\busing\s+python\b/i, /\bpython\s+(?:code|program|implementation)\b/i],
  },
  {
    label: "Java",
    patterns: [/\bin\s+java\b/i, /\busing\s+java\b/i, /\bjava\s+(?:code|program|implementation)\b/i],
  },
  {
    label: "C",
    patterns: [/\bin\s+c\b/i, /\busing\s+c\b/i, /\bc\s+(?:code|program|implementation)\b/i],
  },
];
function createMessageId(prefix) {
  const randomPart = globalThis.crypto?.randomUUID?.() ?? Date.now().toString();
  return `${prefix}-${randomPart}`;
}

function detectCodeLanguage(message) {
  const trimmed = message.trim();

  for (const entry of codeLanguagePatterns) {
    if (entry.patterns.some((pattern) => pattern.test(trimmed))) {
      return entry.label;
    }
  }

  return null;
}

function detectResponseMode(message) {
  const trimmed = message.trim();

  if (interviewPatterns.some((pattern) => pattern.test(trimmed))) {
    return "interview";
  }

  if (notesPatterns.some((pattern) => pattern.test(trimmed))) {
    return "notes";
  }

  if (codePatterns.some((pattern) => pattern.test(trimmed))) {
    return "code";
  }

  if (shortPatterns.some((pattern) => pattern.test(trimmed))) {
    return "short";
  }

  if (depthPatterns.some((pattern) => pattern.test(trimmed))) {
    return "detailed";
  }

  return "auto";
}

function formatTopicLabel(value) {
  return formatTopicText(value, { fallback: "No topic yet", strict: true });
}

function parseChatIntent(message) {
  const trimmed = message.trim();
  let mode = "standard";
  const responseMode = detectResponseMode(trimmed);
  let responseDepth = "normal";
  const detectedCodeLanguage = detectCodeLanguage(trimmed);
  let codeRequired =
    responseMode === "code"
      || Boolean(detectedCodeLanguage)
      || codePatterns.some((pattern) => pattern.test(trimmed));

  if (["detailed", "notes", "code"].includes(responseMode)) {
    responseDepth = "detailed";
  } else if (responseMode === "auto" && depthPatterns.some((pattern) => pattern.test(trimmed))) {
    responseDepth = "detailed";
  }

  if (/\b(real[-\s]?life|real world|examples?|give an example|example of|with example|analogy)\b/i.test(trimmed)) {
    mode = "example";
  } else if (/\b(technically|technical|advanced|complexity|operations?|edge cases?|time complexity|space complexity)\b/i.test(trimmed)) {
    mode = "technical";
  } else if (/\b(simple|simpler|simply|easy|easier|basic)\b/i.test(trimmed)) {
    mode = "simpler";
  }

  const topics = extractTopics(trimmed);
  return {
    mode,
    responseDepth,
    responseMode,
    codeRequired,
    codeLanguage: detectedCodeLanguage || "Python",
    topic: topics.length === 1 ? topics[0] : "",
    topics,
    isClear: topics.length === 1,
  };
}

function extractTopics(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    return [];
  }

  const commandSplitText = trimmed.replace(commandPattern, "|");
  const commandSegments = commandSplitText
    .split("|")
    .map((segment) => segment.trim())
    .filter(Boolean);
  const segments = commandSegments.length ? commandSegments : [trimmed];
  const topics = [];

  segments.forEach((segment) => {
    splitPossibleTopicList(segment).forEach((candidate) => {
      const topic = cleanTopic(candidate);
      if (topic && !topics.includes(topic)) {
        topics.push(topic);
      }
    });
  });

  return topics;
}

function splitPossibleTopicList(value) {
  if (/\s(?:and|or)\s|[,;/]/i.test(value)) {
    return value.split(/\s+(?:and|or)\s+|[,;/]/i).map((part) => part.trim());
  }

  return [value];
}

function cleanTopic(value) {
  return cleanCoreTopic(value);
}

export default function ChatPage() {
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState([starterMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [learnerLevel, setLearnerLevel] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState(() => readStoredLanguage());
  const [lastAskedTopic, setLastAskedTopic] = useState("");
  const [lastExplanationMode, setLastExplanationMode] = useState("standard");
  const [lastResponseMode, setLastResponseMode] = useState("auto");
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [quizCount, setQuizCount] = useState(5);
  const [lastQuizReview, setLastQuizReview] = useState(null);
  const [isQuizLoading, setIsQuizLoading] = useState(false);
  const [isQuizSubmitting, setIsQuizSubmitting] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isLanguageUpdating, setIsLanguageUpdating] = useState(false);
  const pendingChatRequestRef = useRef("");

  const draftIntent = inputValue.trim() ? parseChatIntent(inputValue) : null;
  const draftTopic = draftIntent?.isClear ? draftIntent.topic : "";
  const activeTopic = lastAskedTopic || draftTopic;
  const activeTutorView = lastResponseMode !== "auto" ? lastResponseMode : lastExplanationMode;
  const isBusy = isLoading || isQuizLoading || isQuizSubmitting || isLanguageUpdating;

  function appendMessageOnce(newMessage) {
    setMessages((previousMessages) => {
      const exists = previousMessages.some((message) => message.id === newMessage.id);
      if (exists) {
        return previousMessages;
      }

      return [...previousMessages, newMessage];
    });
  }

  useEffect(() => {
    let ignore = false;

    async function loadInitialData() {
      setIsHistoryLoading(true);

      try {
        const [profileResult, progressResult, historyResult] = await Promise.allSettled([
          getUserProfile(DEFAULT_USER_ID),
          getProgress(DEFAULT_USER_ID),
          getChatHistory(DEFAULT_USER_ID),
        ]);

        if (ignore) {
          return;
        }

        const profile = profileResult.status === "fulfilled" ? profileResult.value : null;
        const progress = progressResult.status === "fulfilled" ? progressResult.value : null;
        const history = historyResult.status === "fulfilled" ? historyResult.value : null;
        const resolvedLanguage =
          profile?.preferred_language || progress?.preferred_language || readStoredLanguage();

        setLearnerLevel(profile?.current_level || progress?.current_level || "");
        setPreferredLanguage(resolvedLanguage);
        if (resolvedLanguage) {
          writeStoredLanguage(resolvedLanguage);
        }
        setChatHistory(history?.history || []);

        if (!profile && !progress && !history) {
          throw profileResult.reason || new Error("Failed to load AICES data.");
        }
      } catch (requestError) {
        if (!ignore) {
          setError(getApiErrorMessage(requestError));
        }
      } finally {
        if (!ignore) {
          setIsHistoryLoading(false);
        }
      }
    }

    loadInitialData();

    return () => {
      ignore = true;
    };
  }, []);

  async function refreshHistory() {
    const data = await getChatHistory(DEFAULT_USER_ID);
    setChatHistory(data.history || []);
  }

  async function submitMessage(rawMessage, topicOverride, overrides = {}) {
    if (pendingChatRequestRef.current) {
      return;
    }

    const message = rawMessage.trim();
    if (!message) {
      setError("Please enter a concept or question before sending.");
      return;
    }

    const parsedIntent = parseChatIntent(message);
    const mode = overrides.modeOverride === "standard" || !overrides.modeOverride
      ? parsedIntent.mode
      : overrides.modeOverride;
    const responseMode = overrides.responseModeOverride === "auto" || !overrides.responseModeOverride
      ? parsedIntent.responseMode
      : overrides.responseModeOverride;
    const responseDepth = ["detailed", "notes", "code"].includes(responseMode)
      ? "detailed"
      : ["short", "interview"].includes(responseMode)
        ? "normal"
        : parsedIntent.responseDepth;
    const codeRequired = responseMode === "code" ? true : parsedIntent.codeRequired;
    const codeLanguage = parsedIntent.codeLanguage;

    const requestId = createMessageId("chat");
    const userMessageId = `user-${requestId}`;
    const assistantMessageId = `assistant-${requestId}`;
    setError("");
    setStatusMessage("");
    setLastExplanationMode(mode);
    setLastResponseMode(responseMode);
    pendingChatRequestRef.current = requestId;
    appendMessageOnce({
      id: userMessageId,
      sender: "user",
      text: message,
    });
    setInputValue("");
    setIsLoading(true);

    try {
      const data = await sendChatMessage({
        userId: DEFAULT_USER_ID,
        message,
        requestId,
        mode,
        responseDepth,
        responseMode,
        codeRequired: codeRequired ? true : undefined,
        codeLanguage: codeRequired ? codeLanguage : undefined,
      });

      if (pendingChatRequestRef.current !== requestId) {
        return;
      }

      setLearnerLevel(data.level);
      setPreferredLanguage(data.language || preferredLanguage);
      if (data.language) {
        writeStoredLanguage(data.language);
      }
      setLastAskedTopic(data.topic);
      setLastExplanationMode(data.mode || mode);
      setLastResponseMode(data.response_mode || responseMode);
      appendMessageOnce({
        id: assistantMessageId,
        sender: "assistant",
        text: data.explanation || data.response,
        level: data.level,
        topic: data.topic,
      });

      try {
        await refreshHistory();
      } catch {
        setStatusMessage("Explanation saved, but recent chats could not refresh automatically.");
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      if (pendingChatRequestRef.current === requestId) {
        pendingChatRequestRef.current = "";
      }
      setIsLoading(false);
    }
  }

  async function startQuiz(topic, countOverride = quizCount) {
    const quizTopic = topic.trim();
    if (!quizTopic) {
      setError("Ask about a concept first so AICES knows what to quiz you on.");
      return;
    }

    setError("");
    setStatusMessage("");
    setQuizResult(null);
    setLastQuizReview(null);
    setActiveQuiz(null);
    setSelectedAnswers({});
    setLastExplanationMode("quiz");
    setLastResponseMode("auto");
    setIsQuizLoading(true);

    try {
      const quizLanguage = preferredLanguage || readStoredLanguage() || "English";
      const data = await generateQuiz({
        userId: DEFAULT_USER_ID,
        topic: quizTopic,
        count: countOverride,
        level: learnerLevel || undefined,
        language: quizLanguage,
      });

      setActiveQuiz(data);
      setLastAskedTopic(data.topic || quizTopic);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsQuizLoading(false);
    }
  }

  function selectQuizAnswer(questionIndex, option) {
    setSelectedAnswers((currentAnswers) => ({
      ...currentAnswers,
      [questionIndex]: option,
    }));
  }

  async function submitQuiz() {
    if (!activeQuiz?.questions?.length) {
      return;
    }

    const reviewSnapshot = {
      topic: activeQuiz.topic,
      questions: activeQuiz.questions.map((question, questionIndex) => ({
        ...question,
        selected_answer: selectedAnswers[questionIndex],
      })),
    };
    const answers = activeQuiz.questions.map((question, questionIndex) => ({
      question: question.question,
      selected_answer: selectedAnswers[questionIndex],
      correct_answer: question.correct_answer,
    }));

    setError("");
    setStatusMessage("");
    setIsQuizSubmitting(true);

    try {
      const result = await evaluateQuiz({
        userId: DEFAULT_USER_ID,
        topic: activeQuiz.topic,
        answers,
      });

      setQuizResult(result);
      setLastQuizReview(reviewSnapshot);
      setLearnerLevel(result.new_level);
      setActiveQuiz(null);
      setSelectedAnswers({});
      setStatusMessage(`Quiz updated for ${formatTopicLabel(activeQuiz.topic)}.`);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsQuizSubmitting(false);
    }
  }

  async function handleLanguageChange(nextLanguage) {
    setError("");
    setStatusMessage("");
    setIsLanguageUpdating(true);

    try {
      const data = await updateUserLanguage({
        userId: DEFAULT_USER_ID,
        preferredLanguage: nextLanguage,
      });

      setPreferredLanguage(data.preferred_language);
      writeStoredLanguage(data.preferred_language);
      setStatusMessage(data.message);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsLanguageUpdating(false);
    }
  }

  function handleHistorySelect(historyItem) {
    setError("");
    setStatusMessage("");
    setActiveQuiz(null);
    setQuizResult(null);
    setLastQuizReview(null);
    setSelectedAnswers({});
    setLastAskedTopic(historyItem.topic);
    setLastExplanationMode("standard");
    setLastResponseMode("auto");
    setLearnerLevel(historyItem.learner_level);
    setMessages([
      starterMessage,
      {
        id: createMessageId("history-user"),
        sender: "user",
        text: historyItem.user_message,
      },
      {
        id: createMessageId("history-assistant"),
        sender: "assistant",
        text: historyItem.ai_response,
        level: historyItem.learner_level,
        topic: historyItem.topic,
      },
    ]);
  }

  function handleAction(actionKey) {
    if (!activeTopic) {
      setError("Ask about a concept first so AICES knows what to adapt.");
      return;
    }

    if (actionKey === "quiz") {
      startQuiz(activeTopic);
      return;
    }

    if (!["short", "detailed", "notes", "code", "interview"].includes(actionKey)) {
      return;
    }

    const nextPrompt = `Explain ${activeTopic}`;
    submitMessage(nextPrompt, activeTopic, { responseModeOverride: actionKey });
  }

  return (
    <div className="grid items-start gap-6 xl:grid-cols-[280px,minmax(0,1fr)]">
      <aside className="order-2 space-y-4 xl:order-1 xl:sticky xl:top-6">
        <LanguageSwitcher
          disabled={isBusy}
          isUpdating={isLanguageUpdating}
          onChange={handleLanguageChange}
          value={preferredLanguage}
        />

        {statusMessage ? (
          <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-sm font-medium text-emerald-200">
            {statusMessage}
          </div>
        ) : null}

        <HistoryPanel
          activeTopic={activeTopic}
          history={chatHistory}
          isLoading={isHistoryLoading}
          onSelect={handleHistorySelect}
        />
      </aside>

      <div className="order-1 mx-auto w-full max-w-5xl space-y-4 xl:order-2">
        <ChatBox
          error={error}
          inputValue={inputValue}
          isLoading={isBusy}
          language={preferredLanguage}
          learnerLevel={learnerLevel}
          messages={messages}
          mode={activeTutorView}
          onAction={handleAction}
          onInputChange={setInputValue}
          onQuizCountChange={setQuizCount}
          onSend={() => submitMessage(inputValue, undefined, {})}
          quizCount={quizCount}
          topic={formatTopicLabel(activeTopic)}
        />

        <QuizCard
          isSubmitting={isQuizSubmitting}
          onCancel={() => {
            setActiveQuiz(null);
            setSelectedAnswers({});
          }}
          onSelectAnswer={selectQuizAnswer}
          onSubmit={submitQuiz}
          quiz={activeQuiz}
          selectedAnswers={selectedAnswers}
        />

        <ScoreCard
          isRetrying={isQuizLoading}
          onRetry={() => startQuiz(lastQuizReview?.topic || lastAskedTopic || activeTopic)}
          result={quizResult}
          review={lastQuizReview}
          topic={formatTopicLabel(lastAskedTopic || activeTopic)}
        />
      </div>
    </div>
  );
}
