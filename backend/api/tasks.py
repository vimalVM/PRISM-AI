"""Task management and SSE streaming endpoints for Sovereign AI Workbench.

Implements Phase 3 endpoints:
- POST /api/tasks: Submit new task and dispatch agent execution.
- GET  /api/tasks: List tasks with role-based filtering.
- GET  /api/tasks/{id}: Retrieve task details.
- GET  /api/tasks/{id}/events: Stream task execution events via SSE (Server-Sent Events).
- POST /api/tasks/{id}/cancel: Cancel active task.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from agent.graph import run_agent
from agent.state import FileRef
from backend.core.audit import log_event
from backend.core.db import FileRecord, Task, User, get_db, get_session_factory
from backend.core.events import get_event_broker
from backend.core.rbac import (
    Clearance,
    Role,
    get_current_user,
    require_role,
)
from backend.schemas.tasks import (
    TaskCancelResponse,
    TaskCreateRequest,
    TaskResponse,
)

logger = logging.getLogger("sovereign-workbench.api.tasks")

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Set of active async task runner handles keyed by task_id
_ACTIVE_TASKS: Dict[str, asyncio.Task] = {}


def _execute_agent_background(
    task_id: str,
    user_id: str,
    user_role: str,
    user_clearance_str: str,
    request_text: str,
    task_type: str,
    uploaded_files: List[FileRef],
) -> None:
    """Synchronous agent execution target run in background thread."""
    factory = get_session_factory()
    with factory() as db:
        stmt = select(Task).where(Task.id == task_id)
        task = db.execute(stmt).scalar_one_or_none()
        if not task:
            return
        task.status = "running"
        db.commit()

    try:
        run_agent(
            user_request=request_text,
            user_id=user_id,
            user_role=user_role,
            user_clearance=user_clearance_str,
            run_id=task_id,
            uploaded_files=uploaded_files,
            task_type=task_type,
        )
    except Exception as exc:
        logger.exception(f"Unhandled error in agent execution for task {task_id}: {exc}")
        broker = get_event_broker()
        broker.emit(
            run_id=task_id,
            event_type="error",
            status="error",
            summary=f"Internal agent execution failure: {exc}",
        )
        with factory() as db:
            stmt = select(Task).where(Task.id == task_id)
            task = db.execute(stmt).scalar_one_or_none()
            if task:
                task.status = "failed"
                task.finished_at = datetime.now(timezone.utc)
                task.error = str(exc)
                db.commit()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(Role.ENGINEER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Submit a new agent execution request and initiate background processing."""
    uploaded_files: List[FileRef] = []
    if payload.file_ids:
        stmt = select(FileRecord).where(FileRecord.id.in_(payload.file_ids))
        file_rows = db.execute(stmt).scalars().all()
        for fr in file_rows:
            uploaded_files.append(
                FileRef(
                    id=fr.id,
                    path=fr.stored_path,
                    modality=fr.modality,
                    pages=fr.pages,
                )
            )

    task = Task(
        owner_id=current_user.id,
        request_text=payload.request_text,
        task_type=payload.task_type or "general",
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    clearance_str = Clearance(current_user.clearance).name

    # Queue background agent execution
    background_tasks.add_task(
        _execute_agent_background,
        task_id=task.id,
        user_id=current_user.id,
        user_role=current_user.role,
        user_clearance_str=clearance_str,
        request_text=payload.request_text,
        task_type=payload.task_type or "general",
        uploaded_files=uploaded_files,
    )

    return TaskResponse.model_validate(task)


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> List[TaskResponse]:
    """List tasks. Admin, Reviewer, and Auditor can view all tasks; Engineers view their own."""
    stmt = select(Task).order_by(Task.created_at.desc())
    if current_user.role == Role.ENGINEER:
        stmt = stmt.where(Task.owner_id == current_user.id)

    stmt = stmt.limit(limit).offset(offset)
    tasks = db.execute(stmt).scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Retrieve details of a single task by ID."""
    stmt = select(Task).where(Task.id == task_id)
    task = db.execute(stmt).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role == Role.ENGINEER and task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view another user's task",
        )

    return TaskResponse.model_validate(task)


@router.get("/{task_id}/events")
async def stream_task_events(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventSourceResponse:
    """Stream real-time and historical events for a task via Server-Sent Events (SSE)."""
    stmt = select(Task).where(Task.id == task_id)
    task = db.execute(stmt).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role == Role.ENGINEER and task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to stream another user's task events",
        )

    broker = get_event_broker()

    async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
        async for event in broker.subscribe(task_id):
            yield {
                "event": event.type,
                "data": event.model_dump_json(),
            }

    return EventSourceResponse(event_generator())


@router.post("/{task_id}/cancel", response_model=TaskCancelResponse)
async def cancel_task(
    task_id: str,
    current_user: User = Depends(require_role(Role.ENGINEER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> TaskCancelResponse:
    """Cancel an active or pending task."""
    stmt = select(Task).where(Task.id == task_id)
    task = db.execute(stmt).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role == Role.ENGINEER and task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to cancel another user's task",
        )

    if task.status in {"completed", "failed", "cancelled"}:
        return TaskCancelResponse(
            task_id=task_id,
            status=task.status,
            message=f"Task already reached terminal state '{task.status}'.",
        )

    task.status = "cancelled"
    task.finished_at = datetime.now(timezone.utc)
    db.commit()

    # Emit cancelled event
    broker = get_event_broker()
    broker.emit(
        run_id=task_id,
        event_type="cancelled",
        status="cancelled",
        summary="Task cancelled by user request.",
    )

    log_event(
        event_type="run_finished",
        status="cancelled",
        user_id=current_user.id,
        role=current_user.role,
        run_id=task_id,
        details={"cancelled_by": current_user.username},
    )

    return TaskCancelResponse(task_id=task_id, status="cancelled")
