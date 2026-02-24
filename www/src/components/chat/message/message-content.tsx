import type React from "react";
import { useState } from "react";

import type { Data, Message } from "@/app/data";
import { FormattedMessage } from "@/components/ui/formatted-message";

const isCow = typeof process !== "undefined" && process.env.NEXT_PUBLIC_BRAND === "cow";
import { LoadingIndicator } from "@/components/ui/loading-indicator";
import { formatAnswerWithReferences, normalizeAnswerLineBreaks } from "@/lib/chat-utils";
import { cn } from "@/lib/utils";

import { useChatStore } from "@/states/use-chat-state";
import { EditableMessage } from "./editable-message";
import { MessageActions } from "./message-actions";

export interface MessageContentProps {
  message: Message;
  isEditable: boolean;
  setIsEditable: (isEditable: boolean) => void;
}
export const MessageContent: React.FC<MessageContentProps> = ({
  message,
  isEditable,
  setIsEditable,
}) => {
  const [editMessageContent, setEditMessageContent] = useState(
    message.data.answer,
  );
  const sendMessage = useChatStore.use.sendMessage();
  const loadingMessageId = useChatStore.use.loadingMessageId();

  const handleOnSendEditMessage = () => {
    const editedMessage: Message = {
      ...message,
      data: { ...message.data, answer: editMessageContent.trim() },
    };
    sendMessage(editedMessage);
    setIsEditable(false);
  };

  const messageContent = (data: Data) => {
    if (data.url_supporting?.length === 0) return normalizeAnswerLineBreaks(data.answer ?? "");
    return formatAnswerWithReferences(data);
  };

  if (loadingMessageId === message.id) {
    return <LoadingIndicator />;
  }

  if (isEditable && message.name !== "Optimism GovGPT" && message.name !== "CoW AI") {
    return (
      <EditableMessage
        editMessageContent={editMessageContent}
        setEditMessageContent={setEditMessageContent}
        handleOnSendEditMessage={handleOnSendEditMessage}
        setIsEditable={setIsEditable}
      />
    );
  }

  return (
    <div
      className={cn(
        "min-w-0 md:max-w-[70%]",
        isCow && "cow-chat-message",
        message.name !== "Optimism GovGPT" &&
          message.name !== "CoW AI" &&
          "bg-chat-primary rounded-lg p-4 my-4 max-w-[70%]",
      )}
    >
      <FormattedMessage content={messageContent(message.data)} />
      <MessageActions message={message} />
    </div>
  );
};
