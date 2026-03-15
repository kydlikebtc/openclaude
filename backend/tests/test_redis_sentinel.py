"""
Tests for Redis Sentinel HA support in app/core/redis.py.
Covers _parse_sentinel_hosts and _build_redis_client logic paths.
"""
from unittest.mock import MagicMock, patch

import pytest
from redis.asyncio import Redis
from redis.asyncio.sentinel import SentinelManagedConnection

from app.core.redis import _build_redis_client, _parse_sentinel_hosts


class TestParseSentinelHosts:
    def test_single_host_with_port(self):
        result = _parse_sentinel_hosts("localhost:26379")
        assert result == [("localhost", 26379)]

    def test_multiple_hosts(self):
        result = _parse_sentinel_hosts("host1:26379,host2:26380,host3:26381")
        assert result == [
            ("host1", 26379),
            ("host2", 26380),
            ("host3", 26381),
        ]

    def test_default_port_when_missing(self):
        result = _parse_sentinel_hosts("myhost")
        assert result == [("myhost", 26379)]

    def test_ignores_empty_entries(self):
        result = _parse_sentinel_hosts("host1:26379,,host2:26379")
        assert result == [("host1", 26379), ("host2", 26379)]

    def test_trims_whitespace(self):
        result = _parse_sentinel_hosts("  host1:26379 , host2:26379  ")
        assert result == [("host1", 26379), ("host2", 26379)]

    def test_empty_string_returns_empty_list(self):
        result = _parse_sentinel_hosts("")
        assert result == []


class TestBuildRedisClient:
    def test_standalone_mode_returns_redis_instance(self):
        """redis_sentinel_hosts が空なら通常 Redis クライアントを返す。"""
        with patch("app.core.redis.settings") as mock_settings:
            mock_settings.redis_sentinel_hosts = ""
            mock_settings.redis_url = "redis://localhost:6379/0"
            client = _build_redis_client()
        assert isinstance(client, Redis)

    def test_sentinel_mode_returns_managed_connection_client(self):
        """redis_sentinel_hosts が設定されていれば Sentinel マスターへの接続を返す。"""
        with patch("app.core.redis.settings") as mock_settings:
            mock_settings.redis_sentinel_hosts = "sentinel1:26379,sentinel2:26379,sentinel3:26379"
            mock_settings.redis_sentinel_master_name = "mymaster"
            mock_settings.redis_sentinel_password = "secret"
            client = _build_redis_client()
        # Sentinel mode client uses a managed connection pool
        assert client is not None
        pool = client.connection_pool
        assert pool.connection_class is SentinelManagedConnection

    def test_sentinel_mode_no_password(self):
        """Sentinel パスワードが空でも正常に動作する。"""
        with patch("app.core.redis.settings") as mock_settings:
            mock_settings.redis_sentinel_hosts = "sentinel1:26379"
            mock_settings.redis_sentinel_master_name = "mymaster"
            mock_settings.redis_sentinel_password = ""
            client = _build_redis_client()
        assert client is not None
