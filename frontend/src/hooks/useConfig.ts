"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { AgentConfig } from "@/lib/types";

export function useConfig() {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getConfig()
      .then((data) => {
        setConfig(data);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to fetch config");
      })
      .finally(() => setIsLoading(false));
  }, []);

  return { config, isLoading, error };
}
