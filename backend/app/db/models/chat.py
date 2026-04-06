"""Chat session and message models."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.db.models.user import User


class ChatSession(Base, TimestampMixin):
    """AI chat session.

    Groups related chat messages into a conversation.
    Each session tracks the region (BY/RU) and optional title.

    Attributes:
        user_id: Optional user reference.
        title: Auto-generated or user-set session title.
        region: Target marketplace region (BY, RU, all).
        message_count: Cached count of messages in session.
    """

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional user who owns the session",
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Session title (auto-generated from first message)",
    )

    region: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="BY",
        comment="Target region: BY, RU, all",
    )

    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Cached message count",
    )

    # Relationships
    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    user: Mapped[User | None] = relationship(
        "User",
        lazy="joined",
    )

    __table_args__ = (Index("ix_chat_sessions_user_created", "user_id", "created_at"),)

    def __repr__(self) -> str:
        return f"ChatSession(id={self.id}, title={self.title!r}, region={self.region!r})"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(Base, TimestampMixin):
    """Individual chat message within a session.

    Stores both user and assistant messages with optional
    metadata like search results and tool calls.

    Attributes:
        session_id: Parent chat session.
        role: Message sender (user or assistant).
        content: Message text content.
        products: JSON array of products found during search.
        tool_calls: JSON array of tool invocations made by AI.
    """

    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent chat session",
    )

    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole, name="message_role_enum"),
        nullable=False,
        comment="Message sender role",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Message text content",
    )

    products: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Products found during AI search (JSON array)",
    )

    tool_calls: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Tool invocations made by AI agent",
    )

    # Relationships
    session: Mapped[ChatSession] = relationship(
        "ChatSession",
        back_populates="messages",
    )

    __table_args__ = (Index("ix_chat_messages_session_created", "session_id", "created_at"),)

    def __repr__(self) -> str:
        preview = self.content[:50] if self.content else ""
        return f"ChatMessage(id={self.id}, role={self.role!r}, content={preview!r})"
