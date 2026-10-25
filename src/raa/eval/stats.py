"""Bootstrap confidence intervals over the 30 split-level estimates."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def summarize(
    values: ArrayLike, *, seed: int = 0, replicates: int = 2000
) -> dict[str, float | int]:
    """Return count, mean, sample standard deviation, and percentile bootstrap 95% CI."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return {
            "n": 0,
            "mean": float("nan"),
            "std": float("nan"),
            "ci95_low": float("nan"),
            "ci95_high": float("nan"),
        }
    rng = np.random.default_rng(seed)
    sampled = rng.choice(x, size=(replicates, x.size), replace=True).mean(axis=1)
    return {
        "n": int(x.size),
        "mean": float(x.mean()),
        "std": float(x.std(ddof=1)) if x.size > 1 else 0.0,
        "ci95_low": float(np.quantile(sampled, 0.025)),
        "ci95_high": float(np.quantile(sampled, 0.975)),
    }
