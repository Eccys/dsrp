"""Student Academic Success dataset analysis utilities."""
from __future__ import annotations

import csv
import io
import math
import statistics
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

DATASET_URL = (
    "https://raw.githubusercontent.com/frontiertechinstitute/datasets/main/"
    "University%20Student%20Academic%20Success%20Dataset/university_student_academic_success_dataset.csv"
)

SCHOLARSHIP_MAP = {"1": "Scholarship", "0": "No scholarship", 1: "Scholarship", 0: "No scholarship"}
ATTENDANCE_MAP = {"1": "Daytime", "0": "Evening", 1: "Daytime", 0: "Evening"}
TARGETS = ("Dropout", "Enrolled", "Graduate")
REQUIRED_COLUMNS = (
    "Marital status",
    "Daytime/evening attendance",
    "Previous qualification (grade)",
    "Scholarship holder",
    "Age at enrollment",
    "Target",
)


def validate_columns(rows: list[dict[str, str]], required: tuple[str, ...] = REQUIRED_COLUMNS) -> None:
    """Validate that required dataset columns exist in the parsed rows."""
    if not rows:
        raise ValueError("Dataset contains no rows")
    present = set(rows[0].keys())
    missing = [col for col in required if col not in present]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def add_human_readable_labels(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Populate scholarship_label and attendance_label on row dicts."""
    for row in rows:
        raw_sch = row.get("Scholarship holder", "")
        sch_key = raw_sch.strip() if isinstance(raw_sch, str) else raw_sch
        raw_att = row.get("Daytime/evening attendance", "")
        att_key = raw_att.strip() if isinstance(raw_att, str) else raw_att
        row["scholarship_label"] = SCHOLARSHIP_MAP.get(sch_key, "Unknown")
        row["attendance_label"] = ATTENDANCE_MAP.get(att_key, "Unknown")
    return rows


def load_rows_from_csv_text(csv_text: str) -> list[dict[str, str]]:
    """Parse semicolon-delimited student academic success CSV text into stripped row dicts."""
    clean_text = csv_text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(clean_text), delimiter=";")
    rows: list[dict[str, str]] = []
    for raw_row in reader:
        row = {k.strip(): (v.strip() if isinstance(v, str) else "") for k, v in raw_row.items() if k is not None}
        if not any(row.values()):
            continue
        rows.append(row)
    return add_human_readable_labels(rows)


def load_dataset(source: str | Path = DATASET_URL) -> list[dict[str, str]]:
    """Load dataset rows from a local file path or remote URL."""
    path_str = str(source)
    if path_str.startswith(("http://", "https://")):
        with urllib.request.urlopen(path_str, timeout=20) as resp:
            text = resp.read().decode("utf-8-sig")
    else:
        text = Path(source).read_text(encoding="utf-8-sig")
    return load_rows_from_csv_text(text)


def _valid_target(row: dict[str, str]) -> str | None:
    raw = row.get("Target", "")
    target = raw.strip() if isinstance(raw, str) else str(raw or "").strip()
    return target if target in TARGETS else None


def target_distribution(rows: list[dict[str, str]]) -> dict[str, dict[str, float | int]]:
    """Compute counts and percentages for each valid Target category."""
    targets = [t for r in rows if (t := _valid_target(r)) is not None]
    total = len(targets)
    counts = Counter(targets)
    result: dict[str, dict[str, float | int]] = {}
    for target, count in counts.most_common():
        pct = round((count / total) * 100, 1) if total > 0 else 0.0
        result[target] = {"count": count, "percent": pct}
    return result


def compute_target_distribution(rows: list[dict[str, str]]) -> dict[str, dict[str, float | int]]:
    """Alias for target_distribution."""
    return target_distribution(rows)


def compute_crosstab_counts(rows: list[dict[str, str]], group_col: str) -> dict[str, dict[str, int]]:
    """Compute raw counts across Dropout, Enrolled, and Graduate by group_col."""
    grouped: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        target = _valid_target(row)
        if target is None:
            continue
        raw_key = row.get(group_col)
        key = str(raw_key).strip() if raw_key is not None and str(raw_key).strip() != "" else "Unknown"
        grouped[key][target] += 1
    return {
        key: {t: grouped[key][t] for t in TARGETS}
        for key in sorted(grouped.keys())
    }


def outcome_rates_by_group(rows: list[dict[str, str]], group_col: str) -> dict[str, dict[str, float]]:
    """Compute normalized row percentages across Dropout, Enrolled, and Graduate by group_col."""
    counts_by_group = compute_crosstab_counts(rows, group_col)
    table: dict[str, dict[str, float]] = {}
    for key, counts in counts_by_group.items():
        total = sum(counts.values())
        table[key] = {
            t: round((counts[t] / total) * 100, 1) if total > 0 else 0.0
            for t in TARGETS
        }
    return table


def mean_numeric_by_target(rows: list[dict[str, str]], numeric_col: str) -> dict[str, float]:
    """Compute the mean of a finite numeric column grouped by valid Target."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        target = _valid_target(row)
        if target is None:
            continue
        raw_val = row.get(numeric_col, "")
        try:
            val = float(raw_val)
        except (TypeError, ValueError):
            continue
        if math.isfinite(val):
            buckets[target].append(val)
    return {target: round(statistics.mean(vals), 2) for target, vals in sorted(buckets.items()) if vals}


def summarize_numeric_by_target(rows: list[dict[str, str]], numeric_col: str) -> dict[str, float]:
    """Alias for mean_numeric_by_target."""
    return mean_numeric_by_target(rows, numeric_col)


