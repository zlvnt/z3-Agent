"use client";

import { useRef, useEffect, useState } from "react";
import { useChat } from "@/hooks/useChat";
import { ChatInput } from "./ChatInput";
import { MessageBubble } from "./MessageBubble";
import { SessionSelector } from "./SessionSelector";
import { MessageMetadata } from "./MessageMetadata";
import { Card } from "@/components/ui/Card";
import type { ChatMessage } from "@/lib/types";

export function ChatContainer() {
  const {
    messages,
    isLoading,
    error,
    sessionId,
    sessions,
    sendMessage,
    clearMessages,
    createSession,
    switchSession,
  } = useChat();

  const [selectedMsg, setSelectedMsg] = useState<ChatMessage | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-full">
      {/* Session sidebar */}
      <SessionSelector
        sessions={sessions}
        current={sessionId}
        onSelect={switchSession}
        onCreate={createSession}
        onClear={clearMessages}
      />

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-zinc-500">
                <p className="text-lg mb-1">Start a conversation</p>
                <p className="text-sm">Send a message to test the agent</p>
              </div>
            </div>
          )}
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isSelected={selectedMsg?.id === msg.id}
              onSelect={() => setSelectedMsg(msg)}
            />
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-zinc-800 rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
              </div>
            </div>
          )}
          {error && (
            <div className="text-center text-sm text-red-400 bg-red-400/10 rounded-lg p-2">
              {error}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>

      {/* Metadata panel */}
      <div className="w-80 bg-zinc-900 border-l border-zinc-800 overflow-y-auto p-4">
        <h3 className="text-sm font-medium text-zinc-400 mb-3">Response Details</h3>
        {selectedMsg?.metadata ? (
          <Card>
            <MessageMetadata data={selectedMsg.metadata} />
          </Card>
        ) : (
          <p className="text-xs text-zinc-600">
            Click a bot message to view metadata
          </p>
        )}
      </div>
    </div>
  );
}
