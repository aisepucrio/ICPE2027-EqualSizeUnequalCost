"""pilotCost must keep its random pilot in the returned sample.

The pilot is measured to fit the cost model, so it is part of the sample: it is
charged in the sample's measured cost and used for training.

Run with `python -m pytest tests` or `python tests/test_pilot_cost_sample.py`.
"""

from math import ceil
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cost_sampling.generated_sampling import _pilot_cost_sample  # noqa: E402


def _expected_pilot(n_rows: int, n: int, seed: int) -> set[int]:
    pilot_n = min(max(4, int(ceil(0.20 * n))), max(1, n // 2))
    rng = np.random.default_rng(seed)
    return set(rng.choice(n_rows, size=pilot_n, replace=False).astype(int).tolist())


def test_pilot_is_part_of_the_sample() -> None:
    rng = np.random.default_rng(123)
    X = rng.integers(0, 2, size=(2000, 12)).astype(float)
    cost = np.exp(X @ rng.normal(0.0, 0.6, 12) + rng.normal(0.0, 0.3, 2000))
    for n in (8, 16, 32, 64):
        for seed in range(10):
            sample = _pilot_cost_sample(X, cost, n, np.random.default_rng(seed))
            assert len(sample) == n == len(set(sample)), (n, seed)
            missing = _expected_pilot(X.shape[0], n, seed) - set(sample)
            assert not missing, f"n={n} seed={seed}: pilot configurations {sorted(missing)} not charged"


if __name__ == "__main__":
    test_pilot_is_part_of_the_sample()
    print("ok: pilotCost keeps and charges its pilot")
