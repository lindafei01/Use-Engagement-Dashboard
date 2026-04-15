"""SQLAlchemy models for Twin usage and engagement."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Twin(Base):
    """A deployed Twin (e.g. Slack app instance) that users chat with."""

    __tablename__ = "twins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)  # slack, web, teams
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    users: Mapped[list[TwinUser]] = relationship(back_populates="twin")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="twin")


class TwinUser(Base):
    """A human who can message a Twin (owner or colleague)."""

    __tablename__ = "twin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    twin_id: Mapped[int] = mapped_column(ForeignKey("twins.id"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # owner, collaborator

    twin: Mapped[Twin] = relationship(back_populates="users")


class Conversation(Base):
    """A chat thread between users and a Twin."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    twin_id: Mapped[int] = mapped_column(ForeignKey("twins.id"), nullable=False)
    twin_user_id: Mapped[int] = mapped_column(ForeignKey("twin_users.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)  # dm, channel slug, etc.
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Proxy for "did the user get value": completed / abandoned / still open
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="open")

    twin: Mapped[Twin] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(back_populates="conversation")


class Message(Base):
    """Single message in a conversation (inbound from human or outbound from Twin)."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    twin_user_id: Mapped[int | None] = mapped_column(ForeignKey("twin_users.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # inbound, outbound
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    feedback: Mapped[MessageFeedback | None] = relationship(back_populates="message")


class MessageFeedback(Base):
    """Explicit thumbs up/down on a Twin reply (outbound message)."""

    __tablename__ = "message_feedback"
    __table_args__ = (UniqueConstraint("message_id", name="uq_feedback_message"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # +1 helpful, -1 not helpful
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    message: Mapped[Message] = relationship(back_populates="feedback")


class DocumentEvent(Base):
    """User generated a draft document in their style (email, memo, etc.)."""

    __tablename__ = "document_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    twin_id: Mapped[int] = mapped_column(ForeignKey("twins.id"), nullable=False)
    twin_user_id: Mapped[int] = mapped_column(ForeignKey("twin_users.id"), nullable=False)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)  # email, memo, slack_post, other
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
