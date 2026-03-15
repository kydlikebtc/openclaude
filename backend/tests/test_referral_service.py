"""Unit tests for the referral service."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.miner import Miner
from app.services.referral_service import (
    apply_referral,
    count_referrals,
    get_referral_tree,
    resolve_referrer,
)


def _make_miner(name: str, referral_code: str, referred_by_id=None) -> Miner:
    return Miner(
        hotkey=f"hotkey-{name}",
        coldkey=f"coldkey-{name}",
        name=name,
        status="active",
        referral_code=referral_code,
        referred_by_id=referred_by_id,
    )


@pytest.mark.asyncio
async def test_resolve_referrer_valid(db: AsyncSession):
    miner = _make_miner("Alice", "REFCODE1")
    db.add(miner)
    await db.flush()

    found = await resolve_referrer(db, "REFCODE1")
    assert found is not None
    assert found.name == "Alice"


@pytest.mark.asyncio
async def test_resolve_referrer_invalid(db: AsyncSession):
    found = await resolve_referrer(db, "INVALID")
    assert found is None


@pytest.mark.asyncio
async def test_apply_referral_success(db: AsyncSession):
    referrer = _make_miner("Bob", "BOBREF0")
    db.add(referrer)
    await db.flush()

    newcomer = _make_miner("Carol", "CAROLRF")
    db.add(newcomer)
    await db.flush()

    result = await apply_referral(db, newcomer, "BOBREF0")
    assert result is not None
    assert newcomer.referred_by_id == referrer.id


@pytest.mark.asyncio
async def test_apply_referral_invalid_code(db: AsyncSession):
    miner = _make_miner("Dave", "DAVEREF")
    db.add(miner)
    await db.flush()

    result = await apply_referral(db, miner, "BADCODE")
    assert result is None
    assert miner.referred_by_id is None


@pytest.mark.asyncio
async def test_apply_referral_self_blocked(db: AsyncSession):
    miner = _make_miner("Eve", "EVEREF0")
    db.add(miner)
    await db.flush()

    result = await apply_referral(db, miner, "EVEREF0")
    assert result is None
    assert miner.referred_by_id is None


@pytest.mark.asyncio
async def test_apply_referral_already_referred(db: AsyncSession):
    referrer1 = _make_miner("Frank", "FRANK01")
    referrer2 = _make_miner("Grace", "GRACE01")
    db.add(referrer1)
    db.add(referrer2)
    await db.flush()

    miner = _make_miner("Henry", "HENRY01", referred_by_id=referrer1.id)
    db.add(miner)
    await db.flush()

    result = await apply_referral(db, miner, "GRACE01")
    assert result is None  # already referred, not changed
    assert miner.referred_by_id == referrer1.id


@pytest.mark.asyncio
async def test_get_referral_tree_one_level(db: AsyncSession):
    root = _make_miner("Root", "ROOT001")
    db.add(root)
    await db.flush()

    child = _make_miner("Child", "CHILD01", referred_by_id=root.id)
    db.add(child)
    await db.flush()

    tree = await get_referral_tree(db, root.id)
    assert len(tree) == 1
    assert tree[0].level == 1
    assert tree[0].miner_id == child.id


@pytest.mark.asyncio
async def test_get_referral_tree_three_levels(db: AsyncSession):
    a = _make_miner("A", "AAAREF1")
    db.add(a)
    await db.flush()

    b = _make_miner("B", "BBBREF1", referred_by_id=a.id)
    db.add(b)
    await db.flush()

    c = _make_miner("C", "CCCREF1", referred_by_id=b.id)
    db.add(c)
    await db.flush()

    d = _make_miner("D", "DDDREF1", referred_by_id=c.id)
    db.add(d)
    await db.flush()

    tree = await get_referral_tree(db, a.id)
    levels = {r.miner_id: r.level for r in tree}
    assert levels[b.id] == 1
    assert levels[c.id] == 2
    assert levels[d.id] == 3


@pytest.mark.asyncio
async def test_get_referral_tree_beyond_max_depth(db: AsyncSession):
    """Nodes deeper than MAX_REFERRAL_DEPTH should not appear."""
    a = _make_miner("AA", "AAREF11")
    db.add(a)
    await db.flush()

    b = _make_miner("BB", "BBREF11", referred_by_id=a.id)
    db.add(b)
    await db.flush()

    c = _make_miner("CC", "CCREF11", referred_by_id=b.id)
    db.add(c)
    await db.flush()

    d = _make_miner("DD", "DDREF11", referred_by_id=c.id)
    db.add(d)
    await db.flush()

    # Level 4 node — should not appear with max_depth=3
    e = _make_miner("EE", "EEREF11", referred_by_id=d.id)
    db.add(e)
    await db.flush()

    tree = await get_referral_tree(db, a.id, max_depth=3)
    found_ids = {r.miner_id for r in tree}
    assert e.id not in found_ids


def test_count_referrals_empty():
    direct, indirect = count_referrals([])
    assert direct == 0
    assert indirect == 0


def test_count_referrals_mixed():
    from app.services.referral_service import ReferralInfo
    from datetime import datetime

    infos = [
        ReferralInfo(uuid.uuid4(), "hk1", "m1", level=1, joined_at=datetime.now()),
        ReferralInfo(uuid.uuid4(), "hk2", "m2", level=1, joined_at=datetime.now()),
        ReferralInfo(uuid.uuid4(), "hk3", "m3", level=2, joined_at=datetime.now()),
    ]
    direct, indirect = count_referrals(infos)
    assert direct == 2
    assert indirect == 1
