"""Student Academic Success dataset analysis utilities."""
from __future__ import annotations

import csv
import io
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


def load_rows_from_csv_text(csv_text: str) -> list[dict[str, str]]:
    """Parse semicolon-delimited student academic success CSV text into stripped row dicts."""
    clean_text = csv_text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(clean_text), delimiter=";")
    rows: list[dict[str, str]] = []
    for raw_row in reader:
        row = {k.strip(): (v.strip() if isinstance(v, str) else "") for k, v in raw_row.items() if k is not None}
        if not any(row.values()):
            continue
        row["scholarship_label"] = SCHOLARSHIP_MAP.get(row.get("Scholarship holder", ""), "Unknown")
        row["attendance_label"] = ATTENDANCE_MAP.get(row.get("Daytime/evening attendance", ""), "Unknown")
        rows.append(row)
    return rows


def load_dataset(source: str | Path = DATASET_URL) -> list[dict[str, str]]:
    """Load dataset rows from a local file path or remote URL."""
    path_str = str(source)
    if path_str.startswith(("http://", "https://")):
        with urllib.request.urlopen(path_str, timeout=20) as resp:
            text = resp.read().decode("utf-8-sig")
    else:
        text = Path(source).read_text(encoding="utf-8-sig")
    return load_rows_from_csv_text(text)


def target_distribution(rows: list[dict[str, str]]) -> dict[str, dict[str, float | int]]:
    """Compute counts and percentages for each Target category."""
    total = len(rows)
    counts = Counter(r.get("Target", "") for r in rows)
    result: dict[str, dict[str, float | int]] = {}
    for target, count in counts.most_common():
        pct = round((count / total) * 100, 1) if total > 0 else 0.0
        result[target] = {"count": count, "percent": pct}
    return result


def outcome_rates_by_group(rows: list[dict[str, str]], group_col: str) -> dict[str, dict[str, float]]:
    """Compute normalized row percentages across Dropout, Enrolled, and Graduate by group_col."""
    grouped: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        key = row.get(group_col, "Unknown")
        target = row.get("Target", "")
        grouped[key][target] += 1

    table: dict[str, dict[str, float]] = {}
    for key in sorted(grouped.keys()):
        total = sum(grouped[key].values())
        table[key] = {
            t: round((grouped[key][t] / total) * 100, 1) if total > 0 else 0.0
            for t in TARGETS
        }
    return table


def mean_numeric_by_target(rows: list[dict[str, str]], numeric_col: str) -> dict[str, float]:
    """Compute the mean of a numeric column grouped by Target."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        target = row.get("Target", "")
        raw_val = row.get(numeric_col, "")
        try:
            buckets[target].append(float(raw_val))
        except (TypeError, ValueError):
            continue
    return {target: round(statistics.mean(vals), 2) for target, vals in sorted(buckets.items()) if vals}
