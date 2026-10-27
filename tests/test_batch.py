import csv
import io

import pytest

from raa.app.demo_assets import load_demo_artifact
from raa.data import load_breast_cancer_data
from raa.inference import CaseInputError, csv_template, predict_csv


def _csv_text(features, row_count=1):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(features.feature_names)
    for index in range(row_count):
        writer.writerow(features.features[index].tolist())
    return output.getvalue()


def test_csv_template_and_valid_batch_are_in_memory(tmp_path):
    artifact = load_demo_artifact()
    data = load_breast_cancer_data()
    template = csv_template(data.feature_names)
    assert next(csv.reader(io.StringIO(template))) == list(data.feature_names)
    before = list(tmp_path.iterdir())

    batch = predict_csv(_csv_text(data), context=artifact.inference_context)

    assert len(batch) == 1
    assert batch[0].row_number == 2
    assert batch[0].record.level.value in ("Automatic", "Assisted", "Human Review")
    assert before == list(tmp_path.iterdir())


def test_csv_empty_malformed_and_over_limit_cases():
    artifact = load_demo_artifact()
    data = load_breast_cancer_data()
    context = artifact.inference_context
    with pytest.raises(CaseInputError, match="at least one row"):
        predict_csv("", context=context)
    with pytest.raises(CaseInputError, match="columns do not match"):
        predict_csv("case_id,age\\n1,22\\n", context=context)
    with pytest.raises(CaseInputError, match="exceeds the 1-row limit"):
        predict_csv(_csv_text(data, row_count=2), context=context, max_rows=1)
    missing = _csv_text(data).replace(str(data.features[0, 0]), "", 1)
    with pytest.raises(CaseInputError, match="is empty"):
        predict_csv(missing, context=context)
