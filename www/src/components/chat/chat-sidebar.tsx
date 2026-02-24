"use client";

import { cn } from "@/lib/utils";
import { useChatStore } from "@/states/use-chat-state";
import { FilePlusIcon, TrashIcon } from "@radix-ui/react-icons";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import type React from "react";
import { Fragment, useEffect, useState } from "react";
import { Button } from "../ui/button";

const isCow = typeof process !== "undefined" && process.env.NEXT_PUBLIC_BRAND === "cow";
const brandColor = isCow ? "#33D0FF" : "#FF0420";
const brandHover = isCow ? "hover:bg-cow/15" : "hover:bg-optimism/15";
const brandText = isCow ? "hover:text-cow text-cow" : "hover:text-optimism text-optimism";
const brandBg = isCow ? "bg-cow/15" : "bg-optimism/15";

export default function ChatSidebar() {
  const { chats, selectedChatId, setSelectedChatId, addChat, removeChat } =
    useChatStore();
  const [chatCount, setChatCount] = useState(0);
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setChatCount(Object.values(chats).length);
  }, [chats]);
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleRemoveChat = (
    e: React.MouseEvent<HTMLButtonElement, MouseEvent>,
    id: string,
  ) => {
    e.stopPropagation();
    removeChat(id);
  };

  return (
    <aside
      className={`w-72 min-w-0 flex flex-col h-full ${isCow ? "bg-cow-surface" : "bg-chat-primary"}`}
    >
      <div className="flex items-center justify-between p-4 mt-6 md:mt-0">
        <h2 className="font-bold text-lg">
          Chats ({chatCount})
        </h2>
        <Button
          className={cn("p-2", brandHover)}
          variant="link"
          onClick={addChat}
        >
          <FilePlusIcon color={brandColor} className="w-6 h-6" />
        </Button>
      </div>
      <div className="h-screen overflow-y-auto px-4">
        <div className="space-y-3 w-full flex-col">
          {mounted &&
          Object.values(chats).map((chat) => (
            <Fragment key={chat.id}>
              <div
                className={cn(
                  "flex group items-center justify-between px-2 py-1 w-full rounded-lg font-medium text-sm",
                  isCow ? "text-chat-secondary hover:bg-cow/10" : "text-chat-secondary hover:text-optimism",
                  isCow && selectedChatId === chat.id && "bg-cow/10",
                  !isCow && selectedChatId === chat.id && `${brandText} ${brandBg}`,
                )}
              >
                <button
                  type="button"
                  className="flex-grow min-w-0 text-left overflow-hidden"
                  onClick={() => setSelectedChatId(chat.id)}
                  title={chat.messages[0]?.data?.answer || "New chat"}
                >
                  <span className="block text-ellipsis line-clamp-2 break-words">
                    {chat.messages[0]?.data?.answer || "New chat"}
                  </span>
                </button>
                <Button
                  className={cn("p-1 ml-1", brandHover)}
                  size="sm"
                  variant="link"
                  onClick={(e) => handleRemoveChat(e, chat.id)}
                >
                  <TrashIcon
                    className={cn(
                      "group-hover:opacity-100 opacity-0 w-5 h-5",
                      isCow ? "text-chat-secondary" : "text-optimism",
                      selectedChatId === chat.id && "opacity-100",
                    )}
                  />
                </Button>
              </div>
            </Fragment>
          ))}
        </div>
      </div>
      <hr className="border-t border-gray-200 my-4 mx-4" />
      <div className="px-4">
        <h2 className="mb-2 font-semibold">
          {isCow ? "CoW AI" : "Catch up on OP Governance"}
        </h2>
        <Link
          href={isCow ? "https://docs.cow.fi" : "/forum"}
          target="_blank"
          className={cn(
            "flex items-center gap-3 rounded-lg py-2 transition-all hover:bg-gray-100 text-gray-700 text-sm mb-12",
          )}
        >
          {isCow ? "Docs & Order Book API" : "Explore GovSummarizer"}
          <ExternalLink className="h-5 w-5 md:h-4 md:w-4" />
        </Link>
      </div>
    </aside>
  );
}
