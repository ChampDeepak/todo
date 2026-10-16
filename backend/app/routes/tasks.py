"""Task CRUD endpoints.

Route order matters: /tasks/stats is declared before /tasks/{task_id}, because
FastAPI matches top to bottom and "stats" would otherwise be parsed as a
task_id and fail validation.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskRead, TaskStats, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    db: Session = Depends(get_db),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = None,
    search: str | None = None,
    # Always bound the page size. An unbounded list endpoint is fine with 20
    # rows and takes the service down at 2 million.
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[Task]:
    stmt = select(Task)
    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if search:
        stmt = stmt.where(Task.title.ilike(f"%{search}%"))
    stmt = stmt.order_by(Task.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars())


@router.get("/stats", response_model=TaskStats)
def task_stats(db: Session = Depends(get_db)) -> TaskStats:
    """Counts computed by Postgres, not by loading every row into Python."""
    rows = db.execute(select(Task.status, func.count()).group_by(Task.status)).all()
    counts = {s.value: 0 for s in TaskStatus}
    for task_status, count in rows:
        counts[task_status.value] = count

    overdue = db.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.due_date < date.today(), Task.status != TaskStatus.done)
    ).scalar_one()

    total = sum(counts.values())
    return TaskStats(
        total=total,
        todo=counts["todo"],
        in_progress=counts["in_progress"],
        done=counts["done"],
        overdue=overdue,
        completion_rate=round(counts["done"] / total * 100, 1) if total else 0.0,
    )


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    return _get_or_404(db, task_id)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = _get_or_404(db, task_id)
    # exclude_unset: only overwrite fields the client actually sent, so a
    # partial update does not silently null out everything it omitted.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/complete", response_model=TaskRead)
def complete_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    task = _get_or_404(db, task_id)
    task.status = TaskStatus.done
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> None:
    task = _get_or_404(db, task_id)
    db.delete(task)
    db.commit()
