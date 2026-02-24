import type { Data, Message } from "@/app/data";

import { format, isValid } from "date-fns";

export interface ChatData {
  id: string;
  name: string;
  messages: Message[];
  timestamp: number;
}

export const getChatName = (messages: Message[]): string => {
  const firstQuestion = messages?.find(
    (m) => m.name !== "Optimism GovGPT" && m.name !== "CoW AI",
  );
  if (firstQuestion) {
    const messageContent = firstQuestion.data.answer;
    return (
      messageContent?.slice(0, 30) + (messageContent?.length > 30 ? "..." : "")
    );
  }
  return "New Chat";
};

export const getValidTimestamp = (timestamp: number | undefined): number => {
  if (timestamp && !Number.isNaN(timestamp)) {
    return timestamp;
  }
  return Date.now();
};

export const saveChatsToLocalStorage = (chats: ChatData[]): void => {
  const nonEmptyChats = chats.filter((chat) => chat.messages.length > 0);
  const chatHistory = nonEmptyChats.reduce(
    (acc, chat) => {
      acc[`chat-${chat.id}`] = chat.messages;
      return acc;
    },
    {} as Record<string, Message[]>,
  );
  localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
};

export const loadChatsFromLocalStorage = (): ChatData[] => {
  const savedHistory = localStorage.getItem("chatHistory");
  if (savedHistory) {
    const parsedHistory = JSON.parse(savedHistory);
    return Object.entries(parsedHistory)
      .map(([name, messages]) => ({
        id: name,
        name: getChatName(messages as Message[]),
        messages: messages as Message[],
        timestamp: getValidTimestamp((messages as Message[])[0]?.timestamp),
      }))
      .sort((a, b) => b.timestamp - a.timestamp);
  }
  return [];
};

export const removeChatFromLocalStorage = (chatId: string): void => {
  const savedHistory = localStorage.getItem("chatHistory");
  if (savedHistory) {
    const parsedHistory = JSON.parse(savedHistory);
    delete parsedHistory[chatId];
    localStorage.setItem("chatHistory", JSON.stringify(parsedHistory));
  }
};

export function generateChatParams(prefix: string): ChatData {
  const now = Date.now();

  return {
    id: `${prefix}-${Date.now()}`,
    name: "New Chat",
    messages: [],
    timestamp: now,
  };
}
export function generateMessageParams(
  chatId: string,
  data: { answer: string; url_supporting: string[] },
  name = "anonymous",
): Message {
  const now = Date.now();

  return {
    id: `${chatId}-message-${name}-${now}`,
    name,
    data,
    timestamp: now,
  };
}
export function generateMessagesMemory(
  messages: Message[],
): { name: string; message: string }[] {
  return messages.map((message) => {
    return {
      name:
      message.name === "Optimism GovGPT" || message.name === "CoW AI"
        ? "chat"
        : "user",
      message: message.data.answer,
    };
  });
}

export const addNewChat = (chats: ChatData[]): ChatData[] => {
  const newChat = generateChatParams("chat");
  return [newChat, ...chats];
};

export const formatDate = (timestamp: number) => {
  const date = new Date(timestamp);
  if (isValid(date)) {
    return format(date, "MMM d, yyyy h:mm a");
  }
  return "Invalid date";
};

const COW_DOCS_BASE = "https://docs.cow.fi";

/** Normalize docs.cow.fi path: lowercase, ow->cow typo, underscores->hyphens (live site uses hyphens, e.g. vault-relayer). */
function normalizeDocsCowFiUrl(url: string): string {
  try {
    const parsed = new URL(url);
    if (parsed.origin === "https://docs.cow.fi" || parsed.hostname === "docs.cow.fi") {
      let path = parsed.pathname
        .split("/")
        .filter(Boolean)
        .map((p) => p.toLowerCase().replace(/_/g, "-"))
        .join("/");
      path = path.replace(/^ow-protocol\//, "cow-protocol/").replace(/\/ow-protocol\//g, "/cow-protocol/");
      return `${COW_DOCS_BASE}/${path}`.replace(/\/+$/, "") || COW_DOCS_BASE;
    }
  } catch {
    // not a valid URL
  }
  return url;
}

const CODE_BLOCK_RE = /```[\s\S]*?```/g;
const MARKDOWN_LINE_BREAK = /[ \t]{2,}\r?\n/g;
const HTML_BR = /<br\s*\/?>/gi;
const MULTI_SPACE = /[ \t]+/g;

/**
 * Collapses all newlines to spaces outside code blocks so prose never breaks mid-sentence.
 * The LLM often outputs \n\n between every phrase (e.g. "To register\n\nappData\n\nand link"),
 * which would render as many <p> tags; we merge everything into one paragraph per "segment" between code blocks.
 */
export function normalizeAnswerLineBreaks(text: string): string {
  if (!text || typeof text !== "string") return text;
  let t = text.replace(MARKDOWN_LINE_BREAK, " ").replace(HTML_BR, " ");
  if (!/\n/.test(t) && t === text) return text;
  const anyLineBreak = /\r\n|\r|\n|\u2028|\u2029/g;
  function processPart(part: string): string {
    // Collapse ALL newlines (single and double) to space so we get one paragraph, no orphan lines
    const oneLine = part.replace(anyLineBreak, " ").replace(MULTI_SPACE, " ").trim();
    return oneLine || "";
  }
  const parts: string[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  CODE_BLOCK_RE.lastIndex = 0;
  while ((m = CODE_BLOCK_RE.exec(t)) !== null) {
    parts.push(processPart(t.slice(last, m.index)));
    parts.push(m[0]);
    last = m.index + m[0].length;
  }
  parts.push(processPart(t.slice(last)));
  return parts.join("");
}

const CODE_BLOCK_RE_SEGMENTS = /```(\w*)\n?([\s\S]*?)```/g;

export type ContentSegment = { type: "prose"; text: string } | { type: "code"; lang: string; text: string };

/**
 * Splits normalized content into prose and code segments. Use with custom renderer so no Markdown parser can add line breaks.
 */
export function getContentSegments(normalized: string): ContentSegment[] {
  const segments: ContentSegment[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  CODE_BLOCK_RE_SEGMENTS.lastIndex = 0;
  while ((m = CODE_BLOCK_RE_SEGMENTS.exec(normalized)) !== null) {
    const prose = normalized.slice(last, m.index).trim();
    if (prose) segments.push({ type: "prose", text: prose });
    segments.push({ type: "code", lang: m[1] || "", text: m[2].trim() });
    last = m.index + m[0].length;
  }
  const tail = normalized.slice(last).trim();
  if (tail) segments.push({ type: "prose", text: tail });
  return segments;
}

/** Ensure URL is absolute so reference links don't open as same-origin (page not found). */
function toAbsoluteUrl(url: string): string {
  const u = (url || "").trim();
  if (!u) return "";
  if (u.startsWith("http://") || u.startsWith("https://")) {
    return normalizeDocsCowFiUrl(u);
  }
  const path = u.startsWith("/") ? u : `/${u}`;
  const full = `${COW_DOCS_BASE}${path}`;
  return normalizeDocsCowFiUrl(full);
}

export const formatAnswerWithReferences = (data: Data): string => {
  const { answer, url_supporting } = data;

  if (!answer) return "An error occurred while fetching the answer.";

  const normalized = normalizeAnswerLineBreaks(answer.trim());

  const validUrls = (url_supporting || []).filter(Boolean).map(toAbsoluteUrl).filter(Boolean);
  const references = validUrls
    .map((url, index) => `<a href="${url}" target="_blank" rel="noopener noreferrer">[${index + 1}]</a>`)
    .join(" ");

  if (validUrls.length === 0) {
    return normalized;
  }

  return `${normalized}\n\nReferences: ${references}`;
};
