"""Pydantic schemas for API responses."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class DailyActivityRow(BaseModel):
    day: date
    inbound_messages: int
    outbound_messages: int
    active_users: int
    new_conversations: int


class EngagementOverview(BaseModel):
    period_days: int = Field(description="Rolling window length in days (UTC calendar days)")
    total_inbound_messages: int
    total_outbound_messages: int
    total_conversations: int
    avg_daily_active_users: float
    avg_inbound_messages_per_active_user: float
    avg_messages_per_conversation: float


class TwinSummary(BaseModel):
    id: int
    name: str
    platform: str
    created_at: datetime
    user_count: int
    conversation_count: int


class HealthResponse(BaseModel):
    status: str = "ok"
    database: str


class QualityMetrics(BaseModel):
    period_days: int
    feedback_submissions: int
    feedback_positive: int
    feedback_negative: int
    helpfulness_rate: float = Field(
        description="Share of feedback scores that are positive (among submitted feedback)"
    )
    outbound_messages_in_period: int
    share_of_outbound_with_feedback: float = Field(
        description="Feedback rows / outbound messages (coverage of explicit ratings)"
    )
    document_events_total: int
    document_events_by_type: dict[str, int]
    conversations_started: int
    outcome_completed_count: int
    outcome_abandoned_count: int
    outcome_open_count: int
    outcome_completed_share: float


class StickinessMetrics(BaseModel):
    period_days: int
    distinct_active_users: int
    users_with_two_plus_active_days: int
    repeat_visitor_share: float
    avg_distinct_active_days_per_user: float
    median_days_between_active_days: float | None = Field(
        default=None,
        description="Median gap in calendar days between consecutive active days (users with 2+ days only)",
    )
    half_period_retention_rate: float = Field(
        description="Share of users active in the first half of the window who are also active in the second half"
    )


class StructureBreakdownRow(BaseModel):
    key: str
    inbound_messages: int
    share: float


class StructureMetrics(BaseModel):
    period_days: int
    by_role: list[StructureBreakdownRow]
    by_channel: list[StructureBreakdownRow]
