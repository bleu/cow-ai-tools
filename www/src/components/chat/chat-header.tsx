"use client";

import { useChatStore } from "@/states/use-chat-state";
import { FilePlusIcon } from "lucide-react";
import Image from "next/image";
import { Button } from "../ui/button";
import { ChatMobileSidebar } from "./chat-mobile-sidebar";

const brandHoverClass = "hover:bg-cow/15";

export function ChatHeader() {
  const { addChat } = useChatStore();

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6">
      <div className="md:hidden flex-1">
        <ChatMobileSidebar />
      </div>
      <div>
        <div className="flex flex-1 gap-x-2 items-center">
          <Image
            src="/cow-ai-logo.png"
            alt="CoW AI"
            width={40}
            height={40}
            className="h-8 w-8 md:h-9 md:w-9 rounded-full object-cover"
          />
          <span className="text-base font-semibold text-cow">CoW AI</span>
        </div>
      </div>
      <div className="flex flex-1 justify-end  md:hidden">
        <Button
          className={`p-2 ${brandHoverClass} ml-auto`}
          variant="link"
          onClick={addChat}
        >
          <FilePlusIcon color="#33D0FF" className="w-6 h-6" />
        </Button>
      </div>
    </header>
  );
}
