"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { MessageMetadata } from "./MessageMetadata";
import type { ChatMessage } from "@/lib/types";

export function MessageBubble({
  message,
  isSelected,
  onSelect,
}: {
  message: ChatMessage;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const [showMeta, setShowMeta] = useState(false);
  const isUser = message.role === "user";

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-2.5 cursor-pointer transition-colors",
          isUser
            ? "bg-blue-600 text-white"
            : cn(
                "bg-zinc-800 text-zinc-100",
                isSelected && "ring-1 ring-zinc-600",
              ),
        )}
        onClick={() => {
          if (!isUser) {
            onSelect();
            setShowMeta(!showMeta);
          }
        }}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {!isUser && message.metadata && showMeta && (
          <MessageMetadata data={message.metadata} />
        )}
        {!isUser && message.metadata && !showMeta && (
          <p className="text-[10px] text-zinc-500 mt-1">Click for details</p>
        )}
      </div>
    </div>
  );
}
