"""Pydantic schemas for task lifecycle management and SSE streaming.

Implements task models for API endpoints specified in 02_DESIGN_DOC.md §13 & §16.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    """Payload to submit a new agent execution task."""

    request_text: str = Field(..., min_length=1, max_length=50000, description="Natural language request or prompt.")
    task_type: Optional[str] = Field(default="general", description="Task classification hint (e.g. general, inspection, code).")
    file_ids: Optional[List[str]] = Field(default=None, description="Optional IDs of previously uploaded source files.")


class TaskResponse(BaseModel):
    """Public summary representation of a workbench task."""

    id: str
    owner_id: str
    request_text: str
    task_type: Optional[str] = None
    complexity: Optional[str] = None
    risk: Optional[str] = None
    status: str
    selected_models_json: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class TaskCancelResponse(BaseModel):
    """Response returned upon cancelling an active task."""

    task_id: str
    status: str = "cancelled"
    message: str = "Task cancellation requested."
