from raa.app.demo_assets import DEFAULT_RUN_DIR, load_demo_artifact
from raa.inference import reroute_case_record, thresholds_for_review_capacity
from raa.pipeline import DecisionSystem


def test_capacity_maps_through_validation_and_default_is_70_90():
    artifact = load_demo_artifact()
    default, automatic, assisted = thresholds_for_review_capacity(artifact.validation_risks, 30)
    exploratory, auto_p, assist_p = thresholds_for_review_capacity(artifact.validation_risks, 20)
    row = [artifact.inference_context.imputer._fit_X[0]]
    record = artifact.system.predict(row)[0]
    updated = reroute_case_record(record, exploratory, artifact.system.weights)
    results_file = DEFAULT_RUN_DIR / "metrics.json"
    original_metrics = results_file.read_bytes()

    assert isinstance(artifact.system, DecisionSystem)
    assert (automatic, assisted) == (70.0, 90.0)
    assert default == artifact.system.thresholds
    assert (auto_p, assist_p) == (80.0, 100 - 20 / 3)
    assert exploratory.automatic_max <= exploratory.assisted_max
    assert updated.risk == record.risk
    assert updated.predicted_class == record.predicted_class
    assert updated.level == exploratory.route_one(record.risk)
    assert results_file.read_bytes() == original_metrics
