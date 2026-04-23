import { formatTopicLabel } from "../utils/topic";

function levelLabel(level) {
  if (!level) {
    return null;
  }

  return level.charAt(0).toUpperCase() + level.slice(1);
}

function renderInlineText(text, keyPrefix) {
  return text.split(/(`[^`]+`)/g).filter(Boolean).flatMap((segment, index) => {
    if (segment.startsWith("`") && segment.endsWith("`")) {
      return [
        <code
          key={`${keyPrefix}-code-${index}`}
          className="rounded-md border border-ocean/12 bg-ink/70 px-1.5 py-0.5 font-mono text-[0.95em] text-butter"
        >
          {segment.slice(1, -1)}
        </code>,
      ];
    }

    return segment
      .split(/(\*\*[^*]+\*\*)/g)
      .filter(Boolean)
      .map((part, partIndex) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={`${keyPrefix}-strong-${index}-${partIndex}`} className="font-semibold">
              {part.slice(2, -2)}
            </strong>
          );
        }

        return <span key={`${keyPrefix}-text-${index}-${partIndex}`}>{part}</span>;
      });
  });
}

function renderPlainBlocks(text, keyPrefix) {
  return text
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block, blockIndex) => {
      const lines = block.split("\n").map((line) => line.trim());
      const listItems = lines.filter(Boolean);

      if (/^#{1,6}\s/.test(block)) {
        const heading = block.replace(/^#{1,6}\s*/, "");
        return (
          <h4 key={`${keyPrefix}-heading-${blockIndex}`} className="text-base font-semibold text-white">
            {renderInlineText(heading, `${keyPrefix}-heading-${blockIndex}`)}
          </h4>
        );
      }

      if (listItems.length && listItems.every((line) => /^[-*]\s+/.test(line))) {
        return (
          <ul
            key={`${keyPrefix}-ul-${blockIndex}`}
            className="list-disc space-y-2 pl-5 text-[15px] leading-7 text-slate-200"
          >
            {listItems.map((line, itemIndex) => (
              <li key={`${keyPrefix}-ul-${blockIndex}-${itemIndex}`}>
                {renderInlineText(line.replace(/^[-*]\s+/, ""), `${keyPrefix}-ul-${blockIndex}-${itemIndex}`)}
              </li>
            ))}
          </ul>
        );
      }

      if (listItems.length && listItems.every((line) => /^\d+\.\s+/.test(line))) {
        return (
          <ol
            key={`${keyPrefix}-ol-${blockIndex}`}
            className="list-decimal space-y-2 pl-5 text-[15px] leading-7 text-slate-200"
          >
            {listItems.map((line, itemIndex) => (
              <li key={`${keyPrefix}-ol-${blockIndex}-${itemIndex}`}>
                {renderInlineText(line.replace(/^\d+\.\s+/, ""), `${keyPrefix}-ol-${blockIndex}-${itemIndex}`)}
              </li>
            ))}
          </ol>
        );
      }

      return (
        <p
          key={`${keyPrefix}-p-${blockIndex}`}
          className="whitespace-pre-wrap text-[15px] leading-7 text-slate-200"
        >
          {lines.map((line, lineIndex) => (
            <span key={`${keyPrefix}-line-${blockIndex}-${lineIndex}`}>
              {renderInlineText(line, `${keyPrefix}-line-${blockIndex}-${lineIndex}`)}
              {lineIndex < lines.length - 1 ? <br /> : null}
            </span>
          ))}
        </p>
      );
    });
}

function renderRichContent(text) {
  const blocks = [];
  const codePattern = /```([\w+-]+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codePattern.exec(text)) !== null) {
    const plainText = text.slice(lastIndex, match.index);
    if (plainText.trim()) {
      blocks.push(...renderPlainBlocks(plainText, `plain-${blocks.length}`));
    }

    blocks.push(
      <div
        key={`code-${blocks.length}`}
        className="overflow-hidden rounded-[18px] border border-ocean/16 bg-[#0d1117] shadow-[0_0_10px_rgba(0,150,255,0.18)]"
      >
        <div className="border-b border-ocean/14 px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-ocean/80">
          {match[1] || "Code"}
        </div>
        <pre className="overflow-x-auto px-4 py-4 text-sm leading-7 text-slate-100">
          <code>{match[2].trim()}</code>
        </pre>
      </div>,
    );

    lastIndex = codePattern.lastIndex;
  }

  const trailingText = text.slice(lastIndex);
  if (trailingText.trim()) {
    blocks.push(...renderPlainBlocks(trailingText, `plain-${blocks.length}`));
  }

  return blocks;
}

export default function MessageBubble({ message }) {
  const isUser = message.sender === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={[
          "max-w-[92%] rounded-[22px] px-5 py-5 shadow-soft sm:max-w-[80%] sm:px-6",
          isUser
            ? "rounded-br-md border border-ocean/24 bg-gradient-to-br from-sky-400 via-ocean to-cyan-300 text-ink shadow-[0_0_10px_rgba(0,150,255,0.3)]"
            : "rounded-bl-md border border-ocean/14 bg-canvas/78 text-slate-100 backdrop-blur-xl shadow-[0_18px_36px_rgba(3,8,22,0.44),0_0_10px_rgba(0,150,255,0.14)]",
        ].join(" ")}
      >
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em]">
          <span className={isUser ? "text-ink/70" : "text-slate-400"}>
            {isUser ? "You" : "AICES"}
          </span>

          {!isUser && message.level ? (
            <span className="rounded-full border border-ocean/15 bg-ocean/10 px-2 py-1 text-[11px] font-semibold tracking-normal text-ocean">
              {levelLabel(message.level)}
            </span>
          ) : null}
        </div>

        {isUser ? (
          <p className="whitespace-pre-wrap text-[15px] leading-7 text-ink">{message.text}</p>
        ) : (
          <div className="space-y-4">{renderRichContent(message.text)}</div>
        )}

        {!isUser && message.topic ? (
          <p className="mt-4 text-xs font-medium text-slate-500">
            Topic: {formatTopicLabel(message.topic, { fallback: "Topic", strict: true })}
          </p>
        ) : null}
      </div>
    </div>
  );
}
