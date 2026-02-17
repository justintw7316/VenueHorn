"""
In-memory conversation store with TTL eviction.

Each conversation keeps a rolling window of the last N turns.
Designed so the storage backend can be swapped to Redis later
without changing any call sites — just replace this module.
"""
import uuid
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional

from .config import settings


@dataclass
class Conversation:
    id: str
    messages: list[dict]  # OpenAI-format: {"role": str, "content": str}
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def turn(self) -> int:
        """Number of user turns so far."""
        return sum(1 for m in self.messages if m["role"] == "user")

    def is_expired(self) -> bool:
        ttl = timedelta(hours=settings.conversation_ttl_hours)
        return datetime.now(timezone.utc) - self.updated_at > ttl

    def append(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.updated_at = datetime.now(timezone.utc)
        # Keep only the most recent N turns to bound token usage.
        # Preserve the full pair (user + assistant) so context stays coherent.
        max_messages = settings.max_conversation_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]


class ConversationStore:
    """Thread-safe, in-memory conversation store."""

    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_or_create(self, conversation_id: Optional[str]) -> Conversation:
        """Return an existing conversation or start a new one."""
        self._evict_expired()

        if conversation_id and conversation_id in self._store:
            return self._store[conversation_id]

        # New conversation
        cid = str(uuid.uuid4())
        conv = Conversation(id=cid, messages=[])
        self._store[cid] = conv
        return conv

    def save(self, conversation: Conversation) -> None:
        self._store[conversation.id] = conversation

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _evict_expired(self) -> None:
        expired = [cid for cid, conv in self._store.items() if conv.is_expired()]
        for cid in expired:
            del self._store[cid]


# Singleton — replace with a Redis-backed class for multi-instance deployments.
conversation_store = ConversationStore()
