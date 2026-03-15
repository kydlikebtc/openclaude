"""Unit tests for sr25519 signature verification and SS58 address utilities.

These tests use real cryptographic operations with generated test keypairs
to validate the full authentication flow used by Bittensor miners.
"""

import os

import pytest
import sr25519

from app.core.sr25519_utils import (
    decode_ss58_address,
    encode_ss58_address,
    verify_miner_signature,
)

# Deterministic test seed — do NOT use in production
_TEST_SEED = bytes.fromhex("deadbeef" * 8)
_TEST_SEED_2 = bytes.fromhex("cafebabe" * 8)


@pytest.fixture(scope="module")
def test_keypair():
    """Generate a deterministic sr25519 keypair for testing."""
    pub, priv = sr25519.pair_from_seed(_TEST_SEED)
    return pub, priv


@pytest.fixture(scope="module")
def test_keypair_2():
    """Second test keypair for negative tests."""
    pub, priv = sr25519.pair_from_seed(_TEST_SEED_2)
    return pub, priv


# ── SS58 encode/decode tests ──────────────────────────────────────────────────

class TestSS58:
    def test_encode_decode_roundtrip(self, test_keypair):
        pub, _ = test_keypair
        ss58 = encode_ss58_address(pub)
        decoded = decode_ss58_address(ss58)
        assert decoded == pub, "Decoded public key must match original"

    def test_encode_produces_valid_ss58(self, test_keypair):
        pub, _ = test_keypair
        ss58 = encode_ss58_address(pub)
        # Substrate SS58 addresses for prefix 42 start with '5'
        assert ss58.startswith("5"), f"Bittensor SS58 should start with '5', got: {ss58}"
        assert len(ss58) == 48, f"SS58 length should be 48, got: {len(ss58)}"

    def test_encode_different_keys_produce_different_addresses(self, test_keypair, test_keypair_2):
        pub1, _ = test_keypair
        pub2, _ = test_keypair_2
        assert encode_ss58_address(pub1) != encode_ss58_address(pub2)

    def test_decode_invalid_checksum_raises(self, test_keypair):
        pub, _ = test_keypair
        ss58 = encode_ss58_address(pub)
        # Tamper with last character to corrupt checksum
        tampered = ss58[:-1] + ("A" if ss58[-1] != "A" else "B")
        with pytest.raises(ValueError, match="checksum"):
            decode_ss58_address(tampered)

    def test_decode_invalid_characters_raises(self):
        with pytest.raises(ValueError, match="Invalid base58 character"):
            decode_ss58_address("0invalid0address")  # '0' not in base58

    def test_decode_wrong_key_length_raises(self):
        with pytest.raises(ValueError, match="too short"):
            decode_ss58_address("1")  # too short

    def test_encode_requires_32_bytes(self):
        with pytest.raises(ValueError, match="32 bytes"):
            encode_ss58_address(b"too_short")

    def test_encode_custom_prefix(self, test_keypair):
        pub, _ = test_keypair
        ss58_42 = encode_ss58_address(pub, prefix=42)
        ss58_0 = encode_ss58_address(pub, prefix=0)
        assert ss58_42 != ss58_0, "Different prefixes should produce different addresses"
        # Prefix 42 → starts with '5'; prefix 0 → starts with '1'
        assert ss58_42.startswith("5")
        assert ss58_0.startswith("1")


# ── Signature verification tests ──────────────────────────────────────────────

class TestVerifyMinerSignature:
    def _make_signature(self, pub: bytes, priv: bytes, nonce: str) -> str:
        """Helper: sign nonce and return hex-encoded signature."""
        sig_bytes = sr25519.sign((pub, priv), nonce.encode("utf-8"))
        return sig_bytes.hex()

    def test_valid_signature_returns_true(self, test_keypair):
        pub, priv = test_keypair
        hotkey = encode_ss58_address(pub)
        nonce = "challenge_nonce_abc123"
        signature = self._make_signature(pub, priv, nonce)

        assert verify_miner_signature(hotkey, nonce, signature) is True

    def test_wrong_nonce_returns_false(self, test_keypair):
        pub, priv = test_keypair
        hotkey = encode_ss58_address(pub)
        nonce = "original_nonce"
        signature = self._make_signature(pub, priv, nonce)

        assert verify_miner_signature(hotkey, "different_nonce", signature) is False

    def test_wrong_keypair_returns_false(self, test_keypair, test_keypair_2):
        pub1, priv1 = test_keypair
        pub2, _ = test_keypair_2
        nonce = "challenge_nonce"
        # Sign with keypair 1 but present keypair 2's hotkey
        signature = self._make_signature(pub1, priv1, nonce)
        hotkey2 = encode_ss58_address(pub2)

        assert verify_miner_signature(hotkey2, nonce, signature) is False

    def test_tampered_signature_returns_false(self, test_keypair):
        pub, priv = test_keypair
        hotkey = encode_ss58_address(pub)
        nonce = "nonce_value"
        signature = self._make_signature(pub, priv, nonce)

        # Flip a byte in the signature
        sig_bytes = bytearray(bytes.fromhex(signature))
        sig_bytes[0] ^= 0xFF
        tampered_sig = bytes(sig_bytes).hex()

        assert verify_miner_signature(hotkey, nonce, tampered_sig) is False

    def test_invalid_hotkey_returns_false(self, test_keypair):
        pub, priv = test_keypair
        nonce = "nonce"
        signature = self._make_signature(pub, priv, nonce)

        assert verify_miner_signature("not_a_valid_ss58_address!!!", nonce, signature) is False

    def test_invalid_signature_hex_returns_false(self, test_keypair):
        pub, _ = test_keypair
        hotkey = encode_ss58_address(pub)

        assert verify_miner_signature(hotkey, "nonce", "not_hex_at_all!") is False

    def test_wrong_signature_length_returns_false(self, test_keypair):
        pub, _ = test_keypair
        hotkey = encode_ss58_address(pub)

        # 32 bytes instead of 64
        short_sig = ("aa" * 32)
        assert verify_miner_signature(hotkey, "nonce", short_sig) is False

    def test_empty_signature_returns_false(self, test_keypair):
        pub, _ = test_keypair
        hotkey = encode_ss58_address(pub)

        assert verify_miner_signature(hotkey, "nonce", "") is False

    def test_nonce_bytes_encoding_is_utf8(self, test_keypair):
        """Verify that the nonce is signed as UTF-8 bytes (not hex-decoded)."""
        pub, priv = test_keypair
        hotkey = encode_ss58_address(pub)
        nonce = "a1b2c3d4e5f6"  # looks like hex but is treated as UTF-8 string

        sig_utf8 = sr25519.sign((pub, priv), nonce.encode("utf-8")).hex()
        sig_hex_decoded = sr25519.sign((pub, priv), bytes.fromhex(nonce)).hex()

        # verify_miner_signature uses UTF-8
        assert verify_miner_signature(hotkey, nonce, sig_utf8) is True
        assert verify_miner_signature(hotkey, nonce, sig_hex_decoded) is False

    def test_multiple_nonces_independent(self, test_keypair):
        """Signatures for different nonces are independent."""
        pub, priv = test_keypair
        hotkey = encode_ss58_address(pub)
        nonces = [f"nonce_{i}" for i in range(5)]
        signatures = [self._make_signature(pub, priv, n) for n in nonces]

        for i, (nonce, sig) in enumerate(zip(nonces, signatures)):
            assert verify_miner_signature(hotkey, nonce, sig) is True, f"nonce_{i} should verify"

        # Cross-verify: sig[0] should not verify against nonce[1]
        assert verify_miner_signature(hotkey, nonces[1], signatures[0]) is False
