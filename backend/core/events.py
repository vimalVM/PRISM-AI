"""Event broker and persistence for Sovereign AI Workbench streaming events (SSE).

Implements 02_DESIGN_DOC.md section 6.6:
Stores step-by-step agent events into SQLite `task_events` table and broadcasts
to active SSE subscribers.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.db import TaskEvent, get_session_factory


logger = logging.getLogger("sovereign-workbench.events")


class WorkbenchEvent(BaseModel):
    """Pydantic model for streaming events."""

    seq: int
    ts: str
    run_id: str
    type: str
    node: Optional[str] = None
    tool: Optional[str] = None
    model: Optional[str] = None
    status: str = "ok"
    duration_ms: Optional[int] = None
    summary: Optional[str] = None
    refs: Optional[List[str]] = None


class EventBroker:
    """Thread-safe and async-safe broadcast broker with database persistence."""

    _instance: Optional["EventBroker"] = None

    def __init__(self) -> None:
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "EventBroker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def emit(
        self,
        run_id: str,
        event_type: str,
        status: str = "ok",
        node: Optional[str] = None,
        tool: Optional[str] = None,
        model: Optional[str] = None,
        duration_ms: Optional[int] = None,
        summary: Optional[str] = None,
        refs: Optional[List[str]] = None,
        db: Optional[Session] = None,
    ) -> WorkbenchEvent:
        """Emit an event: persist in DB and notify in-memory subscribers."""
        ts_dt = datetime.now(timezone.utc)
        ts_iso = ts_dt.isoformat()

        owns_session = False
        if db is None:
            factory = get_session_factory()
            db = factory()
            owns_session = True

        seq = 1
        try:
            # Check if task exists in DB before inserting foreign key row
            from backend.core.db import Task
            stmt_task = select(Task.id).where(Task.id == run_id)
            task_exists = db.execute(stmt_task).scalar_one_or_none()

            if task_exists:
                # Query last seq for this task
                stmt = (
                    select(TaskEvent.seq)
                    .where(TaskEvent.task_id == run_id)
                    .order_by(TaskEvent.seq.desc())
                    .limit(1)
                )
                last_seq = db.execute(stmt).scalar_one_or_none()
                if last_seq is not None:
                    seq = last_seq + 1

                refs_json = json.dumps(refs) if refs else None

                # Persist to database
                event_row = TaskEvent(
                    task_id=run_id,
                    seq=seq,
                    ts=ts_dt,
                    type=event_type,
                    node=node,
                    tool=tool,
                    model=model,
                    status=status,
                    duration_ms=duration_ms,
                    summary=summary,
                    refs_json=refs_json,
                )
                db.add(event_row)
                db.commit()
        except Exception as exc:
            logger.warning(f"Failed to persist task event for run {run_id}: {exc}")
            if owns_session:
                db.rollback()
        finally:
            if owns_session:
                db.close()

        wb_event = WorkbenchEvent(
            seq=seq,
            ts=ts_iso,
            run_id=run_id,
            type=event_type,
            node=node,
            tool=tool,
            model=model,
            status=status,
            duration_ms=duration_ms,
            summary=summary,
            refs=refs,
        )

        # Notify active async subscriber queues if any exist
        queues = self._subscribers.get(run_id, set()).copy()
        for q in queues:
            try:
                q.put_nowait(wb_event)
            except Exception:
                pass

        return wb_event

    async def subscribe(self, run_id: str) -> AsyncGenerator[WorkbenchEvent, None]:
        """Subscribe to historical and live events for a given run_id."""
        queue: asyncio.Queue[WorkbenchEvent] = asyncio.Queue()

        if run_id not in self._subscribers:
            self._subscribers[run_id] = set()
        self._subscribers[run_id].add(queue)

        try:
            # 1. Yield historical events from database first
            factory = get_session_factory()
            with factory() as db:
                stmt = (
                    select(TaskEvent)
                    .where(TaskEvent.task_id == run_id)
                    .order_by(TaskEvent.seq.asc())
                )
                rows = db.execute(stmt).scalars().all()
                last_seq = 0
                for row in rows:
                    refs = json.loads(row.refs_json) if row.refs_json else None
                    event = WorkbenchEvent(
                        seq=row.seq,
                        ts=row.ts.isoformat(),
                        run_id=row.task_id,
                        type=row.type,
                        node=row.node,
                        tool=row.tool,
                        model=row.model,
                        status=row.status,
                        duration_ms=row.duration_ms,
                        summary=row.summary,
                        refs=refs,
                    )
                    last_seq = row.seq
                    yield event

                    if row.type in {"run_finished", "error", "cancelled"}:
                        return

            # 2. Yield live events from queue
            while True:
                event = await queue.get()
                if event.seq > last_seq:
                    yield event
                    if event.type in {"run_finished", "error", "cancelled"}:
                        break
        finally:
            if run_id in self._subscribers and queue in self._subscribers[run_id]:
                self._subscribers[run_id].remove(queue)
                if not self._subscribers[run_id]:
                    del self._subscribers[run_id]


def get_event_broker() -> EventBroker:
    """Get singleton EventBroker instance."""
    return EventBroker.get_instance()
