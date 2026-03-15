"""SR25519 signature verification utilities for Bittensor hotkey authentication.

Provides SS58 address decoding and sr25519 signature verification.
Protocol: miner signs the nonce string (UTF-8) with their sr25519 private key.
Signature is passed as a hex-encoded 64-byte value on the wire.
"""

import hashlib
import struct

import sr25519
import structlog

logger = structlog.get_logger(__name__)

# Substrate SS58 base58 alphabet (same as Bitcoin)
_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# Bittensor / generic Substrate network prefix
_BITTENSOR_SS58_PREFIX = 42


def _base58_decode(s: str) -> bytes:
    """Decode a base58-encoded string to bytes."""
    n = 0
    for char in s:
        idx = _BASE58_ALPHABET.find(char)
        if idx < 0:
            raise ValueError(f"Invalid base58 character: {char!r}")
        n = n * 58 + idx

    # Convert integer to bytes
    result = []
    while n:
        result.append(n & 0xFF)
        n >>= 8

    # Count leading '1' characters (map to zero bytes)
    leading_zeros = len(s) - len(s.lstrip(_BASE58_ALPHABET[0]))
    return bytes(leading_zeros) + bytes(reversed(result))


def _ss58_checksum(prefix: int, public_key: bytes) -> bytes:
    """Compute the 2-byte SS58 checksum.

    checksum = blake2b-512("SS58PRE" + prefix_encoded + public_key)[0:2]
    """
    if prefix < 64:
        prefix_bytes = bytes([prefix])
    else:
        # Double-byte prefix encoding for >= 64
        first = ((prefix & 0xFC) >> 2) | 0x40
        second = (prefix >> 8) | ((prefix & 0x03) << 6)
        prefix_bytes = bytes([first, second])

    payload = b"SS58PRE" + prefix_bytes + public_key
    digest = hashlib.blake2b(payload, digest_size=64).digest()
    return digest[:2]


def encode_ss58_address(public_key: bytes, prefix: int = _BITTENSOR_SS58_PREFIX) -> str:
    """Encode a raw 32-byte public key to SS58 format.

    Args:
        public_key: 32-byte raw sr25519 public key.
        prefix: SS58 network prefix (default 42 for Bittensor).

    Returns:
        SS58-encoded address string.
    """
    if len(public_key) != 32:
        raise ValueError(f"public_key must be 32 bytes, got {len(public_key)}")

    if prefix < 64:
        prefix_bytes = bytes([prefix])
    else:
        first = ((prefix & 0xFC) >> 2) | 0x40
        second = (prefix >> 8) | ((prefix & 0x03) << 6)
        prefix_bytes = bytes([first, second])

    checksum = _ss58_checksum(prefix, public_key)
    payload = prefix_bytes + public_key + checksum

    # Base58 encode
    n = int.from_bytes(payload, "big")
    result = []
    while n:
        n, r = divmod(n, 58)
        result.append(_BASE58_ALPHABET[r])
    leading_zeros = len(payload) - len(payload.lstrip(b"\x00"))
    return _BASE58_ALPHABET[0] * leading_zeros + "".join(reversed(result))


def decode_ss58_address(address: str) -> bytes:
    """Decode an SS58-encoded address to the raw 32-byte public key.

    Args:
        address: SS58-encoded Substrate/Bittensor address (e.g. "5Grw...")

    Returns:
        32-byte raw public key bytes.

    Raises:
        ValueError: if the address is invalid or checksum fails.
    """
    decoded = _base58_decode(address)
    if len(decoded) < 35:
        raise ValueError(f"SS58 address too short: {len(decoded)} bytes")

    prefix_byte = decoded[0]
    if prefix_byte < 64:
        # Single-byte prefix
        public_key = decoded[1:33]
        checksum_stored = decoded[33:35]
        prefix = prefix_byte
    else:
        # Double-byte prefix (canary/encode)
        public_key = decoded[2:34]
        checksum_stored = decoded[34:36]
        first, second = decoded[0], decoded[1]
        prefix = ((first & 0x3F) << 2) | (second >> 6)

    checksum_computed = _ss58_checksum(prefix, public_key)
    if checksum_stored != checksum_computed:
        raise ValueError(
            f"SS58 checksum mismatch for address {address!r}: "
            f"stored={checksum_stored.hex()}, computed={checksum_computed.hex()}"
        )

    logger.debug("ss58 decoded", address=address[:8] + "...", prefix=prefix)
    return public_key


def verify_miner_signature(hotkey: str, nonce: str, signature_hex: str) -> bool:
    """Verify a miner's sr25519 signature of the challenge nonce.

    Args:
        hotkey: SS58-encoded sr25519 public key (Bittensor hotkey address).
        nonce: The challenge nonce string issued by /miners/auth/challenge.
        signature_hex: Hex-encoded 64-byte sr25519 signature.

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        public_key_bytes = decode_ss58_address(hotkey)
    except (ValueError, Exception) as exc:
        logger.warning(
            "sr25519 verification failed: ss58 decode error",
            hotkey=hotkey[:16] + "...",
            error=str(exc),
        )
        return False

    try:
        signature_bytes = bytes.fromhex(signature_hex)
    except ValueError as exc:
        logger.warning(
            "sr25519 verification failed: invalid signature hex",
            error=str(exc),
        )
        return False

    if len(signature_bytes) != 64:
        logger.warning(
            "sr25519 verification failed: wrong signature length",
            expected=64,
            got=len(signature_bytes),
        )
        return False

    message_bytes = nonce.encode("utf-8")

    try:
        # py-sr25519-bindings API: verify(signature, message, pubkey)
        is_valid = sr25519.verify(signature_bytes, message_bytes, public_key_bytes)
        logger.info(
            "sr25519 signature verified",
            hotkey=hotkey[:16] + "...",
            valid=is_valid,
        )
        return bool(is_valid)
    except Exception as exc:
        logger.error(
            "sr25519 verify() raised exception",
            hotkey=hotkey[:16] + "...",
            error=str(exc),
        )
        return False
