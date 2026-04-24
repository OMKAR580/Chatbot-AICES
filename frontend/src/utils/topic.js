const topicNormalizationPatterns = [
  [/\bdeepth\b/gi, "depth"],
  [/\bdeeply\b/gi, "depth"],
  [/\brobability\b/gi, "probability"],
  [/\bprobabilities\b/gi, "probability"],
  [/\blinked[\s-]*lists?\b/gi, "linked list"],
  [/\bbinary[\s-]*search(?:ing)?\b/gi, "binary search"],
  [/\bconvolutional\s+neural\s+networks?\b/gi, "cnn"],
  [/\bneural\s+networks?\b/gi, "neural network"],
  [/\barrays\b/gi, "array"],
  [/\bstacks\b/gi, "stack"],
  [/\bqueues\b/gi, "queue"],
  [/\btrees\b/gi, "tree"],
  [/\bgraphs\b/gi, "graph"],
  [/\brecursive\s+function\b/gi, "recursion"],
];

const protectedTechnicalTopics = [
  ["cnn", [/\bcnn\b/i, /\bcnn\s+model\b/i, /\bconvolutional\s+neural\s+network\b/i]],
  ["natural language processing", [/\bnlp\b/i, /\bnatural\s+language\s+processing\b/i]],
  ["linked list", [/\blinked\s+list\b/i, /\blinkedlist\b/i]],
  ["binary search", [/\bbinary\s+search\b/i, /\bbinarysearch\b/i]],
  ["static routing", [/\bstatic\s+routing\b/i]],
  ["dynamic routing", [/\bdynamic\s+routing\b/i]],
  ["computer network", [/\bcomputer\s+network(?:ing)?\b/i]],
  ["deep learning", [/\bdeep\s+learning\b/i]],
  ["machine learning", [/\bmachine\s+learning\b/i]],
  ["neural network", [/\bneural\s+network\b/i]],
  ["array", [/\barray\b/i]],
  ["stack", [/\bstack\b/i]],
  ["queue", [/\bqueue\b/i]],
  ["tree", [/\btree\b/i]],
  ["graph", [/\bgraph\b/i]],
  ["dbms", [/\bdbms\b/i]],
  ["os", [/\bos\b/i]],
  ["cn", [/\bcn\b/i]],
  ["oop", [/\boop\b/i]],
  ["dsa", [/\bdsa\b/i]],
  ["recursion", [/\brecursion\b/i]],
  ["probability", [/\bprobability\b/i]],
];

const topicDisplayLabels = {
  cnn: "CNN / Convolutional Neural Network",
  "linked list": "Linked List",
  "binary search": "Binary Search",
  "static routing": "Static Routing",
  "dynamic routing": "Dynamic Routing",
  "computer network": "Computer Network",
  "machine learning": "Machine Learning",
  "deep learning": "Deep Learning",
  "neural network": "Neural Network",
  "natural language processing": "Natural Language Processing",
  array: "Array",
  stack: "Stack",
  queue: "Queue",
  tree: "Tree",
  graph: "Graph",
  dbms: "DBMS",
  os: "OS",
  cn: "CN",
  oop: "OOP",
  dsa: "DSA",
  recursion: "Recursion",
  probability: "Probability",
};

const uppercaseTopicTokens = new Set(["cnn", "dbms", "os", "cn", "oop", "dsa"]);
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

const commandPattern =
  /\b(?:please\s+)?(?:explain|teach\s+me|tell\s+me\s+about|describe|define|what\s+is|what\s+are|how\s+does|how\s+do|why\s+does|why\s+do|give(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|show(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|create(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|make(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|generate(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?)\b/gi;
const fillerTopicPattern =
  /\b(please|kindly|can|could|would|you|me|about|of|for|on|in|with|a|an|the|what|is|are|how|why|do|does|explain|teach|tell|describe|define|give|show|create|make|generate|concept|topic|question|answer|explanation|simple|simpler|simply|easy|easier|basic|technical|technically|advanced|example|examples|real[-\s]?life|way|words|detail|detailed|deep|depth|dive|notes|code|program|implementation|output|step|quiz|full|short|brief|quick|and|or|interview|viva|class|study|mode|algorithm|method|approach|function|structure|data)\b/gi;

function normalizeTopicPhrasing(value) {
  let normalizedValue = (value || "").replace(/_+/g, " ");
  topicNormalizationPatterns.forEach(([pattern, replacement]) => {
    normalizedValue = normalizedValue.replace(pattern, replacement);
  });
  return normalizedValue;
}

function normalizeTopicSearchText(value) {
  return normalizeTopicPhrasing(value)
    .replace(/\//g, " ")
    .replace(/[^a-zA-Z0-9\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function extractProtectedTopic(value) {
  const searchText = normalizeTopicSearchText(value);
  if (!searchText) {
    return "";
  }

  for (const [canonicalTopic, patterns] of protectedTechnicalTopics) {
    if (patterns.some((pattern) => pattern.test(searchText))) {
      return canonicalTopic;
    }
  }

  return "";
}

function formatNormalizedTopic(topic) {
  const normalizedTopic = normalizeTopicSearchText(topic);
  if (!normalizedTopic) {
    return "";
  }

  if (topicDisplayLabels[normalizedTopic]) {
    return topicDisplayLabels[normalizedTopic];
  }

  return normalizedTopic
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => (uppercaseTopicTokens.has(word) ? word.toUpperCase() : word.charAt(0).toUpperCase() + word.slice(1)))
    .join(" ");
}

export function cleanCoreTopic(value, maxWords = 4) {
  if (!value || !value.trim()) {
    return "";
  }

  let topic = normalizeTopicPhrasing(value);
  const protectedTopic = extractProtectedTopic(topic);
  if (protectedTopic) {
    return formatNormalizedTopic(protectedTopic);
  }

  topic = topic
    .replace(commandPattern, " ")
    .replace(/\b(in\s+)?(a\s+)?(very\s+)?(simple|simpler|easy|easier|basic)\s+(way|words)\b/gi, " ")
    .replace(/\b(with\s+)?(real[-\s]?life\s+)?examples?\b/gi, " ")
    .replace(/\b(in\s+)?(technical|advanced)\s+(way|detail)\b/gi, " ")
    .replace(/\b(full\s+notes|class\s+notes|study\s+notes|interview\s+mode|notes\s+mode)\b/gi, " ")
    .replace(/\b(in\s+depth|in\s+detail|detail|detailed|full\s+notes|notes|with\s+code|with\s+output|step\s+by\s+step)\b/gi, " ")
    .replace(/\b(short|brief|quick|summary|interview|viva)\b/gi, " ")
    .replace(/\b(?:in|using|with)\s+(python|java|c)\b/gi, " ")
    .replace(/\b(?:python|java|c)\s+(?:code|program|implementation)\b/gi, " ")
    .replace(/\b(code|program|implementation|output)\b/gi, " ");

  const secondaryProtectedTopic = extractProtectedTopic(topic);
  if (secondaryProtectedTopic) {
    return formatNormalizedTopic(secondaryProtectedTopic);
  }

  topic = normalizeTopicPhrasing(topic.replace(fillerTopicPattern, " "))
    .replace(/^(?:and|or)\b/gi, " ")
    .replace(/\b(?:and|or)$/gi, " ")
    .replace(/\s+/g, " ")
    .replace(/^[\s.?!:-_]+|[\s.?!:-_]+$/g, "")
    .toLowerCase();

  if (!topic || !/[a-z0-9]/i.test(topic)) {
    return "";
  }

  const finalProtectedTopic = extractProtectedTopic(topic);
  if (finalProtectedTopic) {
    return formatNormalizedTopic(finalProtectedTopic);
  }

  const limitedTopic = topic.split(/\s+/).filter(Boolean).slice(0, maxWords).join(" ");
  if (!limitedTopic || genericTopics.has(limitedTopic)) {
    return "";
  }

  return formatNormalizedTopic(limitedTopic);
}

export function normalizeTopicPhrase(value) {
  const normalizedValue = normalizeTopicPhrasing(value).replace(/\s+/g, " ").trim();
  if (!normalizedValue) {
    return "";
  }

  return formatNormalizedTopic(normalizedValue);
}

export function formatTopicLabel(value, options = {}) {
  const { fallback = "Topic", strict = false } = options;
  const formattedValue = strict ? cleanCoreTopic(value) : normalizeTopicPhrase(value);
  return formattedValue || fallback;
}
