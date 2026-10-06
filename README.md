# AutoResearch for Computational Social Science

[中文版 README](README.zh-CN.md)

> Give it a dataset and a vague research direction. Let it look for something worth checking.

This is an early prototype of an AutoResearch loop for computational social science.

Karpathy's `autoresearch` works because the loop is small and explicit: change one thing, run a fixed experiment, keep or discard the change. There is no reason to copy the model-training part for social science. The useful part is the discipline.

Here the loop is:

```text
research direction
    → candidate questions
    → data audit
    → cheap empirical checks
    → ranked shortlist
    → human review
```

The intended use is an overnight research scout. In the morning, it should give you two or three questions that are interesting enough to investigate—not pretend that it has written a paper or discovered a theory.

## What it does today

The current MVP takes a local CSV, JSON, or JSONL file and:

- profiles the columns and missing values;
- separates numeric and categorical variables;
- generates several mechanism-shaped candidate questions;
- runs a small correlation-based feasibility check;
- ranks the candidates;
- writes a JSON report with the dataset hash and the evidence used for ranking.

It is intentionally boring. The first version should make the research trail inspectable before it becomes ambitious.

## Run it

```bash
python -m autoresearch_css.cli examples/demo.csv \
  --direction "国家信息能力与公众信任" \
  --count 10 \
  --out report.json
```

The command prints the top three candidates and writes the complete report to `report.json`.

Try it with your own data:

```bash
python -m autoresearch_css.cli /path/to/data.csv \
  --direction "你的研究方向" \
  --count 20 \
  --out my_run.json
```

No external services or Python packages are required for this MVP.

## What the score means

The score is a triage score, not a scientific result. It combines:

- whether the required variables are present;
- the size of the initial empirical signal;
- a fixed theoretical-value prior;
- a provisional novelty prior;
- a small risk penalty.

The correlation check answers only: **is this worth looking at next?** It does not answer whether the relationship is causal, generalisable, or publishable.

The novelty field is also not a claim that nobody has done the work. A real run needs a literature search, close-reading, citation tracing, and a human researcher willing to defend the difference.

## The important constraint

This project is not an autonomous paper-writing machine.

It should not:

- turn a correlation into a causal claim;
- announce that a question is novel without checking the literature;
- search the open web without a source, licence, and access policy;
- merge personal records across datasets;
- silently change a registered analysis after seeing the result;
- publish a conclusion without human review.

A useful agent is allowed to fail. It is not allowed to hide why it failed.

## Why this is different from `autoresearch`

The transferable idea is the experiment loop:

- define the part the agent may change;
- keep the data and evaluation protocol stable;
- run a bounded experiment;
- record the result;
- keep useful work and discard weak work.

The non-transferable idea is a single fast metric. Social-science evidence is not one number. A serious run has to keep track of theory, measurement, identification, uncertainty, robustness, representativeness, ethics, and provenance. Those checks are slower and often disagree with each other. That is a feature, not a bug.

## Planned loop

The next version will make the loop explicit:

1. **Frame** — turn the research direction into a population, unit, mechanism, outcome, and constraint.
2. **Diverge** — generate 20–50 candidates across theory, mechanism, subgroup, time, and method.
3. **Screen** — remove duplicates and score feasibility, contribution, identification, cost, and risk.
4. **Lock** — let the researcher choose a question and freeze the estimand, sample, primary outcome, and stopping rule.
5. **Audit** — check schema, missingness, duplicates, coverage, sensitive fields, and data provenance.
6. **Scout** — search the literature and produce a dated “nearest work / difference / possible contribution” table.
7. **Run** — execute a small, reproducible analysis with fixed seeds and recorded inputs.
8. **Attack** — try alternative explanations, placebo tests, sensitivity checks, and obvious leakage paths.
9. **Reproduce** — rerun from a clean environment and compare the artifacts.
10. **Report** — return a research card and a decision log. A human decides what becomes research.

Only the first pieces of this list are implemented here.

## Data collection

The MVP only reads local files. This is deliberate.

If external data collection is added, it will use explicit connectors rather than an unrestricted browser agent. Each connector should record the source, terms, retrieval time, version, hash, fields, rate limit, retention rule, and whether a human approved access.

The default should be metadata and feasibility checks first. Full downloads, sensitive data, identity linkage, and redistribution should require an explicit approval step.

## Project layout

```text
.
├── autoresearch_css/
│   ├── core.py        # profiling, question generation, scoring, manifest
│   └── cli.py         # command-line entry point
├── examples/
│   └── demo.csv
├── pyproject.toml
├── README.md
└── README.zh-CN.md
```

## Status

This is a research prototype, not a finished framework. The current implementation is useful for testing the shape of the loop and the report format. It is not yet suitable for confirmatory analysis.

The next useful additions are not more autonomous cleverness. They are:

- regression and uncertainty estimates;
- a proper analysis manifest and preregistration lock;
- Parquet/DuckDB support;
- literature retrieval with citations and timestamps;
- robustness and placebo templates;
- a clean-environment reproduction command;
- an append-only experiment log;
- human approval gates for data access and release.

If those pieces work, the agent can run overnight without turning the morning into archaeology.
