# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ETL pipeline (college Big Data assignment) that consolidates NogTech transaction and student-engagement data. Built with **Luigi** for orchestration, **pandas/pyarrow** for processing, and **Docker** for containerization. Local CSV/JSON files are extracted, enriched against the public BrasilAPI (CEP → address, year → national holidays), anonymized for LGPD compliance, and written to a Parquet data lake partitioned by `ano/mes`. Requirements live in [documents/REQUISITOS.md](documents/REQUISITOS.md). Code identifiers, comments, and logs are in Portuguese — match that when editing.

## Commands

Dependency management uses **uv** (lockfile `uv.lock`, Python 3.13).

```bash
# Run the full pipeline locally (uses local Luigi scheduler — see scheduler note below)
uv run python main.py

# Run all tests (stdlib unittest, not pytest)
uv run python -m unittest discover tests

# Run a single test case
uv run python -m unittest tests.test_utils.TestUtils.test_format_cep

# Full Docker run (central scheduler + pipeline), first build:
docker-compose up --build
docker-compose up        # subsequent runs
docker-compose down

# Luigi scheduler UI (Docker only): http://localhost:8082
```

## Architecture

### Entry point & DAG construction
[main.py](main.py) configures logging then calls `luigi.build([LoadDataLakeTask()])`. Only the **terminal task** is named; the entire DAG is resolved backward through each task's `requires()`. To trace the flow you must read across multiple files in [pipelines/](pipelines). The dependency graph (leaf → root):

```
ExtractTransactionsTask ─► TransformTransactionsTask ─► EnrichTransactionsAddressTask ─► EnrichTransactionsHolidayTask ┐
                                                                                                                        ├─► TransformEnrichedDataTask ─► TransactionAnonymizationTask ─► LoadDataLakeTask
ExtractEngagementTask ──► TransformEngagementTask ──────────────────────────────────────────────────────────────────────┘
```

The two branches merge in `TransformEnrichedDataTask` via a **LEFT JOIN** on `['cpf_aluno', 'mes', 'ano']` (transactions are kept even with no engagement match). Anonymization (mask CPF to `***.456.789-**`, drop `nome_aluno`) happens last, just before the load.

### Task convention
Every Luigi task follows the same shape: `requires()` lists upstream tasks → `run()` reads the upstream Parquet via `self.input()[i].path`, transforms a pandas DataFrame, and writes via `save_df_to_parquet(...)` → `output()` returns a `luigi.LocalTarget`. All intermediate and final paths are **centralized as constants in [config/settings.py](config/settings.py)** and passed as task `Parameter` defaults — change paths there, not inline.

### Layers
- **`pipelines/`** — Luigi tasks grouped by ETL stage (`extract/`, `transform/`, `load/`). Enrichment and the final join live under `transform/`.
- **`infrastructure/services/`** — Each external integration has two classes: a thin BrasilAPI client (`brasil_api_*_service.py`, owns the `requests` session + retry config) and an *enrichment service* (`*_enrichment_service.py`) that orchestrates cache-lookup-then-fetch and exposes `enrich_dataframe(df, column)`. Tasks talk only to the enrichment service.
- **`infrastructure/cache/`** — JSON-file-backed caches (`AddressCache`, `HolidayCache`) persisted to `databases/*.json`. CEP cached per CEP; holidays cached per year. These satisfy the "never call the API twice for the same key" requirement.
- **`infrastructure/utils/`** — Pure formatting/IO helpers (`format_cpf`, `format_cep`, `format_date`, `format_float`, `anonymization_utils`, `file_utils`). This is what the unit tests cover.
- **`shared/responses/`** — Pydantic models for BrasilAPI responses (`CepResponse`, `HolidayResponse`).
- **`databases/`** — raw inputs (`transacoes_nogtech.csv` is `latin-1` + `;`-delimited; `engajamento_alunos.json` is utf-8) and the JSON caches.
- **`output/`** — `loaded/` → `processed/` → `transformed/` → `final/data_lake/` (partitioned Parquet). Parquet files are gitignored.

### Resilience & idempotency
- **Idempotency**: Luigi skips tasks whose `LocalTarget` output already exists, so re-runs don't reprocess. The final load uses `existing_data_behavior="overwrite_or_ignore"` (see `save_df_to_parquet` in [infrastructure/utils/file_utils.py](infrastructure/utils/file_utils.py)) with `ano/mes` partitioning to avoid duplicates. **To force a stage to re-run, delete its output file/dir under `output/`** (and the relevant `databases/*_cache.json` to force fresh API calls).
- **API resilience**: BrasilAPI clients use `urllib3` `Retry` with backoff on `429/5xx` plus a timeout (`API_TIMEOUT`/`API_RETRIES` in settings). On failure they log and return `None`/empty, so enrichment degrades gracefully rather than corrupting data.

### Configuration & the scheduler gotcha
Config is read via **python-decouple** in [config/settings.py](config/settings.py). decouple reads a `.env` file (gitignored) or process env vars, falling back to the defaults coded in `settings.py`; [.env.config](.env.config) is a reference template, not auto-loaded — copy it to `.env` to override defaults locally.

`PIPELINE_LOCAL_SCHEDULER` (env `LUIGI_LOCAL_SCHEDULER`) controls whether `main.py` connects to the central scheduler:
- **Default `True`** → `uv run python main.py` runs with an in-process scheduler, no UI, no Docker needed.
- **`False`** (set in `docker-compose.yml` and `.env.config`) → connects to the `luigi-scheduler` container on port 8082 (host/port from [luigi.cfg](luigi.cfg)). Running locally with `False` but no scheduler running will fail to connect.

`docker-compose.yml` runs two services: `luigi-scheduler` (`luigid`, healthchecked) and `etl-pipeline` (waits for the scheduler healthy, then runs `main.py`).
