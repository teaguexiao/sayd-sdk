"""
sayd-ai: Official Python SDK for the Sayd Speech API
Voice Interface for AI Agents. You said it. Agents did it.
"""

from .client import Sayd, AsyncSayd
from .models import TalkEvent, TalkSession, ListenSession, TranscriptionTask
from .exceptions import SaydError, AuthenticationError, RateLimitError

__version__ = "0.2.0"
__all__ = [
    "Sayd",
    "AsyncSayd",
    "TalkEvent",
    "TalkSession",
    "ListenSession",
    "TranscriptionTask",
    "SaydError",
    "AuthenticationError",
    "RateLimitError",
]
