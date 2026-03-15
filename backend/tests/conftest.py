import asyncio
import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Enable debug mode before app imports so settings.debug=True during tests.
# This bypasses sr25519 signature verification in integration tests.
os.environ.setdefault("DEBUG", "true")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# Use SQLite for tests (in-memory, no PostgreSQL needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_redis() -> AsyncMock:
    """A mock Redis client that supports common async operations."""
    redis = AsyncMock()

    # Internal storage for simple get/set/hset/hgetall simulations
    _store: dict = {}
    _sets: dict = {}
    _zsets: dict = {}

    async def _get(key):
        return _store.get(key)

    async def _set(key, value, ex=None, **kwargs):
        _store[key] = value

    async def _exists(*keys):
        return sum(1 for k in keys if k in _store)

    async def _hset(key, field=None, value=None, mapping=None):
        if key not in _store:
            _store[key] = {}
        if mapping:
            _store[key].update(mapping)
        elif field is not None:
            _store[key][field] = value

    async def _hgetall(key):
        return _store.get(key, {})

    async def _hincrby(key, field, amount):
        if key not in _store:
            _store[key] = {}
        current = int(_store[key].get(field, 0))
        _store[key][field] = current + amount
        return current + amount

    async def _sadd(key, *values):
        if key not in _sets:
            _sets[key] = set()
        _sets[key].update(values)

    async def _smembers(key):
        return _sets.get(key, set())

    async def _zadd(key, mapping):
        if key not in _zsets:
            _zsets[key] = {}
        _zsets[key].update(mapping)

    async def _zrem(key, *members):
        if key in _zsets:
            for m in members:
                _zsets[key].pop(m, None)

    async def _zscore(key, member):
        return _zsets.get(key, {}).get(member)

    async def _zcard(key):
        return len(_zsets.get(key, {}))

    async def _zrange(key, start, stop, withscores=False):
        members = list(_zsets.get(key, {}).items())
        if withscores:
            return members
        return [m[0] for m in members]

    async def _delete(*keys):
        for k in keys:
            _store.pop(k, None)
        return len(keys)

    async def _hget(key, field):
        return _store.get(key, {}).get(field)

    async def _scan_iter(match="*"):
        """Yield keys matching the pattern (simple prefix/glob emulation)."""
        import fnmatch
        for k in list(_store.keys()) + list(_sets.keys()):
            if fnmatch.fnmatch(str(k), match):
                yield k.encode() if isinstance(k, str) else k

    # Pipeline mock (synchronous method returning async-capable pipeline)
    class _MockPipeline:
        def __init__(self):
            self._calls = []
            self._results = []

        def zremrangebyscore(self, key, min_score, max_score):
            self._results.append(0)
            return self

        def zcard(self, key):
            self._results.append(0)
            return self

        def zadd(self, key, mapping):
            self._results.append(1)
            return self

        def expire(self, key, seconds):
            self._results.append(True)
            return self

        async def execute(self):
            return self._results

    def _pipeline():
        return _MockPipeline()

    redis.get = _get
    redis.set = _set
    redis.exists = _exists
    redis.hset = _hset
    redis.hget = _hget
    redis.hgetall = _hgetall
    redis.hincrby = _hincrby
    redis.sadd = _sadd
    redis.smembers = _smembers
    redis.zadd = _zadd
    redis.zrem = _zrem
    redis.zscore = _zscore
    redis.zcard = _zcard
    redis.zrange = _zrange
    redis.pipeline = _pipeline
    redis.delete = _delete
    redis.scan_iter = _scan_iter

    return redis


@pytest_asyncio.fixture
async def client(db, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with SQLite DB and mock Redis."""
    import app.core.redis as redis_module

    async def override_get_db():
        yield db

    async def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db

    # Patch redis module so lifespan uses mock instead of real Redis
    original_get = redis_module.get_redis_client
    original_close = redis_module.close_redis_client
    redis_module.get_redis_client = override_get_redis
    redis_module.close_redis_client = AsyncMock()

    # Pre-set state so endpoints get mock redis immediately
    app.state.redis = mock_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    redis_module.get_redis_client = original_get
    redis_module.close_redis_client = original_close
