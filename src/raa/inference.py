"""Validated adapter from user supplied measurements to the real RAA pipeline."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.impute import KNNImputer

from raa.explain.record import DecisionRecord
from raa.pipeline import DecisionSystem


def select_guided_features(
    feature_names: Sequence[str], feature_importances: ArrayLike, *, count: int = 6
) -> tuple[str, ...]:
    """Choose the most important mean-valued WDBC fields, with stable tie-breaking."""
    names = tuple(str(name) for name in feature_names)
    importance = np.asarray(feature_importances, dtype=np.float64)
    if importance.ndim != 1 or importance.size != len(names):
        raise ValueError("Feature importances must match the feature-name list")
    if not np.isfinite(importance).all() or np.any(importance < 0):
        raise ValueError("Feature importances must be finite and nonnegative")
    eligible = [i for i, name in enumerate(names) if name.startswith("mean ")]
    if not 1 <= count <= len(eligible):
        raise ValueError("count must select at least one available mean feature")
    ranked = sorted(eligible, key=lambda i: (-importance[i], i))
    return tuple(names[i] for i in ranked[:count])


@dataclass(frozen=True)
class BatchRow:
    """A CSV line number paired with its real RAA decision record."""

    row_number: int
    record: DecisionRecord


class CaseInputError(ValueError):
    """A friendly, actionable error for an invalid case input."""


@dataclass(frozen=True)
class InferenceContext:
    """Pre-fitted inference objects and TRAIN-only feature bounds."""

    system: DecisionSystem
    feature_names: tuple[str, ...]
    training_min: tuple[float, ...]
    training_max: tuple[float, ...]
    imputer: KNNImputer | None = None

    def __post_init__(self) -> None:
        size = len(self.feature_names)
        if size == 0 or len(self.training_min) != size or len(self.training_max) != size:
            raise ValueError("Feature names and training bounds must have the same nonzero size")

    @classmethod
    def fit_from_training(
        cls,
        system: DecisionSystem,
        training_features: ArrayLike,
        feature_names: Sequence[str],
        *,
        neighbors: int = 5,
    ) -> InferenceContext:
        """Fit the partial-feature imputer and warnings bounds on training rows only."""
        x_train = np.asarray(training_features, dtype=np.float64)
        names = tuple(str(name) for name in feature_names)
        if x_train.ndim != 2 or x_train.shape[1] != len(names) or not len(x_train):
            raise ValueError(
                "Training features must be a nonempty 2D matrix matching feature names"
            )
        if not np.isfinite(x_train).all() or np.any(x_train < 0):
            raise ValueError("Training features must be finite and nonnegative")
        if neighbors < 1:
            raise ValueError("neighbors must be at least 1")
        imputer = KNNImputer(n_neighbors=min(neighbors, len(x_train)), weights="distance")
        imputer.fit(x_train)
        return cls(
            system=system,
            feature_names=names,
            training_min=tuple(float(value) for value in x_train.min(axis=0)),
            training_max=tuple(float(value) for value in x_train.max(axis=0)),
            imputer=imputer,
        )


def predict_case(
    features: ArrayLike,
    measured_mask: ArrayLike,
    *,
    context: InferenceContext,
) -> DecisionRecord:
    """Validate, impute missing fields, and run the actual classifier-to-policy pipeline.

    ``features`` and ``measured_mask`` must each have one element per WDBC feature.
    Unmeasured entries are ignored and estimated with the KNN imputer fitted on TRAIN only.
    The returned immutable record carries measured/estimated counts and input warnings.
    """
    raw = np.asarray(features, dtype=object)
    mask = np.asarray(measured_mask, dtype=bool)
    size = len(context.feature_names)
    if raw.ndim != 1 or raw.size != size:
        raise CaseInputError(f"Enter exactly {size} feature values.")
    if mask.ndim != 1 or mask.size != size:
        raise CaseInputError(f"The measured-field mask must contain exactly {size} values.")
    if not mask.any():
        raise CaseInputError("Enter at least one measured value.")

    row = np.full(size, np.nan, dtype=np.float64)
    for index in np.flatnonzero(mask):
        try:
            value = float(raw[index])
        except (TypeError, ValueError) as error:
            raise CaseInputError(f"{context.feature_names[index]} must be a number.") from error
        if not np.isfinite(value):
            raise CaseInputError(f"{context.feature_names[index]} must be a finite number.")
        if value < 0:
            raise CaseInputError(f"{context.feature_names[index]} cannot be negative.")
        row[index] = value

    measured_count = int(mask.sum())
    warnings = _input_warnings(row, mask, context)
    if measured_count < size:
        if context.imputer is None:
            raise CaseInputError(
                "Partial measurements need a TRAIN-only imputer, which is unavailable."
            )
        completed = np.asarray(context.imputer.transform(row.reshape(1, -1)), dtype=np.float64)
        if completed.shape != (1, size) or not np.isfinite(completed).all():
            raise CaseInputError(
                "The missing measurements could not be estimated from the training data."
            )
        row = completed[0]
        warnings.append(
            f"{size - measured_count} features were estimated with a TRAIN-only KNN imputer. "
            "The model disagreement score runs on this completed profile; it is not calibrated "
            "to measure imputation uncertainty."
        )

    record = context.system.predict(row.reshape(1, -1))[0]
    return replace(
        record,
        measured_feature_count=measured_count,
        estimated_feature_count=size - measured_count,
        input_warnings=tuple(warnings),
    )


def _input_warnings(
    row: NDArray[np.float64], mask: NDArray[np.bool_], context: InferenceContext
) -> list[str]:
    warnings: list[str] = []
    low = np.asarray(context.training_min)
    high = np.asarray(context.training_max)
    outside = [
        context.feature_names[i]
        for i in np.flatnonzero(mask)
        if row[i] < low[i] or row[i] > high[i]
    ]
    if outside:
        shown = ", ".join(outside[:3])
        suffix = " and more" if len(outside) > 3 else ""
        warnings.append(
            "Outside the observed TRAIN range: "
            + shown
            + suffix
            + ". This can make the case unusual."
        )

    by_name = {name.casefold(): i for i, name in enumerate(context.feature_names)}
    radius = by_name.get("mean radius")
    perimeter = by_name.get("mean perimeter")
    area = by_name.get("mean area")
    pairs = ((radius, perimeter, 2.0 * np.pi, "perimeter"), (radius, area, np.pi, "area"))
    for radius_index, measure_index, factor, label in pairs:
        if (
            radius_index is not None
            and measure_index is not None
            and mask[radius_index]
            and mask[measure_index]
            and row[radius_index] > 0
        ):
            expected = factor * row[radius_index] ** (2 if label == "area" else 1)
            relative_difference = abs(row[measure_index] - expected) / max(expected, 1e-12)
            if relative_difference > 0.50:
                warnings.append(
                    f"Mean {label} is far from the approximate circle check using mean radius; "
                    "please verify the entered units and values."
                )
    return warnings


MAX_BATCH_ROWS = 100


def csv_template(feature_names: Sequence[str]) -> str:
    """Return an empty downloadable CSV template with canonical WDBC columns."""
    output = io.StringIO(newline="")
    csv.writer(output).writerow(feature_names)
    return output.getvalue()


def predict_csv(
    csv_text: str, *, context: InferenceContext, max_rows: int = MAX_BATCH_ROWS
) -> tuple[BatchRow, ...]:
    """Validate a full-feature CSV and run each row through the RAA pipeline in memory."""
    if max_rows < 1:
        raise ValueError("max_rows must be at least 1")
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise CaseInputError("Paste or upload a CSV containing a header and at least one row.")
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        raw_headers = reader.fieldnames
    except csv.Error as error:
        raise CaseInputError(f"Could not read CSV header: {error}") from error
    if not raw_headers:
        raise CaseInputError("CSV header is missing.")
    headers = [header.strip() for header in raw_headers]
    if len(set(headers)) != len(headers):
        raise CaseInputError("CSV contains duplicate column names.")
    expected = list(context.feature_names)
    missing = [name for name in expected if name not in headers]
    extra = [name for name in headers if name not in expected]
    if missing or extra:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing[:3]))
        if extra:
            details.append("unexpected " + ", ".join(extra[:3]))
        raise CaseInputError("CSV columns do not match the 30 WDBC features: " + "; ".join(details))

    reader.fieldnames = headers
    results: list[BatchRow] = []
    for row_number, row in enumerate(reader, start=2):
        if row is None or all(value is None or not str(value).strip() for value in row.values()):
            continue
        if len(results) >= max_rows:
            raise CaseInputError(f"CSV exceeds the {max_rows}-row limit.")
        if None in row:
            raise CaseInputError(f"CSV row {row_number} has more values than the header.")
        values = []
        for name in expected:
            raw_value = row.get(name)
            if raw_value is None or not str(raw_value).strip():
                raise CaseInputError(f"CSV row {row_number}: {name} is empty.")
            values.append(raw_value.strip())
        try:
            record = predict_case(
                values,
                np.ones(len(expected), dtype=bool),
                context=context,
            )
        except CaseInputError as error:
            raise CaseInputError(f"CSV row {row_number}: {error}") from error
        results.append(BatchRow(row_number=row_number, record=record))
    if not results:
        raise CaseInputError("CSV contains a header but no data rows.")
    return tuple(results)


def synthetic_shift_case(
    features: ArrayLike,
    training_std: ArrayLike,
    *,
    feature_count: int = 8,
    shift_sigma: float = 3.0,
    seed: int = 4242,
) -> tuple[NDArray[np.float64], tuple[int, ...]]:
    """Apply the paper's synthetic signed k-sigma shift and clip perturbed values at zero."""
    row = np.asarray(features, dtype=np.float64)
    std = np.asarray(training_std, dtype=np.float64)
    if row.ndim != 1 or std.shape != row.shape or row.size == 0:
        raise CaseInputError(
            "A full feature row and matching TRAIN standard deviations are required."
        )
    if (
        not np.isfinite(row).all()
        or not np.isfinite(std).all()
        or np.any(row < 0)
        or np.any(std < 0)
    ):
        raise CaseInputError("Synthetic stress inputs must be finite and nonnegative.")
    if not 1 <= feature_count <= row.size:
        raise ValueError("feature_count must be between 1 and the feature count")
    if not np.isfinite(shift_sigma) or shift_sigma <= 0:
        raise ValueError("shift_sigma must be finite and positive")
    rng = np.random.default_rng(seed)
    selected = rng.choice(row.size, size=feature_count, replace=False)
    signs = rng.choice(np.array([-1.0, 1.0]), size=feature_count)
    shifted = row.copy()
    shifted[selected] = np.maximum(0.0, row[selected] + signs * shift_sigma * std[selected])
    return shifted, tuple(int(index) for index in selected)
