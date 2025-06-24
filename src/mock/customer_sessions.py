from __future__ import annotations
from typing import Dict, Optional
import uuid

from pydantic import BaseModel, Field


"""Light-weight in-memory store for caller sessions used in mock/testing.

This module intentionally keeps state in-process only. In production you would
back this with Redis or a database, or replace the store with an adapter that
handles multi-instance deployments.
"""



class CustomerSession(BaseModel):
    """Represents an active customer voice/chat session."""

    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    phone_number: str
    channel: str

    model_config = {
        "populate_by_name": True,
    }


class _CustomerSessionStore:
    """In-memory, *NOT* thread-safe store mapping session_id → sessions."""

    def __init__(self) -> None:
        # Keyed by session_id for unique identification
        self._sessions: Dict[str, CustomerSession] = {}

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def get_session(self, session_id: str) -> Optional[CustomerSession]:
        """Fetch an existing session by session_id or None."""
        return self._sessions.get(session_id)

    def create_session(self, phone_number: str, channel: str) -> CustomerSession:
        """Create a new session and return it."""
        session = CustomerSession(phone_number=phone_number, channel=channel.lower())
        self._sessions[session.session_id] = session
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by session_id. Returns True if session existed, False otherwise."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def check_session(self, session_id: str) -> bool:
        """Return True iff there is an active session for the given session_id."""
        return session_id in self._sessions

    def get_session_by_phone_and_channel(self, phone_number: str, channel: str) -> Optional[CustomerSession]:
        """Find a session by phone_number and channel. Returns None if not found."""
        channel_lower = channel.lower()
        for session in self._sessions.values():
            if session.phone_number == phone_number and session.channel == channel_lower:
                return session
        return None


customer_session_store = _CustomerSessionStore()
