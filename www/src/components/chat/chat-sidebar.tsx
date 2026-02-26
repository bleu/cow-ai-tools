"use client";

import { cn } from "@/lib/utils";
import { useChatStore } from "@/states/use-chat-state";
import { FilePlusIcon, TrashIcon } from "@radix-ui/react-icons";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import type React from "react";
import { Fragment, useEffect, useState } from "react";
import { Button } from "../ui/button";

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
    <aside className="w-72 min-w-0 flex flex-col h-full bg-cow-surface">
      <div className="flex items-center justify-between p-4 mt-6 md:mt-0">
        <h2 className="font-bold text-lg">
          Chats ({chatCount})
        </h2>
        <Button
          className={cn("p-2", "hover:bg-cow/15")}
          variant="link"
          onClick={addChat}
        >
          <FilePlusIcon color="#33D0FF" className="w-6 h-6" />
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
                  "text-chat-secondary hover:bg-cow/10",
                  selectedChatId === chat.id && "bg-cow/10",
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
                  className={cn("p-1 ml-1", "hover:bg-cow/15")}
                  size="sm"
                  variant="link"
                  onClick={(e) => handleRemoveChat(e, chat.id)}
                >
                  <TrashIcon
                    className={cn(
                      "group-hover:opacity-100 opacity-0 w-5 h-5 text-chat-secondary",
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
        <h2 className="mb-2 font-semibold">CoW AI</h2>
        <Link
          href="https://docs.cow.fi"
          target="_blank"
          className={cn(
            "flex items-center gap-3 rounded-lg py-2 transition-all hover:bg-gray-100 text-gray-700 text-sm mb-12",
          )}
        >
          Docs & Order Book API
          <ExternalLink className="h-5 w-5 md:h-4 md:w-4" />
        </Link>
      </div>
    </aside>
  );
}
