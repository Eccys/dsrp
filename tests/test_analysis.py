import json
from pathlib import Path

from analyze_academic_success import (
    load_rows_from_csv_text,
    mean_numeric_by_target,
    outcome_rates_by_group,
    target_distribution,
)


REPO_DIR = Path(__file__).resolve().parent.parent

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
    assert len(rows) == 4
    assert rows[0]["scholarship_label"] == "No scholarship"
    assert rows[1]["scholarship_label"] == "Scholarship"
    assert rows[0]["attendance_label"] == "Daytime"
    assert rows[2]["attendance_label"] == "Evening"


def test_target_distribution_and_crosstabs():
    rows = load_rows_from_csv_text(SAMPLE_CSV)
    dist = target_distribution(rows)
    assert dist["Dropout"] == {"count": 2, "percent": 50.0}
    assert dist["Graduate"] == {"count": 1, "percent": 25.0}
    assert dist["Enrolled"] == {"count": 1, "percent": 25.0}

    by_scholarship = outcome_rates_by_group(rows, "scholarship_label")
    assert by_scholarship["No scholarship"] == {"Dropout": 100.0, "Enrolled": 0.0, "Graduate": 0.0}
    assert by_scholarship["Scholarship"] == {"Dropout": 0.0, "Enrolled": 50.0, "Graduate": 50.0}

    means = mean_numeric_by_target(rows, "Previous qualification (grade)")
    assert means["Dropout"] == 111.0
    assert means["Graduate"] == 160.0


def test_empty_input_edge_cases():
    assert load_rows_from_csv_text("") == []
    assert target_distribution([]) == {}
    assert outcome_rates_by_group([], "scholarship_label") == {}
    assert mean_numeric_by_target([], "Age at enrollment") == {}
