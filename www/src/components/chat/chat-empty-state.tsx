import Image from "next/image";
import type React from "react";

import useMobileStore from "@/states/use-mobile-state";
import { Button } from "../ui/button";
import { suggestions } from "./chat-suggestions";

const isCow = typeof process !== "undefined" && process.env.NEXT_PUBLIC_BRAND === "cow";

export function ChatEmptyState({
  onSuggestionClick,
}: {
  onSuggestionClick: (suggestion: string) => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-4">
      <div className="mb-8">
        {isCow ? (
          <Image
            src="/cow-ai-logo.png"
            alt="CoW AI"
            width={100}
            height={100}
            className="w-[75px] md:w-[100px] h-[75px] md:h-[100px] rounded-full object-cover"
          />
        ) : (
          <Image
            src="/op-logo.svg"
            alt="Optimism logo"
            width={75}
            height={75}
            className="w-[75px] md:w-[100px]"
          />
        )}
      </div>
      <h2 className="text-lg md:text-2xl font-bold mb-4 text-center text-chat-secondary">
        {isCow ? "CoW AI — ask about the Order Book API" : "How can I help you today?"}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
        {suggestions.map((suggestion) => (
          <Button
            key={suggestion.label}
            variant="outline"
            className="flex items-center justify-start gap-2 h-auto py-3 px-4 text-sm md:text-base"
            onClick={() => onSuggestionClick(suggestion.value)}
          >
            {suggestion.icon}
            <span>{suggestion.label}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}
