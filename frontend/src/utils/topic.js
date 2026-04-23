const commandPattern =
  /\b(?:please\s+)?(?:explain|teach\s+me|tell\s+me\s+about|describe|define|what\s+is|what\s+are|how\s+does|how\s+do|why\s+does|why\s+do|give(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|show(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|create(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|make(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|generate(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?)\b/gi;
const fillerTopicPattern =
  /\b(please|kindly|can|could|would|you|me|about|of|for|on|in|with|a|an|the|what|is|are|how|why|do|does|explain|teach|tell|describe|define|give|show|create|make|generate|concept|topic|question|answer|explanation|simple|simpler|simply|easy|easier|basic|technical|technically|advanced|example|examples|real[-\s]?life|way|words|detail|detailed|deep|depth|dive|notes|code|program|implementation|output|step|quiz|full|short|brief|quick|interview|viva|class|study|mode|algorithm|method|approach|function|structure|data)\b/gi;
const genericTopics = new Set([
  "it",
  "this",
  "that",
  "concept",
  "topic",
  "question",
  "example",
  "explanation",
]);

export function cleanCoreTopic(value) {
  const cleanedValue = (value || "").trim();
  if (!cleanedValue) {
    return "";
  }

  const topic = cleanedValue
    .replace(commandPattern, " ")
    .replace(/\b(in\s+)?(a\s+)?(very\s+)?(simple|simpler|easy|easier|basic)\s+(way|words)\b/gi, " ")
    .replace(/\b(with\s+)?(real[-\s]?life\s+)?examples?\b/gi, " ")
    .replace(/\b(in\s+)?(technical|advanced)\s+(way|detail)\b/gi, " ")
    .replace(/\b(full\s+notes|class\s+notes|study\s+notes|interview\s+mode|notes\s+mode)\b/gi, " ")
    .replace(/\b(in\s+depth|in\s+detail|detail|detailed|full\s+notes|notes|with\s+code|with\s+output|step\s+by\s+step)\b/gi, " ")
    .replace(/\b(short|brief|quick|summary|interview|viva)\b/gi, " ")
    .replace(/\b(?:in|using|with)\s+(python|java|c)\b/gi, " ")
    .replace(/\b(?:python|java|c)\s+(?:code|program|implementation)\b/gi, " ")
    .replace(/\b(code|program|implementation|output)\b/gi, " ")
    .replace(fillerTopicPattern, " ")
    .replace(/\s+/g, " ")
    .replace(/^[\s.?!:-_]+|[\s.?!:-_]+$/g, "")
    .toLowerCase();

  const limitedTopic = topic.split(/\s+/).filter(Boolean).slice(0, 2).join(" ");
  if (!limitedTopic || !/[a-z0-9]/i.test(limitedTopic) || genericTopics.has(limitedTopic)) {
    return "";
  }

  return limitedTopic;
}

export function normalizeTopicPhrase(value) {
  const cleanedTopic = cleanCoreTopic(value);
  if (cleanedTopic) {
    return cleanedTopic;
  }

  return (value || "").trim().toLowerCase().replace(/\s+/g, " ");
}

export function formatTopicLabel(value, options = {}) {
  const { fallback = "Topic", strict = false } = options;
  const cleanedValue = strict ? cleanCoreTopic(value) : normalizeTopicPhrase(value);
  if (!cleanedValue) {
    return fallback;
  }

  return cleanedValue
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
