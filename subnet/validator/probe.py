"""
Probe task generation for OpenClade Validators.

Validators probe Miners with a mix of deterministic and open-ended questions.
Deterministic questions (math, code) allow exact consistency checking.
Open-ended questions use semantic similarity for softer consistency scoring.

The test bank is deterministic by default (seeded random) so Validators
produce reproducible probe sets across heartbeat runs.
"""

import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProbeTask:
    """A single probe task sent to one or more Miners."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Dict[str, str]] = field(default_factory=list)
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 512
    temperature: float = 0.0  # Deterministic for consistency scoring
    expected_answer: Optional[str] = None  # For deterministic tasks
    task_type: str = "deterministic"  # "deterministic" | "open_ended"


# Built-in test bank: deterministic questions with known correct answers.
# Validators use these for consistency cross-checking across Miners.
_DETERMINISTIC_TASKS = [
    ProbeTask(
        messages=[{"role": "user", "content": "What is 17 × 23? Reply with only the number."}],
        expected_answer="391",
        task_type="deterministic",
        temperature=0.0,
    ),
    ProbeTask(
        messages=[{"role": "user", "content": "How many days are in a leap year? Reply with only the number."}],
        expected_answer="366",
        task_type="deterministic",
        temperature=0.0,
    ),
    ProbeTask(
        messages=[{"role": "user", "content": "In Python, what does `len([1, 2, 3])` return? Reply with only the number."}],
        expected_answer="3",
        task_type="deterministic",
        temperature=0.0,
    ),
    ProbeTask(
        messages=[{"role": "user", "content": "What is the capital of France? Reply with one word."}],
        expected_answer="Paris",
        task_type="deterministic",
        temperature=0.0,
    ),
    ProbeTask(
        messages=[{"role": "user", "content": "What is 2^10? Reply with only the number."}],
        expected_answer="1024",
        task_type="deterministic",
        temperature=0.0,
    ),
]

_OPEN_ENDED_TASKS = [
    ProbeTask(
        messages=[{"role": "user", "content": "In 2-3 sentences, explain what an API is."}],
        task_type="open_ended",
        temperature=1.0,
        max_tokens=200,
    ),
    ProbeTask(
        messages=[{"role": "user", "content": "Briefly describe the concept of blockchain in 2 sentences."}],
        task_type="open_ended",
        temperature=1.0,
        max_tokens=200,
    ),
]


class ProbeTaskGenerator:
    """
    Generates probe task batches for Validator epochs.

    Scheduling follows the rules from incentive_mechanism.md:
      - < 20 miners: every 5 minutes, probe all
      - 20-100 miners: every 2 minutes, probe random 50
      - > 100 miners: every 1 minute, probe random 30
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def sample(self, num_miners: int) -> List[ProbeTask]:
        """
        Return a list of probe tasks for the current epoch.

        Each task gets a fresh task_id so deduplication is unambiguous.
        """
        tasks = []
        # Always include a mix of deterministic and open-ended
        tasks.extend(self._sample_deterministic(count=3))
        tasks.extend(self._sample_open_ended(count=1))
        return tasks

    def probe_interval_sec(self, num_miners: int) -> int:
        """Return the recommended probe interval in seconds."""
        if num_miners < 20:
            return 300  # 5 minutes
        if num_miners <= 100:
            return 120  # 2 minutes
        return 60  # 1 minute

    def miners_to_probe(self, all_uids: List[int], num_miners: int) -> List[int]:
        """Select which miner UIDs to probe this epoch."""
        if num_miners < 20:
            return all_uids
        limit = 50 if num_miners <= 100 else 30
        return self._rng.sample(all_uids, min(limit, len(all_uids)))

    def _sample_deterministic(self, count: int) -> List[ProbeTask]:
        sampled = self._rng.sample(
            _DETERMINISTIC_TASKS, min(count, len(_DETERMINISTIC_TASKS))
        )
        return [self._fresh_task(t) for t in sampled]

    def _sample_open_ended(self, count: int) -> List[ProbeTask]:
        sampled = self._rng.sample(
            _OPEN_ENDED_TASKS, min(count, len(_OPEN_ENDED_TASKS))
        )
        return [self._fresh_task(t) for t in sampled]

    @staticmethod
    def _fresh_task(template: ProbeTask) -> ProbeTask:
        """Return a copy of the template with a fresh task_id."""
        return ProbeTask(
            task_id=str(uuid.uuid4()),
            messages=template.messages,
            model=template.model,
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            expected_answer=template.expected_answer,
            task_type=template.task_type,
        )
