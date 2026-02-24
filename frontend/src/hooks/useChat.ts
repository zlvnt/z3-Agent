"use client";

import { useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";
import { generateId } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";

const STORAGE_PREFIX = "z3_chat_";

function loadMessages(sessionId: string): ChatMessage[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(`${STORAGE_PREFIX}${sessionId}`);
  return raw ? JSON.parse(raw) : [];
}

function saveMessages(sessionId: string, messages: ChatMessage[]) {
  localStorage.setItem(`${STORAGE_PREFIX}${sessionId}`, JSON.stringify(messages));
}

function loadSessions(): string[] {
  if (typeof window === "undefined") return ["default"];
  const raw = localStorage.getItem("z3_sessions");
  return raw ? JSON.parse(raw) : ["default"];
}

function saveSessions(sessions: string[]) {
  localStorage.setItem("z3_sessions", JSON.stringify(sessions));
}

export function useChat() {
  const [sessions, setSessions] = useState<string[]>(() => loadSessions());
  const [sessionId, setSessionId] = useState<string>(sessions[0] || "default");
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages(sessionId));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync messages when session changes
  useEffect(() => {
    setMessages(loadMessages(sessionId));
  }, [sessionId]);

  // Persist messages
  useEffect(() => {
    saveMessages(sessionId, messages);
  }, [sessionId, messages]);

  const sendMessage = useCallback(
    async (text: string) => {
      const userMsg: ChatMessage = {
        id: generateId(),
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setError(null);

      try {
        const res = await api.sendMessage({
          message: text,
          session_id: sessionId,
        });
        const botMsg: ChatMessage = {
          id: generateId(),
          role: "assistant",
          content: res.reply,
          timestamp: res.timestamp,
          metadata: res,
        };
        setMessages((prev) => [...prev, botMsg]);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId],
  );

  const createSession = useCallback(() => {
    const id = `session_${generateId()}`;
    setSessions((prev) => {
      const next = [...prev, id];
      saveSessions(next);
      return next;
    });
    setSessionId(id);
    return id;
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    saveMessages(sessionId, []);
  }, [sessionId]);

  const switchSession = useCallback((id: string) => {
    setSessionId(id);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    sessions,
    sendMessage,
    clearMessages,
    createSession,
    switchSession,
  };
}
