"""
Tests for ProbeTaskGenerator — task sampling, interval scheduling,
and miner selection logic.
"""

import pytest

from validator.probe import ProbeTask, ProbeTaskGenerator


class TestProbeTaskGenerator:
    def test_sample_returns_tasks(self):
        gen = ProbeTaskGenerator(seed=42)
        tasks = gen.sample(num_miners=5)
        assert len(tasks) > 0

    def test_sample_tasks_have_unique_ids(self):
        gen = ProbeTaskGenerator(seed=42)
        tasks = gen.sample(num_miners=5)
        ids = [t.task_id for t in tasks]
        assert len(ids) == len(set(ids))

    def test_sample_includes_deterministic_tasks(self):
        gen = ProbeTaskGenerator(seed=42)
        tasks = gen.sample(num_miners=5)
        types = {t.task_type for t in tasks}
        assert "deterministic" in types

    def test_sample_includes_open_ended_tasks(self):
        gen = ProbeTaskGenerator(seed=42)
        tasks = gen.sample(num_miners=5)
        types = {t.task_type for t in tasks}
        assert "open_ended" in types


class TestProbeInterval:
    def test_small_network_5_min_interval(self):
        gen = ProbeTaskGenerator()
        assert gen.probe_interval_sec(5) == 300

    def test_medium_network_2_min_interval(self):
        gen = ProbeTaskGenerator()
        assert gen.probe_interval_sec(50) == 120

    def test_large_network_1_min_interval(self):
        gen = ProbeTaskGenerator()
        assert gen.probe_interval_sec(150) == 60

    def test_boundary_20_miners(self):
        gen = ProbeTaskGenerator()
        assert gen.probe_interval_sec(20) == 120

    def test_boundary_100_miners(self):
        gen = ProbeTaskGenerator()
        assert gen.probe_interval_sec(100) == 120


class TestMinersToProbe:
    def test_small_network_probes_all(self):
        gen = ProbeTaskGenerator(seed=0)
        all_uids = list(range(10))
        probed = gen.miners_to_probe(all_uids, 10)
        assert set(probed) == set(all_uids)

    def test_medium_network_capped_at_50(self):
        gen = ProbeTaskGenerator(seed=0)
        all_uids = list(range(80))
        probed = gen.miners_to_probe(all_uids, 80)
        assert len(probed) <= 50

    def test_large_network_capped_at_30(self):
        gen = ProbeTaskGenerator(seed=0)
        all_uids = list(range(200))
        probed = gen.miners_to_probe(all_uids, 200)
        assert len(probed) <= 30

    def test_probed_uids_are_subset_of_all(self):
        gen = ProbeTaskGenerator(seed=1)
        all_uids = list(range(100))
        probed = gen.miners_to_probe(all_uids, 100)
        assert all(uid in all_uids for uid in probed)

    def test_fewer_miners_than_limit_returns_all(self):
        gen = ProbeTaskGenerator(seed=2)
        all_uids = [0, 1, 2]
        probed = gen.miners_to_probe(all_uids, 200)  # Large network but few UIDs
        assert set(probed) == set(all_uids)


class TestProbeTaskStructure:
    def test_probe_task_has_messages(self):
        task = ProbeTask(
            messages=[{"role": "user", "content": "test"}],
            task_type="deterministic",
        )
        assert len(task.messages) > 0

    def test_deterministic_task_has_expected_answer(self):
        task = ProbeTask(
            messages=[{"role": "user", "content": "What is 1+1?"}],
            task_type="deterministic",
            expected_answer="2",
        )
        assert task.expected_answer == "2"

    def test_task_id_auto_generated(self):
        import uuid
        task = ProbeTask(messages=[{"role": "user", "content": "hi"}])
        uuid.UUID(task.task_id)  # Should not raise
