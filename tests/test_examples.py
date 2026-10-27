import numpy as np

from raa.app.demo_assets import load_demo_artifact
from raa.app.examples import select_example_cases
from raa.data import load_breast_cancer_data, stratified_split
from raa.risk.policy import DecisionLevel


def test_held_out_example_categories_match_their_claims(monkeypatch):
    import raa.app.demo_assets as assets

    monkeypatch.setattr(
        assets,
        "fit_system",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("loader retrained")),
    )
    artifact = load_demo_artifact()
    data = load_breast_cancer_data()
    split = stratified_split(data.targets, seed=artifact.run_seed)
    records = artifact.system.predict(data.features[split.test])
    cases = select_example_cases(data, split, records)
    assert set(cases) == {
        "low_risk",
        "high_concern",
        "borderline_review",
        "unusual",
        "baseline_wrong",
        "random",
    }
    assert len({case.dataset_row for case in cases.values()}) == 6

    records_by_test = {i: record for i, record in enumerate(records)}
    low_position = cases["low_risk"].test_position
    low_record = records_by_test[low_position]
    automatic_risks = [r.risk for r in records if r.level is DecisionLevel.AUTOMATIC]
    assert low_record.level is DecisionLevel.AUTOMATIC
    assert low_record.risk == min(automatic_risks)

    high_position = cases["high_concern"].test_position
    high_record = records_by_test[high_position]
    human_risks = [r.risk for r in records if r.level is DecisionLevel.HUMAN_REVIEW]
    assert high_record.level is DecisionLevel.HUMAN_REVIEW
    assert high_record.risk == max(human_risks)

    borderline_position = cases["borderline_review"].test_position
    borderline_record = records_by_test[borderline_position]
    above_threshold = [r.risk for r in records if r.level is DecisionLevel.HUMAN_REVIEW]
    assert borderline_record.level is DecisionLevel.HUMAN_REVIEW
    assert borderline_record.risk == min(above_threshold)
    assert borderline_record.risk > borderline_record.assisted_threshold

    unusual_position = cases["unusual"].test_position
    unusual_record = records_by_test[unusual_position]
    assert unusual_record.anomaly >= np.quantile([r.anomaly for r in records], 0.9)

    error_case = cases["baseline_wrong"]
    target = int(data.targets[error_case.dataset_row])
    prediction = records_by_test[error_case.test_position].predicted_class
    assert prediction != target

    second = select_example_cases(data, split, records)
    assert cases["random"] == second["random"]


def test_guided_fields_match_train_only_importance_results():
    import csv
    from pathlib import Path

    artifact = load_demo_artifact()
    table = Path(__file__).resolve().parents[1] / "results" / "demo" / "feature_importance.csv"
    with table.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows and all(row["fit_partition"] == "train" for row in rows)
    assert all(int(row["split_seed"]) == artifact.run_seed for row in rows)
    ranked_mean = [row["feature"] for row in rows if row["feature"].startswith("mean ")]
    assert tuple(ranked_mean[:6]) == artifact.guided_features
