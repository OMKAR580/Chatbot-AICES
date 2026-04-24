import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim();

const apiClient = axios.create({
  baseURL: BASE_URL ? BASE_URL.replace(/\/+$/, "") : "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

export async function sendChatMessage({
  userId,
  message,
  requestId,
  mode = "standard",
  responseDepth = "normal",
  responseMode = "auto",
  codeRequired,
  codeLanguage,
  topic,
}) {
  const response = await apiClient.post("/chat", {
    user_id: userId,
    message,
    request_id: requestId,
    mode,
    response_depth: responseDepth,
    response_mode: responseMode,
    code_required: codeRequired,
    code_language: codeLanguage,
    topic,
  });

  const data = response.data || {};
  return {
    ...data,
    explanation: data.explanation || data.response || "",
    language: data.language || "",
    topic: data.topic || "",
  };
}

export async function generateQuiz({ userId, topic, count = 5, level, language }) {
  const response = await apiClient.post("/quiz", {
    user_id: userId,
    topic,
    count,
    level,
    language,
  });

  return response.data;
}

export async function evaluateQuiz({ userId, topic, answers }) {
  const response = await apiClient.post("/evaluate", {
    user_id: userId,
    topic,
    answers,
  });

  return response.data;
}

export async function getProgress(userId) {
  const response = await apiClient.get(`/progress/${encodeURIComponent(userId)}`);

  return response.data;
}

export async function getUserProfile(userId) {
  const response = await apiClient.get(`/user/${encodeURIComponent(userId)}`);

  return response.data;
}

export async function updateUserLanguage({ userId, preferredLanguage }) {
  const response = await apiClient.post("/user/language", {
    user_id: userId,
    preferred_language: preferredLanguage,
  });

  return response.data;
}

export async function getChatHistory(userId) {
  const response = await apiClient.get(`/history/${encodeURIComponent(userId)}`);

  return response.data;
}

export async function getRecommendations(userId) {
  const response = await apiClient.get(`/recommendations/${encodeURIComponent(userId)}`);

  return response.data;
}

export function getApiErrorMessage(error) {
  if (error.response?.data?.detail) {
    if (Array.isArray(error.response.data.detail)) {
      return error.response.data.detail
        .map((item) => item.msg || "Invalid request data.")
        .join(" ");
    }

    return error.response.data.detail;
  }

  if (error.code === "ECONNABORTED") {
    return "The request took too long. Please try again.";
  }

  if (error.message === "Network Error") {
    return "The AICES backend is unreachable. Check that the API is running and that VITE_API_BASE_URL points to the deployed backend.";
  }

  return "Something went wrong while contacting the backend. Please try again.";
}
