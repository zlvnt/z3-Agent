"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";

export function useHealth(intervalMs = 30000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOnline, setIsOnline] = useState(false);

  const check = useCallback(async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
      setIsOnline(true);
    } catch {
      setIsOnline(false);
    }
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, intervalMs);
    return () => clearInterval(id);
  }, [check, intervalMs]);

  return { health, isOnline };
}
