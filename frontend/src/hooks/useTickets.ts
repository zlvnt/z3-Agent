"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { Ticket, TicketStats } from "@/lib/types";

export function useTickets(statusFilter?: string) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [listData, statsData] = await Promise.all([
        api.listTickets({ status: statusFilter, page, page_size: 20 }),
        api.getTicketStats(),
      ]);
      setTickets(listData.tickets);
      setTotal(listData.total);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch tickets");
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, page]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { tickets, stats, total, page, setPage, isLoading, error, refresh };
}
