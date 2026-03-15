"""
OpenClade Subnet Protocol Definition.

LLMAPISynapse is the core message type passed between Validators (dendrite)
and Miners (axon) on the Bittensor network.

Protocol version bumps when backward-incompatible field changes are made.
Validators check this version before scoring to avoid comparing apples and
oranges across protocol upgrades.
"""

import hashlib
import time
from typing import Dict, List, Optional

import bittensor as bt

PROTOCOL_VERSION = "1.0.0"


class LLMAPISynapse(bt.Synapse):
    """
    Synapse for forwarding Claude API requests through the OpenClade subnet.

    Request fields are set by the Validator (dendrite side) before sending.
    Response fields are filled in by the Miner (axon side) before returning.

    Validation rules (Pydantic v2) enforce type correctness at both ends.
    """

    # ── Protocol metadata ────────────────────────────────────────────────
    protocol_version: str = PROTOCOL_VERSION

    # ── Request fields (set by Validator) ───────────────────────────────
    messages: List[Dict[str, str]] = []
    """OpenAI-compatible messages list, e.g. [{"role": "user", "content": "..."}]"""

    model: str = "claude-sonnet-4-6"
    """Claude model identifier the caller wants to use."""

    max_tokens: int = 4096
    """Maximum tokens in the generated response."""

    temperature: float = 1.0
    """Sampling temperature (0.0 = deterministic, 1.0 = default)."""

    stream: bool = False
    """Whether the caller expects a streaming response (not yet supported)."""

    request_id: str = ""
    """UUID assigned by the Validator for deduplication and audit trail."""

    request_timestamp: float = 0.0
    """Unix timestamp when the Validator created this request."""

    # ── Response fields (filled by Miner) ───────────────────────────────
    response: Optional[str] = None
    """The text content of the Claude API response."""

    tokens_used: int = 0
    """Total tokens consumed (prompt + completion)."""

    finish_reason: str = ""
    """Claude finish reason: 'end_turn', 'max_tokens', 'stop_sequence', etc."""

    response_hash: str = ""
    """SHA-256 of the raw response string, for Validator integrity checks."""

    latency_ms: int = 0
    """End-to-end latency in milliseconds as measured by the Miner."""

    miner_model_used: str = ""
    """Actual model the Miner called (may differ from requested if downgraded)."""

    error_message: str = ""
    """Non-empty when the Miner encountered an error processing the request."""

    # ── Serialization helpers ────────────────────────────────────────────

    def compute_response_hash(self) -> str:
        """
        Compute and set response_hash from the current response field.

        Returns the computed hash so callers can chain this call.
        """
        if self.response is None:
            self.response_hash = ""
        else:
            self.response_hash = hashlib.sha256(
                self.response.encode("utf-8")
            ).hexdigest()
        return self.response_hash

    def is_success(self) -> bool:
        """Return True when the Miner populated a non-empty response."""
        return bool(self.response) and not self.error_message

    def validate_response_hash(self) -> bool:
        """
        Verify that response_hash matches the actual response content.

        Used by Validators to detect tampered or truncated responses.
        """
        if self.response is None:
            return self.response_hash == ""
        expected = hashlib.sha256(self.response.encode("utf-8")).hexdigest()
        return expected == self.response_hash

    def to_request_dict(self) -> Dict:
        """Return only the request-side fields as a plain dict."""
        return {
            "protocol_version": self.protocol_version,
            "messages": self.messages,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": self.stream,
            "request_id": self.request_id,
            "request_timestamp": self.request_timestamp,
        }

    def to_response_dict(self) -> Dict:
        """Return only the response-side fields as a plain dict."""
        return {
            "response": self.response,
            "tokens_used": self.tokens_used,
            "finish_reason": self.finish_reason,
            "response_hash": self.response_hash,
            "latency_ms": self.latency_ms,
            "miner_model_used": self.miner_model_used,
            "error_message": self.error_message,
        }

    @classmethod
    def create_request(
        cls,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        request_id: str = "",
    ) -> "LLMAPISynapse":
        """
        Factory method for creating a well-formed request synapse.

        Sets request_timestamp automatically so Validators don't need to.
        """
        import uuid

        return cls(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            request_id=request_id or str(uuid.uuid4()),
            request_timestamp=time.time(),
        )
