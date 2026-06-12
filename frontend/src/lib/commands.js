export const COMMAND_ALIASES = [
  {
    action: "close",
    words: ["close", "closed", "clothes", "clause", "cloze", "close it"],
  },
  {
    action: "buy",
    words: [
      "buy",
      "buy it",
      "bye",
      "bye it",
      "by",
      "by it",
      "bi",
      "boy",
      "you why",
    ],
  },
  {
    action: "sell",
    words: ["sell", "sell it", "sale", "cell", "shell", "sail", "sel"],
  },
];

function normalize(text) {
  return text.toLowerCase().trim().replace(/\s+/g, " ");
}

export function parseCommand(text) {
  const normalized = normalize(text);
  if (!normalized) return null;

  const matched = [];
  for (const { action, words } of COMMAND_ALIASES) {
    const hit = words.some(
      (alias) =>
        normalized === alias ||
        normalized.includes(alias) ||
        new RegExp(`\\b${alias.replace(/\s+/g, "\\s+")}\\b`).test(normalized),
    );
    if (hit) matched.push(action);
  }

  const unique = [...new Set(matched)];
  if (unique.length === 1) return unique[0];
  return null;
}
