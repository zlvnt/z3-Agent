"""
HITL Ticket Service - Persistence layer for escalation tickets.

Uses the same database connection pattern as TelegramMemory:
- PostgreSQL in production (via DATABASE_URL)
- SQLite for local development (fallback)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import create_engine, text


class TicketService:
    def __init__(self):
        from app.config import settings

        database_url = getattr(settings, 'DATABASE_URL', None)
        if database_url:
            self.connection_string = database_url
            self.db_type = "postgresql"
        else:
            db_path = getattr(settings, 'TELEGRAM_DB_PATH', 'data/telegram_memory.db')
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.connection_string = f"sqlite:///{db_path}"
            self.db_type = "sqlite"

        self.engine = create_engine(self.connection_string)
        self._ensure_table()
        print(f"🎫 TicketService initialized: {self.db_type}")

    def _ensure_table(self):
        """Auto-create tickets table if not exists."""
        ddl = text("""
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                channel TEXT NOT NULL DEFAULT 'telegram',
                session_id TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                chat_id TEXT,
                escalation_stage TEXT NOT NULL,
                escalation_reason TEXT NOT NULL,
                original_query TEXT NOT NULL,
                history_snippet TEXT,
                quality_score REAL,
                assigned_to TEXT,
                resolution_note TEXT,
                resolved_at TIMESTAMP
            )
        """)
        with self.engine.connect() as conn:
            conn.execute(ddl)
            conn.commit()

    def create_ticket(
        self,
        channel: str,
        session_id: str,
        escalation_stage: str,
        escalation_reason: str,
        original_query: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        chat_id: Optional[str] = None,
        history_snippet: Optional[str] = None,
        quality_score: Optional[float] = None,
    ) -> Optional[str]:
        """Create a ticket. Returns ticket ID or None on failure."""
        try:
            ticket_id = f"tkt_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)

            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO tickets (
                            id, created_at, updated_at, status, channel, session_id,
                            user_id, username, chat_id, escalation_stage,
                            escalation_reason, original_query, history_snippet, quality_score
                        ) VALUES (
                            :id, :created_at, :updated_at, :status, :channel, :session_id,
                            :user_id, :username, :chat_id, :escalation_stage,
                            :escalation_reason, :original_query, :history_snippet, :quality_score
                        )
                    """),
                    {
                        "id": ticket_id,
                        "created_at": now,
                        "updated_at": now,
                        "status": "open",
                        "channel": channel,
                        "session_id": session_id,
                        "user_id": user_id,
                        "username": username,
                        "chat_id": chat_id,
                        "escalation_stage": escalation_stage,
                        "escalation_reason": escalation_reason,
                        "original_query": original_query,
                        "history_snippet": history_snippet,
                        "quality_score": quality_score,
                    },
                )
                conn.commit()

            return ticket_id
        except Exception as e:
            print(f"❌ Ticket creation failed: {e}")
            return None

    def list_tickets(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List tickets with optional status filter and pagination."""
        try:
            with self.engine.connect() as conn:
                # Count
                if status:
                    count_row = conn.execute(
                        text("SELECT COUNT(*) FROM tickets WHERE status = :status"),
                        {"status": status},
                    ).fetchone()
                else:
                    count_row = conn.execute(
                        text("SELECT COUNT(*) FROM tickets")
                    ).fetchone()
                total = count_row[0] if count_row else 0

                # Query
                if status:
                    rows = conn.execute(
                        text("""
                            SELECT * FROM tickets WHERE status = :status
                            ORDER BY created_at DESC LIMIT :limit OFFSET :offset
                        """),
                        {"status": status, "limit": limit, "offset": offset},
                    ).fetchall()
                else:
                    rows = conn.execute(
                        text("""
                            SELECT * FROM tickets
                            ORDER BY created_at DESC LIMIT :limit OFFSET :offset
                        """),
                        {"limit": limit, "offset": offset},
                    ).fetchall()

                tickets = [self._row_to_dict(row) for row in rows]
                return {"tickets": tickets, "total": total}
        except Exception as e:
            print(f"❌ List tickets failed: {e}")
            return {"tickets": [], "total": 0}

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get single ticket by ID."""
        try:
            with self.engine.connect() as conn:
                row = conn.execute(
                    text("SELECT * FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                ).fetchone()
                return self._row_to_dict(row) if row else None
        except Exception as e:
            print(f"❌ Get ticket failed: {e}")
            return None

    def update_ticket(
        self,
        ticket_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        resolution_note: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update ticket fields. Returns updated ticket or None."""
        try:
            updates = []
            params: Dict[str, Any] = {"id": ticket_id}

            if status is not None:
                updates.append("status = :status")
                params["status"] = status
                if status in ("resolved", "closed"):
                    updates.append("resolved_at = :resolved_at")
                    params["resolved_at"] = datetime.now(timezone.utc)

            if assigned_to is not None:
                updates.append("assigned_to = :assigned_to")
                params["assigned_to"] = assigned_to

            if resolution_note is not None:
                updates.append("resolution_note = :resolution_note")
                params["resolution_note"] = resolution_note

            if not updates:
                return self.get_ticket(ticket_id)

            updates.append("updated_at = :updated_at")
            params["updated_at"] = datetime.now(timezone.utc)

            query = f"UPDATE tickets SET {', '.join(updates)} WHERE id = :id"

            with self.engine.connect() as conn:
                conn.execute(text(query), params)
                conn.commit()

            return self.get_ticket(ticket_id)
        except Exception as e:
            print(f"❌ Update ticket failed: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get ticket statistics."""
        try:
            with self.engine.connect() as conn:
                # Counts by status
                rows = conn.execute(
                    text("SELECT status, COUNT(*) as cnt FROM tickets GROUP BY status")
                ).fetchall()

                counts = {"open": 0, "in_progress": 0, "resolved": 0, "closed": 0}
                total = 0
                for row in rows:
                    counts[row[0]] = row[1]
                    total += row[1]

                # Avg resolution time
                avg_hours = None
                resolved_rows = conn.execute(
                    text("""
                        SELECT created_at, resolved_at FROM tickets
                        WHERE resolved_at IS NOT NULL
                    """)
                ).fetchall()

                if resolved_rows:
                    durations = []
                    for row in resolved_rows:
                        created = row[0] if isinstance(row[0], datetime) else datetime.fromisoformat(str(row[0]))
                        resolved = row[1] if isinstance(row[1], datetime) else datetime.fromisoformat(str(row[1]))
                        durations.append((resolved - created).total_seconds() / 3600)
                    if durations:
                        avg_hours = round(sum(durations) / len(durations), 2)

                return {
                    "total": total,
                    "open": counts["open"],
                    "in_progress": counts["in_progress"],
                    "resolved": counts["resolved"],
                    "closed": counts["closed"],
                    "avg_resolution_time_hours": avg_hours,
                }
        except Exception as e:
            print(f"❌ Get stats failed: {e}")
            return {"total": 0, "open": 0, "in_progress": 0, "resolved": 0, "closed": 0, "avg_resolution_time_hours": None}

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to dict."""
        keys = [
            "id", "created_at", "updated_at", "status", "channel", "session_id",
            "user_id", "username", "chat_id", "escalation_stage",
            "escalation_reason", "original_query", "history_snippet",
            "quality_score", "assigned_to", "resolution_note", "resolved_at",
        ]
        d = {}
        for i, key in enumerate(keys):
            val = row[i]
            if isinstance(val, datetime):
                val = val.isoformat()
            d[key] = val
        return d


# Singleton
_ticket_service = None


def get_ticket_service() -> TicketService:
    """Get global TicketService instance."""
    global _ticket_service
    if _ticket_service is None:
        _ticket_service = TicketService()
    return _ticket_service
