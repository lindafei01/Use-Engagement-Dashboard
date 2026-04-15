"""Populate SQLite with synthetic Twin usage data (deterministic)."""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from twin_dashboard_api.database import SessionLocal, init_db
from twin_dashboard_api.models import (
    Conversation,
    DocumentEvent,
    Message,
    MessageFeedback,
    Twin,
    TwinUser,
)


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


CHANNELS = [
    "dm",
    "#general",
    "#project-alpha",
    "#sales",
    "#engineering",
    "#customer-success",
]


def seed(session: Session, *, days: int = 45) -> None:
    random.seed(42)
    now = datetime.now(timezone.utc)
    start_day = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

    twins_spec = [
        ("Acme — Product Twin", "slack"),
        ("Beta Labs — Research Twin", "web"),
        ("Northwind — Sales Twin", "slack"),
    ]

    twins: list[Twin] = []
    for name, platform in twins_spec:
        t = Twin(
            name=name,
            platform=platform,
            created_at=start_day - timedelta(days=random.randint(5, 30)),
        )
        session.add(t)
        session.flush()
        twins.append(t)

    all_users: list[TwinUser] = []
    for twin in twins:
        owner = TwinUser(
            twin_id=twin.id,
            display_name=f"Owner {twin.id}",
            role="owner",
        )
        session.add(owner)
        session.flush()
        all_users.append(owner)
        n_collab = random.randint(4, 10)
        for i in range(n_collab):
            u = TwinUser(
                twin_id=twin.id,
                display_name=f"Colleague {twin.id}-{i}",
                role="collaborator",
            )
            session.add(u)
            session.flush()
            all_users.append(u)

    outbound_messages: list[Message] = []

    for day_offset in range(days):
        day = start_day + timedelta(days=day_offset)
        weekday = day.weekday()
        weekend = 0.35 if weekday >= 5 else 1.0
        adoption = 0.4 + 0.6 * (day_offset / max(days - 1, 1))

        for twin in twins:
            twin_users = [u for u in all_users if u.twin_id == twin.id]
            n_active = max(1, int(len(twin_users) * adoption * weekend * random.uniform(0.15, 0.45)))
            active_users = random.sample(twin_users, min(n_active, len(twin_users)))

            for user in active_users:
                n_convs = random.choices([1, 2], weights=[0.85, 0.15])[0]
                for _ in range(n_convs):
                    hour = random.randint(8, 21)
                    minute = random.randint(0, 59)
                    started = day.replace(hour=hour, minute=minute) + timedelta(seconds=random.randint(0, 59))
                    started = _utc(started)
                    outcome = random.choices(
                        ["completed", "abandoned", "open"],
                        weights=[0.52, 0.18, 0.30],
                    )[0]
                    conv = Conversation(
                        twin_id=twin.id,
                        twin_user_id=user.id,
                        channel=random.choice(CHANNELS),
                        started_at=started,
                        outcome=outcome,
                    )
                    session.add(conv)
                    session.flush()

                    # Odd turn counts + occasional trailing user-only message so inbound ≠ outbound totals
                    # (pure even-length alternating dialogue yields a 1:1 ratio).
                    n_turns = random.choices(
                        [2, 3, 4, 5, 6, 7, 8, 9, 10],
                        weights=[0.10, 0.12, 0.12, 0.14, 0.12, 0.12, 0.10, 0.10, 0.08],
                    )[0]
                    t = started
                    for turn in range(n_turns):
                        inbound = turn % 2 == 0
                        body = (
                            "Can you summarize yesterday's thread about the launch checklist?"
                            if inbound
                            else "Here is a concise summary with three action items and owners."
                        )
                        msg = Message(
                            conversation_id=conv.id,
                            twin_user_id=user.id if inbound else None,
                            direction="inbound" if inbound else "outbound",
                            body=body,
                            created_at=t,
                        )
                        session.add(msg)
                        session.flush()
                        if not inbound:
                            outbound_messages.append(msg)
                        t += timedelta(seconds=random.randint(5, 180))

                    # User follow-up or "thanks" without another Twin reply in this slice (more inbound).
                    if random.random() < 0.22:
                        session.add(
                            Message(
                                conversation_id=conv.id,
                                twin_user_id=user.id,
                                direction="inbound",
                                body="Thanks — can you also tighten the risks section?",
                                created_at=t + timedelta(seconds=random.randint(3, 90)),
                            )
                        )
                        session.flush()

                    # Abandoned threads: sometimes end before the Twin's last reply (drop one outbound).
                    if outcome == "abandoned" and random.random() < 0.45 and n_turns >= 2:
                        last_out = (
                            session.query(Message)
                            .filter(
                                Message.conversation_id == conv.id,
                                Message.direction == "outbound",
                            )
                            .order_by(Message.created_at.desc())
                            .first()
                        )
                        if last_out:
                            session.delete(last_out)
                            session.flush()
                            outbound_messages[:] = [m for m in outbound_messages if m.id != last_out.id]

                    # Document drafted in user's style (subset of conversations)
                    if random.random() < 0.12:
                        doc_type = random.choice(["email", "memo", "slack_post", "other"])
                        doc_time = t + timedelta(minutes=random.randint(1, 15))
                        session.add(
                            DocumentEvent(
                                twin_id=twin.id,
                                twin_user_id=user.id,
                                conversation_id=conv.id,
                                doc_type=doc_type,
                                created_at=doc_time,
                            )
                        )

    # Thumbs up/down on Twin replies
    for msg in outbound_messages:
        if random.random() > 0.42:
            continue
        score = random.choices([1, -1], weights=[0.78, 0.22])[0]
        session.add(
            MessageFeedback(
                message_id=msg.id,
                score=score,
                created_at=msg.created_at + timedelta(seconds=random.randint(2, 120)),
            )
        )


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        db.query(MessageFeedback).delete()
        db.query(DocumentEvent).delete()
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(TwinUser).delete()
        db.query(Twin).delete()
        db.commit()
        seed(db, days=45)
        db.commit()
        print("Seed complete: twins, users, conversations, messages, feedback, documents.", file=sys.stderr)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
