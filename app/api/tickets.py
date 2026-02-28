"""
Ticket management API endpoints.

CRUD operations for HITL escalation tickets.
"""

from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# --- Models ---

class TicketResponse(BaseModel):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: str
    channel: str
    session_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    chat_id: Optional[str] = None
    escalation_stage: str
    escalation_reason: str
    original_query: str
    history_snippet: Optional[str] = None
    quality_score: Optional[float] = None
    assigned_to: Optional[str] = None
    resolution_note: Optional[str] = None
    resolved_at: Optional[str] = None


class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int
    page: int
    page_size: int


class TicketUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|closed)$")
    assigned_to: Optional[str] = Field(None, max_length=100)
    resolution_note: Optional[str] = Field(None, max_length=2000)


class TicketStatsResponse(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    avg_resolution_time_hours: Optional[float] = None


# --- Endpoints ---

@router.get("/tickets", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[str] = Query(None, pattern="^(open|in_progress|resolved|closed)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List tickets with optional status filter and pagination."""
    from app.services.ticket_service import get_ticket_service

    service = get_ticket_service()
    offset = (page - 1) * page_size
    result = service.list_tickets(status=status, limit=page_size, offset=offset)

    return TicketListResponse(
        tickets=[TicketResponse(**t) for t in result["tickets"]],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get("/tickets/stats", response_model=TicketStatsResponse)
async def ticket_stats():
    """Get ticket statistics."""
    from app.services.ticket_service import get_ticket_service

    service = get_ticket_service()
    stats = service.get_stats()
    return TicketStatsResponse(**stats)


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """Get single ticket by ID."""
    from app.services.ticket_service import get_ticket_service

    service = get_ticket_service()
    ticket = service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketResponse(**ticket)


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(ticket_id: str, req: TicketUpdateRequest):
    """Update ticket status, assignment, or resolution."""
    from app.services.ticket_service import get_ticket_service

    service = get_ticket_service()

    existing = service.get_ticket(ticket_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ticket not found")

    updated = service.update_ticket(
        ticket_id=ticket_id,
        status=req.status,
        assigned_to=req.assigned_to,
        resolution_note=req.resolution_note,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update ticket")

    return TicketResponse(**updated)
