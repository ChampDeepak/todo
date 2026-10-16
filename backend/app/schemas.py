"""Pydantic schemas -- the API contract.

These are deliberately separate from the ORM models. The model describes what
is stored; the schema describes what crosses the network. Keeping them apart
means an internal column can be added without leaking it to every API client,
and an API field can be renamed without a migration.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None


class TaskCreate(TaskBase):
    """Request body for POST /api/tasks."""


class TaskUpdate(BaseModel):
    """Request body for PUT /api/tasks/{id}. Every field optional: the client
    sends only what it wants changed."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TaskStats(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int
    overdue: int
    completion_rate: float
