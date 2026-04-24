const LANGUAGE_STORAGE_KEY = "aices_preferred_language";
const SUPPORTED_LANGUAGES = new Set(["English", "Hindi", "Hinglish"]);

export function readStoredLanguage() {
  if (typeof window === "undefined") {
    return "";
  }

  const storedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY) || "";
  return SUPPORTED_LANGUAGES.has(storedLanguage) ? storedLanguage : "";
}

export function writeStoredLanguage(language) {
  if (typeof window === "undefined" || !SUPPORTED_LANGUAGES.has(language)) {
    return;
  }

  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
}
