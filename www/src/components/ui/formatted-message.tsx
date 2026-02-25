import React from "react";
import {
  normalizeAnswerLineBreaks,
  getContentSegments,
} from "@/lib/chat-utils";

interface FormattedMessageProps {
  content: string;
}

const LINK_RE = /(<a\s+href="([^"]*)"[^>]*>([\s\S]*?)<\/a>)/gi;
const INLINE_CODE_RE = /`([^`]+)`/g;
const BOLD_RE = /\*\*([^*]+)\*\*/g;

function renderInlineCodeBoldAndText(str: string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  let last = 0;
  let key = 0;
  let match: RegExpExecArray | null;
  INLINE_CODE_RE.lastIndex = 0;
  while ((match = INLINE_CODE_RE.exec(str)) !== null) {
    if (match.index > last) {
      out.push(...renderBoldAndText(str.slice(last, match.index), (k) => `bold-${key}-${k}`));
    }
    out.push(
      <code
        key={key++}
        className="rounded bg-muted px-1.5 py-0.5 font-mono text-sm"
      >
        {match[1]}
      </code>
    );
    last = match.index + match[0].length;
  }
  if (last < str.length) {
    out.push(...renderBoldAndText(str.slice(last), (k) => `bold-${key}-${k}`));
  }
  return out;
}

function renderBoldAndText(str: string, keyFn: (k: number) => string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  let last = 0;
  let key = 0;
  let boldMatch: RegExpExecArray | null;
  BOLD_RE.lastIndex = 0;
  while ((boldMatch = BOLD_RE.exec(str)) !== null) {
    if (boldMatch.index > last) out.push(str.slice(last, boldMatch.index));
    out.push(<strong key={keyFn(key++)}>{boldMatch[1]}</strong>);
    last = boldMatch.index + boldMatch[0].length;
  }
  if (last < str.length) out.push(str.slice(last));
  return out;
}

function renderProse(text: string): React.ReactNode {
  const parts = text.split(LINK_RE);
  const nodes: React.ReactNode[] = [];
  let skip = 0;
  for (let i = 0; i < parts.length; i++) {
    if (skip > 0) {
      skip--;
      continue;
    }
    const p = parts[i];
    if (!p) continue;
    if (p.startsWith("<a ")) {
      const href = parts[i + 1] ?? "#";
      const linkText = parts[i + 2] ?? "";
      nodes.push(
        <a
          key={`link-${i}`}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500"
        >
          {linkText}
        </a>
      );
      skip = 2;
      continue;
    }
    nodes.push(
      <React.Fragment key={i}>{renderInlineCodeBoldAndText(p)}</React.Fragment>
    );
  }
  return nodes;
}

/**
 * Renders the chat message without using a Markdown parser, so the parser cannot
 * introduce line breaks. Prose is one block per segment; code blocks preserved.
 */
export const FormattedMessage: React.FC<FormattedMessageProps> = ({
  content,
}) => {
  const normalized = normalizeAnswerLineBreaks(content);
  const segments = getContentSegments(normalized);

  return (
    <div className="whitespace-normal">
      {segments.map((seg, i) =>
        seg.type === "code" ? (
          <pre
            key={i}
            className="min-w-0 overflow-x-auto overflow-y-hidden rounded-md bg-muted p-3 text-sm max-w-full whitespace-pre my-3"
          >
            <code className="block min-w-0 max-w-full overflow-x-auto whitespace-pre font-mono text-sm">
              {seg.text}
            </code>
          </pre>
        ) : (
          <p key={i} className="whitespace-normal my-2 first:mt-0 last:mb-0">
            {renderProse(seg.text)}
          </p>
        )
      )}
    </div>
  );
};
