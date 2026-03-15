"""
Tests for LLMAPISynapse protocol definition.

Covers: serialization round-trips, hash computation/verification,
factory method, and response validation helpers.
"""

import hashlib
import time
import uuid

import pytest

from protocol.synapse import LLMAPISynapse, PROTOCOL_VERSION


class TestLLMAPISynapseDefaults:
    def test_default_protocol_version(self):
        s = LLMAPISynapse()
        assert s.protocol_version == PROTOCOL_VERSION

    def test_default_model(self):
        s = LLMAPISynapse()
        assert s.model == "claude-sonnet-4-6"

    def test_default_max_tokens(self):
        s = LLMAPISynapse()
        assert s.max_tokens == 4096

    def test_default_response_is_none(self):
        s = LLMAPISynapse()
        assert s.response is None

    def test_is_success_on_empty_synapse(self):
        s = LLMAPISynapse()
        assert not s.is_success()


class TestResponseHash:
    def test_compute_hash_sets_field(self):
        s = LLMAPISynapse(response="Hello, world!")
        computed = s.compute_response_hash()
        expected = hashlib.sha256("Hello, world!".encode()).hexdigest()
        assert computed == expected
        assert s.response_hash == expected

    def test_compute_hash_on_none_response(self):
        s = LLMAPISynapse(response=None)
        result = s.compute_response_hash()
        assert result == ""
        assert s.response_hash == ""

    def test_validate_response_hash_passes(self):
        s = LLMAPISynapse(response="test response")
        s.compute_response_hash()
        assert s.validate_response_hash()

    def test_validate_response_hash_fails_on_tamper(self):
        s = LLMAPISynapse(response="original")
        s.compute_response_hash()
        s.response = "tampered"  # Hash not updated
        assert not s.validate_response_hash()

    def test_validate_hash_none_response_empty_hash(self):
        s = LLMAPISynapse(response=None, response_hash="")
        assert s.validate_response_hash()

    def test_validate_hash_none_response_nonempty_hash(self):
        s = LLMAPISynapse(response=None, response_hash="abc123")
        assert not s.validate_response_hash()


class TestIsSuccess:
    def test_success_with_response_no_error(self):
        s = LLMAPISynapse(response="some text", error_message="")
        assert s.is_success()

    def test_failure_with_empty_response(self):
        s = LLMAPISynapse(response="", error_message="")
        assert not s.is_success()

    def test_failure_with_error_message(self):
        s = LLMAPISynapse(response="some text", error_message="API error")
        assert not s.is_success()

    def test_failure_with_none_response(self):
        s = LLMAPISynapse(response=None, error_message="")
        assert not s.is_success()


class TestCreateRequest:
    def test_create_request_sets_messages(self):
        msgs = [{"role": "user", "content": "hello"}]
        s = LLMAPISynapse.create_request(messages=msgs)
        assert s.messages == msgs

    def test_create_request_auto_request_id(self):
        s = LLMAPISynapse.create_request(messages=[])
        assert len(s.request_id) > 0
        # Should be a valid UUID
        uuid.UUID(s.request_id)

    def test_create_request_custom_request_id(self):
        rid = str(uuid.uuid4())
        s = LLMAPISynapse.create_request(messages=[], request_id=rid)
        assert s.request_id == rid

    def test_create_request_sets_timestamp(self):
        before = time.time()
        s = LLMAPISynapse.create_request(messages=[])
        after = time.time()
        assert before <= s.request_timestamp <= after

    def test_create_request_custom_model(self):
        s = LLMAPISynapse.create_request(
            messages=[], model="claude-haiku-4-5-20251001"
        )
        assert s.model == "claude-haiku-4-5-20251001"

    def test_create_request_custom_max_tokens(self):
        s = LLMAPISynapse.create_request(messages=[], max_tokens=256)
        assert s.max_tokens == 256


class TestSerializationDicts:
    def test_to_request_dict_contains_required_keys(self):
        s = LLMAPISynapse.create_request(messages=[{"role": "user", "content": "hi"}])
        d = s.to_request_dict()
        assert "messages" in d
        assert "model" in d
        assert "max_tokens" in d
        assert "temperature" in d
        assert "request_id" in d
        assert "protocol_version" in d

    def test_to_response_dict_contains_required_keys(self):
        s = LLMAPISynapse(response="hello", tokens_used=10, finish_reason="end_turn")
        s.compute_response_hash()
        d = s.to_response_dict()
        assert "response" in d
        assert "tokens_used" in d
        assert "finish_reason" in d
        assert "response_hash" in d
        assert "latency_ms" in d

    def test_to_request_dict_excludes_response_fields(self):
        s = LLMAPISynapse(response="should not appear")
        d = s.to_request_dict()
        assert "response" not in d

    def test_to_response_dict_excludes_request_fields(self):
        s = LLMAPISynapse(messages=[{"role": "user", "content": "hi"}])
        d = s.to_response_dict()
        assert "messages" not in d
