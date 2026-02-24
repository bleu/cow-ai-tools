import type React from "react";

import { Avatar, AvatarImage, BoringAvatar } from "@/components/ui/avatar";

const isCow = typeof process !== "undefined" && process.env.NEXT_PUBLIC_BRAND === "cow";
const isAssistant = (n: string) => n === "Optimism GovGPT" || n === "CoW AI" || n === "CoW Protocol";

export interface MessageAvatarProps {
  name: string;
}

export const MessageAvatar: React.FC<MessageAvatarProps> = ({ name }) => {
  if (isAssistant(name)) {
    if (isCow) {
      return (
        <Avatar className="flex justify-center items-center mt-1 shrink-0 w-10 h-10">
          <AvatarImage
            src="/cow-ai-logo.png"
            alt="CoW AI"
            width={40}
            height={40}
            className="w-10 h-10 rounded-full object-cover"
          />
        </Avatar>
      );
    }
    return (
      <Avatar className="flex justify-center items-center mt-1">
        <AvatarImage
          src="/op-logo.png"
          alt="Optimism GovGPT"
          width={6}
          height={6}
          className="w-10 h-10"
        />
      </Avatar>
    );
  }
  return (
    <Avatar className="flex justify-center items-center mt-1">
      <BoringAvatar name={name} />
    </Avatar>
  );
};
