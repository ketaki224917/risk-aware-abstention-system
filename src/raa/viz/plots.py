"""Generate plots from the CSV artifacts of a reproducibility run."""

from __future__ import annotations

import csv
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import auc, roc_curve

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MPL_CONFIG_DIR = _PROJECT_ROOT / ".mplconfig"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger(__name__)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def plot_result_artifacts(run_dir: str | Path) -> list[Path]:
    """Write risk-by-level, risk-coverage, and ablation figures from saved tables."""
    root = Path(run_dir)
    created: list[Path] = []
    risk_file = root / "risk_distribution.csv"
    if risk_file.exists():
        groups: dict[str, list[float]] = defaultdict(list)
        for row in _read(risk_file):
            groups[row["decision_level"]].append(float(row["risk"]))
        order = ["Automatic", "Assisted", "Human Review"]
        fig, ax = plt.subplots(figsize=(7.2, 4.4))
        ax.boxplot([groups.get(key, []) for key in order], tick_labels=order, showfliers=False)
        ax.set(
            xlabel="Policy decision level", ylabel="Normalized risk", title="Risk by routed level"
        )
        ax.grid(axis="y", alpha=0.25)
        path = root / "risk_by_level.png"
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        created.append(path)
    curve_file = root / "risk_coverage.csv"
    if curve_file.exists():
        grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in _read(curve_file):
            grouped[int(row["automatic_percentile"])].append(row)
        xs = sorted(grouped)
        coverage = [np.mean([float(row["automatic_coverage"]) for row in grouped[x]]) for x in xs]
        accuracy = [np.mean([float(row["selective_accuracy"]) for row in grouped[x]]) for x in xs]
        fig, ax = plt.subplots(figsize=(6.4, 4.6))
        ax.plot(coverage, accuracy, marker="o")
        ax.set(
            xlabel="Automatic coverage",
            ylabel="Selective accuracy",
            title="Risk–coverage trade-off",
        )
        ax.set_ylim(0, 1.01)
        ax.grid(alpha=0.25)
        for x, cov, acc in zip(xs, coverage, accuracy, strict=True):
            if x == 70:
                ax.scatter([cov], [acc], color="crimson", zorder=3, label="Chosen 70/90 point")
                ax.legend()
        path = root / "risk_coverage.png"
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        created.append(path)
    ablation_file = root / "ablations.csv"
    if ablation_file.exists():
        grouped_ablation: dict[str, list[float]] = defaultdict(list)
        for row in _read(ablation_file):
            grouped_ablation[row["ablation"]].append(float(row["selective_accuracy"]))
        names = list(grouped_ablation)
        means = [float(np.mean(grouped_ablation[name])) for name in names]
        errors = [
            float(np.std(grouped_ablation[name], ddof=1) / np.sqrt(len(grouped_ablation[name])))
            if len(grouped_ablation[name]) > 1
            else 0.0
            for name in names
        ]
        fig, ax = plt.subplots(figsize=(8.4, 4.7))
        ax.bar(names, means, yerr=errors, capsize=3)
        ax.set(
            ylabel="Selective accuracy (automatic cases)", title="Ablation comparison (mean ± SE)"
        )
        ax.tick_params(axis="x", rotation=28)
        ax.set_ylim(0, 1.01)
        ax.grid(axis="y", alpha=0.25)
        path = root / "ablation_accuracy.png"
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        created.append(path)
    logger.info("Generated %d figures in %s", len(created), root)
    return created


def plot_stress_roc(clean_scores: Any, shifted_scores: Any, output: str | Path) -> Path:
    """Plot AUROC for clean versus synthetic shifted examples."""
    clean = np.asarray(clean_scores).ravel()
    shifted = np.asarray(shifted_scores).ravel()
    y = np.r_[np.zeros(clean.size), np.ones(shifted.size)]
    scores = np.r_[clean, shifted]
    fpr, tpr, _ = roc_curve(y, scores)
    score_auc = auc(fpr, tpr)
    path = Path(output)
    fig, ax = plt.subplots(figsize=(5.5, 5.0))
    ax.plot(fpr, tpr, label=f"AUROC = {score_auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Chance")
    ax.set(
        xlabel="False positive rate",
        ylabel="True positive rate",
        title="Isolation Forest synthetic-shift stress test",
    )
    ax.legend(loc="lower right")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_reliability(
    targets: Any, malignant_probability: Any, bins: int, output: str | Path
) -> Path:
    """Create an equal-width reliability diagram for RF P(malignant)."""
    y = np.asarray(targets)
    p = np.asarray(malignant_probability, dtype=float)
    observed = (y == 0).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    means: list[float] = []
    rates: list[float] = []
    for index in range(bins):
        mask = (p >= edges[index]) & (
            (p <= edges[index + 1]) if index == bins - 1 else (p < edges[index + 1])
        )
        if mask.any():
            means.append(float(p[mask].mean()))
            rates.append(float(observed[mask].mean()))
    path = Path(output)
    fig, ax = plt.subplots(figsize=(5.5, 5.0))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
    ax.plot(means, rates, marker="o", label="Random Forest")
    ax.set(
        xlabel="Mean predicted P(malignant)",
        ylabel="Observed malignant fraction",
        title="Reliability diagram",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path
