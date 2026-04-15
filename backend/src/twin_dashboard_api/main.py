"""FastAPI application: Twin engagement dashboard API."""

from __future__ import annotations

import os
import statistics
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from twin_dashboard_api.database import get_database_url, get_db, init_db
from twin_dashboard_api.models import (
    Conversation,
    DocumentEvent,
    Message,
    MessageFeedback,
    Twin,
    TwinUser,
)
from twin_dashboard_api.schemas import (
    DailyActivityRow,
    EngagementOverview,
    HealthResponse,
    QualityMetrics,
    StickinessMetrics,
    StructureBreakdownRow,
    StructureMetrics,
    TwinSummary,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _period_bounds(days: int) -> tuple[date, date, datetime, datetime]:
    end = _utc_now().date()
    start = end - timedelta(days=days - 1)
    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end, datetime.max.time()).replace(tzinfo=timezone.utc)
    return start, end, start_dt, end_dt


def _half_period(start: date, end: date) -> tuple[tuple[date, date], tuple[date, date]] | None:
    n = (end - start).days + 1
    if n < 4:
        return None
    mid_n = n // 2
    first = (start, start + timedelta(days=mid_n - 1))
    second = (first[1] + timedelta(days=1), end)
    return first, second


def _active_user_ids(
    db: Session, start_d: str, end_d: str
) -> set[int]:
    q = text("""
        SELECT DISTINCT twin_user_id FROM messages
        WHERE direction = 'inbound' AND twin_user_id IS NOT NULL
          AND date(created_at) >= :s AND date(created_at) <= :e
    """)
    return {r[0] for r in db.execute(q, {"s": start_d, "e": end_d}).all()}


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Twin Engagement Dashboard API", version="0.2.0", lifespan=lifespan)

_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(database=get_database_url())


@app.get("/api/metrics/overview", response_model=EngagementOverview)
def engagement_overview(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> EngagementOverview:
    start, end, start_dt, end_dt = _period_bounds(days)

    total_inbound = (
        db.query(func.count(Message.id))
        .filter(
            Message.direction == "inbound",
            Message.created_at >= start_dt,
            Message.created_at <= end_dt,
        )
        .scalar()
        or 0
    )
    total_outbound = (
        db.query(func.count(Message.id))
        .filter(
            Message.direction == "outbound",
            Message.created_at >= start_dt,
            Message.created_at <= end_dt,
        )
        .scalar()
        or 0
    )
    total_conversations = (
        db.query(func.count(Conversation.id))
        .filter(
            Conversation.started_at >= start_dt,
            Conversation.started_at <= end_dt,
        )
        .scalar()
        or 0
    )

    dau_sql = text("""
        SELECT AVG(daily_users) FROM (
            SELECT COUNT(DISTINCT twin_user_id) AS daily_users
            FROM messages
            WHERE direction = 'inbound'
              AND twin_user_id IS NOT NULL
              AND date(created_at) >= :start_d
              AND date(created_at) <= :end_d
            GROUP BY date(created_at)
        )
    """)
    avg_dau = db.execute(dau_sql, {"start_d": start.isoformat(), "end_d": end.isoformat()}).scalar()
    avg_daily_active_users = float(avg_dau) if avg_dau is not None else 0.0

    per_pair_sql = text("""
        SELECT
            CAST(COUNT(*) AS REAL) / NULLIF(COUNT(DISTINCT twin_user_id || '-' || date(created_at)), 0)
        FROM messages
        WHERE direction = 'inbound'
          AND twin_user_id IS NOT NULL
          AND date(created_at) >= :start_d
          AND date(created_at) <= :end_d
    """)
    avg_per_active = db.execute(per_pair_sql, {"start_d": start.isoformat(), "end_d": end.isoformat()}).scalar()
    avg_inbound_per_active_user = float(avg_per_active) if avg_per_active is not None else 0.0

    conv_sql = text("""
        SELECT AVG(msg_count) FROM (
            SELECT c.id AS cid, COUNT(m.id) AS msg_count
            FROM conversations c
            JOIN messages m ON m.conversation_id = c.id
            WHERE c.started_at >= :start_dt AND c.started_at <= :end_dt
            GROUP BY c.id
        )
    """)
    avg_conv = db.execute(conv_sql, {"start_dt": start_dt, "end_dt": end_dt}).scalar()
    avg_messages_per_conversation = float(avg_conv) if avg_conv is not None else 0.0

    return EngagementOverview(
        period_days=days,
        total_inbound_messages=int(total_inbound),
        total_outbound_messages=int(total_outbound),
        total_conversations=int(total_conversations),
        avg_daily_active_users=avg_daily_active_users,
        avg_inbound_messages_per_active_user=avg_inbound_per_active_user,
        avg_messages_per_conversation=avg_messages_per_conversation,
    )


@app.get("/api/metrics/daily", response_model=list[DailyActivityRow])
def daily_metrics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> list[DailyActivityRow]:
    end = _utc_now().date()
    start = end - timedelta(days=days - 1)

    inbound_sql = text("""
        SELECT date(created_at) AS d, COUNT(*) FROM messages
        WHERE direction = 'inbound' AND date(created_at) >= :start_d AND date(created_at) <= :end_d
        GROUP BY date(created_at)
    """)
    outbound_sql = text("""
        SELECT date(created_at) AS d, COUNT(*) FROM messages
        WHERE direction = 'outbound' AND date(created_at) >= :start_d AND date(created_at) <= :end_d
        GROUP BY date(created_at)
    """)
    active_sql = text("""
        SELECT date(created_at) AS d, COUNT(DISTINCT twin_user_id) FROM messages
        WHERE direction = 'inbound' AND twin_user_id IS NOT NULL
          AND date(created_at) >= :start_d AND date(created_at) <= :end_d
        GROUP BY date(created_at)
    """)
    conv_sql = text("""
        SELECT date(started_at) AS d, COUNT(*) FROM conversations
        WHERE date(started_at) >= :start_d AND date(started_at) <= :end_d
        GROUP BY date(started_at)
    """)

    params = {"start_d": start.isoformat(), "end_d": end.isoformat()}
    inbound_map = {r[0]: r[1] for r in db.execute(inbound_sql, params).all()}
    outbound_map = {r[0]: r[1] for r in db.execute(outbound_sql, params).all()}
    active_map = {r[0]: r[1] for r in db.execute(active_sql, params).all()}
    conv_map = {r[0]: r[1] for r in db.execute(conv_sql, params).all()}

    rows: list[DailyActivityRow] = []
    d = start
    while d <= end:
        ds = d.isoformat()
        rows.append(
            DailyActivityRow(
                day=d,
                inbound_messages=int(inbound_map.get(ds, 0)),
                outbound_messages=int(outbound_map.get(ds, 0)),
                active_users=int(active_map.get(ds, 0)),
                new_conversations=int(conv_map.get(ds, 0)),
            )
        )
        d += timedelta(days=1)
    return rows


@app.get("/api/metrics/quality", response_model=QualityMetrics)
def quality_metrics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> QualityMetrics:
    start, end, start_dt, end_dt = _period_bounds(days)
    sd, ed = start.isoformat(), end.isoformat()

    outbound_total = (
        db.query(func.count(Message.id))
        .filter(
            Message.direction == "outbound",
            Message.created_at >= start_dt,
            Message.created_at <= end_dt,
        )
        .scalar()
        or 0
    )

    fb_sql = text("""
        SELECT
            COUNT(*),
            SUM(CASE WHEN mf.score > 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN mf.score < 0 THEN 1 ELSE 0 END)
        FROM message_feedback mf
        JOIN messages m ON m.id = mf.message_id
        WHERE m.direction = 'outbound'
          AND date(m.created_at) >= :s AND date(m.created_at) <= :e
    """)
    r = db.execute(fb_sql, {"s": sd, "e": ed}).one()
    fb_total, pos, neg = int(r[0] or 0), int(r[1] or 0), int(r[2] or 0)
    helpful = float(pos) / float(pos + neg) if (pos + neg) > 0 else 0.0
    coverage = float(fb_total) / float(outbound_total) if outbound_total > 0 else 0.0

    doc_rows = (
        db.query(DocumentEvent.doc_type, func.count(DocumentEvent.id))
        .filter(DocumentEvent.created_at >= start_dt, DocumentEvent.created_at <= end_dt)
        .group_by(DocumentEvent.doc_type)
        .all()
    )
    doc_by_type = {str(row[0]): int(row[1]) for row in doc_rows}
    doc_total = sum(doc_by_type.values())

    conv_total = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.started_at >= start_dt, Conversation.started_at <= end_dt)
        .scalar()
        or 0
    )
    oc = (
        db.query(Conversation.outcome, func.count(Conversation.id))
        .filter(Conversation.started_at >= start_dt, Conversation.started_at <= end_dt)
        .group_by(Conversation.outcome)
        .all()
    )
    outcome_map = {str(row[0]): int(row[1]) for row in oc}
    n_completed = outcome_map.get("completed", 0)
    n_abandoned = outcome_map.get("abandoned", 0)
    n_open = outcome_map.get("open", 0)
    completed_share = float(n_completed) / float(conv_total) if conv_total > 0 else 0.0

    return QualityMetrics(
        period_days=days,
        feedback_submissions=fb_total,
        feedback_positive=pos,
        feedback_negative=neg,
        helpfulness_rate=helpful,
        outbound_messages_in_period=int(outbound_total),
        share_of_outbound_with_feedback=coverage,
        document_events_total=doc_total,
        document_events_by_type=doc_by_type,
        conversations_started=int(conv_total),
        outcome_completed_count=n_completed,
        outcome_abandoned_count=n_abandoned,
        outcome_open_count=n_open,
        outcome_completed_share=completed_share,
    )


@app.get("/api/metrics/stickiness", response_model=StickinessMetrics)
def stickiness_metrics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> StickinessMetrics:
    start, end, start_dt, end_dt = _period_bounds(days)
    sd, ed = start.isoformat(), end.isoformat()

    distinct_sql = text("""
        SELECT COUNT(DISTINCT twin_user_id) FROM messages
        WHERE direction = 'inbound' AND twin_user_id IS NOT NULL
          AND date(created_at) >= :s AND date(created_at) <= :e
    """)
    distinct_users = int(db.execute(distinct_sql, {"s": sd, "e": ed}).scalar() or 0)

    repeat_sql = text("""
        SELECT COUNT(*) FROM (
            SELECT twin_user_id FROM messages
            WHERE direction = 'inbound' AND twin_user_id IS NOT NULL
              AND date(created_at) >= :s AND date(created_at) <= :e
            GROUP BY twin_user_id
            HAVING COUNT(DISTINCT date(created_at)) >= 2
        )
    """)
    repeat_users = int(db.execute(repeat_sql, {"s": sd, "e": ed}).scalar() or 0)
    repeat_share = float(repeat_users) / float(distinct_users) if distinct_users > 0 else 0.0

    avg_days_sql = text("""
        SELECT AVG(dc) FROM (
            SELECT COUNT(DISTINCT date(created_at)) AS dc
            FROM messages
            WHERE direction = 'inbound' AND twin_user_id IS NOT NULL
              AND date(created_at) >= :s AND date(created_at) <= :e
            GROUP BY twin_user_id
        )
    """)
    avg_days = db.execute(avg_days_sql, {"s": sd, "e": ed}).scalar()
    avg_distinct = float(avg_days) if avg_days is not None else 0.0

    day_pairs = text("""
        SELECT twin_user_id, date(created_at) AS d
        FROM messages
        WHERE direction = 'inbound' AND twin_user_id IS NOT NULL
          AND date(created_at) >= :s AND date(created_at) <= :e
        GROUP BY twin_user_id, date(created_at)
    """)
    by_user: dict[int, list[str]] = defaultdict(list)
    for uid, dstr in db.execute(day_pairs, {"s": sd, "e": ed}).all():
        by_user[int(uid)].append(str(dstr))
    gaps: list[int] = []
    for days_list in by_user.values():
        ds_sorted = sorted(set(days_list))
        for i in range(1, len(ds_sorted)):
            a = date.fromisoformat(ds_sorted[i - 1])
            b = date.fromisoformat(ds_sorted[i])
            gaps.append((b - a).days)
    median_gap = float(statistics.median(gaps)) if gaps else None

    halves = _half_period(start, end)
    retention = 0.0
    if halves:
        (a0, a1), (b0, b1) = halves
        first = _active_user_ids(db, a0.isoformat(), a1.isoformat())
        second = _active_user_ids(db, b0.isoformat(), b1.isoformat())
        if first:
            retention = float(len(first & second)) / float(len(first))

    return StickinessMetrics(
        period_days=days,
        distinct_active_users=distinct_users,
        users_with_two_plus_active_days=repeat_users,
        repeat_visitor_share=repeat_share,
        avg_distinct_active_days_per_user=avg_distinct,
        median_days_between_active_days=median_gap,
        half_period_retention_rate=retention,
    )


@app.get("/api/metrics/structure", response_model=StructureMetrics)
def structure_metrics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> StructureMetrics:
    start, end, start_dt, end_dt = _period_bounds(days)
    sd, ed = start.isoformat(), end.isoformat()

    total_inbound = (
        db.query(func.count(Message.id))
        .filter(
            Message.direction == "inbound",
            Message.created_at >= start_dt,
            Message.created_at <= end_dt,
        )
        .scalar()
        or 0
    )

    role_sql = text("""
        SELECT u.role, COUNT(m.id)
        FROM messages m
        JOIN twin_users u ON u.id = m.twin_user_id
        WHERE m.direction = 'inbound'
          AND date(m.created_at) >= :s AND date(m.created_at) <= :e
        GROUP BY u.role
    """)
    by_role: list[StructureBreakdownRow] = []
    for role, cnt in db.execute(role_sql, {"s": sd, "e": ed}).all():
        c = int(cnt)
        share = float(c) / float(total_inbound) if total_inbound > 0 else 0.0
        by_role.append(StructureBreakdownRow(key=str(role), inbound_messages=c, share=share))

    ch_sql = text("""
        SELECT c.channel, COUNT(m.id)
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE m.direction = 'inbound'
          AND date(m.created_at) >= :s AND date(m.created_at) <= :e
        GROUP BY c.channel
        ORDER BY COUNT(m.id) DESC
    """)
    by_channel: list[StructureBreakdownRow] = []
    for ch, cnt in db.execute(ch_sql, {"s": sd, "e": ed}).all():
        c = int(cnt)
        share = float(c) / float(total_inbound) if total_inbound > 0 else 0.0
        by_channel.append(StructureBreakdownRow(key=str(ch), inbound_messages=c, share=share))

    return StructureMetrics(period_days=days, by_role=by_role, by_channel=by_channel)


@app.get("/api/twins", response_model=list[TwinSummary])
def list_twins(db: Session = Depends(get_db)) -> list[TwinSummary]:
    twins = db.query(Twin).order_by(Twin.id).all()
    out: list[TwinSummary] = []
    for t in twins:
        user_count = db.query(func.count(TwinUser.id)).filter(TwinUser.twin_id == t.id).scalar() or 0
        conv_count = db.query(func.count(Conversation.id)).filter(Conversation.twin_id == t.id).scalar() or 0
        out.append(
            TwinSummary(
                id=t.id,
                name=t.name,
                platform=t.platform,
                created_at=t.created_at,
                user_count=int(user_count),
                conversation_count=int(conv_count),
            )
        )
    return out
