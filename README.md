# Student Academic Success

Analysis of factors relating to university students dropping out, staying enrolled, or graduating using the UCI Higher Education Student Retention dataset (~4,424 students and 37 features).

## Contents

- `student_academic_success.ipynb` — Exploratory data analysis notebook (gender distribution, nationality diversity, scholarship correlation, curricular units & GPA by target outcome).
- `analyze_academic_success.py` — Reproducible data loading, validation, and statistical summary functions backing the notebook analyses.
- `tests/test_analysis.py` — Automated test suite verifying schema validation, notebook structural integrity, and statistical summaries across edge cases.

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

