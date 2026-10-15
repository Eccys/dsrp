import json
from pathlib import Path
import sys
import urllib.request

import pytest

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

from analyze_academic_success import (
    add_human_readable_labels,
    compute_crosstab_counts,
    compute_target_distribution,
    load_dataset,
    load_rows_from_csv_text,
    mean_numeric_by_target,
    outcome_rates_by_group,
    summarize_numeric_by_target,
    target_distribution,
    validate_columns,
)

SAMPLE_CSV = """\ufeffMarital status;Daytime/evening attendance;Previous qualification (grade);Scholarship holder;Age at enrollment;Target
1;1;122.0;0;20;Dropout
1;1;160.0;1;19;Graduate
1;0;100.0;0;45;Dropout
2;0;140.0;1;22;Enrolled
"""


def test_notebook_structure_and_cell_ids():
    nb_path = REPO_DIR / "student_academic_success.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert "cells" in nb
    assert len(nb["cells"]) == 17
    for idx, cell in enumerate(nb["cells"]):
        assert cell.get("id"), f"Cell {idx} is missing top-level id"


def test_load_rows_and_labels():
    rows = load_rows_from_csv_text(SAMPLE_CSV)
    validate_columns(rows)
    assert len(rows) == 4
    assert rows[0]["scholarship_label"] == "No scholarship"
    assert rows[1]["scholarship_label"] == "Scholarship"
    assert rows[0]["attendance_label"] == "Daytime"
    assert rows[2]["attendance_label"] == "Evening"

    # Direct call with whitespace or integer values
    manual = [{"Scholarship holder": " 1 ", "Daytime/evening attendance": 0}]
    add_human_readable_labels(manual)
    assert manual[0]["scholarship_label"] == "Scholarship"
    assert manual[0]["attendance_label"] == "Evening"


def test_target_distribution_and_crosstabs():
    rows = load_rows_from_csv_text(SAMPLE_CSV)
    dist = target_distribution(rows)
    assert dist == compute_target_distribution(rows)
    assert dist["Dropout"] == {"count": 2, "percent": 50.0}
    assert dist["Graduate"] == {"count": 1, "percent": 25.0}
    assert dist["Enrolled"] == {"count": 1, "percent": 25.0}

    counts = compute_crosstab_counts(rows, "scholarship_label")
    assert counts["No scholarship"] == {"Dropout": 2, "Enrolled": 0, "Graduate": 0}

    by_scholarship = outcome_rates_by_group(rows, "scholarship_label")
    assert by_scholarship["No scholarship"] == {"Dropout": 100.0, "Enrolled": 0.0, "Graduate": 0.0}
    assert by_scholarship["Scholarship"] == {"Dropout": 0.0, "Enrolled": 50.0, "Graduate": 50.0}

    means = mean_numeric_by_target(rows, "Previous qualification (grade)")
    assert means == summarize_numeric_by_target(rows, "Previous qualification (grade)")
    assert means["Dropout"] == 111.0
    assert means["Graduate"] == 160.0


def test_nan_inf_and_unknown_target_filtering():
    rows = load_rows_from_csv_text(SAMPLE_CSV)
    rows.append({
        "scholarship_label": "No scholarship",
        "Previous qualification (grade)": "nan",
        "Target": "Dropout",
    })
    rows.append({
        "scholarship_label": "No scholarship",
        "Previous qualification (grade)": "inf",
        "Target": "Dropout",
    })
    rows.append({
        "scholarship_label": "No scholarship",
        "Previous qualification (grade)": "150.0",
        "Target": "",
    })
    rows.append({
        "scholarship_label": None,
        "Previous qualification (grade)": "199.0",
        "Target": "UnknownOutcome",
    })
    rows.append({
        "scholarship_label": None,
        "Previous qualification (grade)": "not-a-number",
        "Target": "Graduate",
    })
    means = mean_numeric_by_target(rows, "Previous qualification (grade)")
    assert means["Dropout"] == 111.0
    assert "UnknownOutcome" not in means

    dist = target_distribution(rows)
    assert "UnknownOutcome" not in dist

    by_scholarship = outcome_rates_by_group(rows, "scholarship_label")
    assert by_scholarship["No scholarship"] == {"Dropout": 100.0, "Enrolled": 0.0, "Graduate": 0.0}
    assert by_scholarship["Unknown"] == {"Dropout": 0.0, "Enrolled": 0.0, "Graduate": 100.0}


def test_load_dataset_local_and_remote(tmp_path, monkeypatch):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(SAMPLE_CSV + "\n;;;\n", encoding="utf-8")
    local_rows = load_dataset(csv_file)
    assert len(local_rows) == 4

    class DummyResp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return SAMPLE_CSV.encode("utf-8-sig")

    monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout=20: DummyResp())
    remote_rows = load_dataset("https://example.com/dataset.csv")
    assert len(remote_rows) == 4


def test_empty_input_and_validation_edge_cases():
    assert load_rows_from_csv_text("") == []
    assert load_rows_from_csv_text("   \n\r\n  ") == []
    assert len(load_rows_from_csv_text("\n\r\n" + SAMPLE_CSV)) == 4
    assert target_distribution([]) == {}
    assert outcome_rates_by_group([], "scholarship_label") == {}
    assert mean_numeric_by_target([], "Age at enrollment") == {}

    # Booleans should not be coerced to 1/0 in labels or numeric means
    bool_rows = [{"Scholarship holder": True, "Daytime/evening attendance": False, "Age at enrollment": True, "Target": "Dropout"}]
    add_human_readable_labels(bool_rows)
    assert bool_rows[0]["scholarship_label"] == "Unknown"
    assert bool_rows[0]["attendance_label"] == "Unknown"
    assert mean_numeric_by_target(bool_rows, "Age at enrollment") == {}

    with pytest.raises(ValueError, match="no rows"):
        validate_columns([])
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_columns([{"Target": "Dropout"}])
    valid_rows = load_rows_from_csv_text(SAMPLE_CSV)
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_columns([valid_rows[0], {"Target": "Dropout"}])


