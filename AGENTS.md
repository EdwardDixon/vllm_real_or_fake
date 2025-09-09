# Repository Guidelines

## Project Structure & Modules
- `main.py`: Entry point used for quick smoke runs.
- `pyproject.toml` / `uv.lock`: Python packaging metadata (Python ≥3.13) and lockfile (for `uv`).
- `elm-detector-probe/requirements.txt`: Runtime deps for remote tools.
- `elm-detector-probe/src/`:
  - `judge_remote.py`: Classifies images as AI vs. real via OpenRouter VLM.
  - `promptgen_remote.py`: Generates image-to-text prompts via VLM.
- `.env`: API keys and config (not committed).

## Build, Test, and Dev Commands
- Create env (pip): `python -m venv .venv && . .venv/bin/activate && pip install -r elm-detector-probe/requirements.txt`
- Create env (uv): `uv sync` (respects `uv.lock`).
- Run judge: `python elm-detector-probe/src/judge_remote.py --images data/images.csv --model "qwen2-vl-7b-instruct" --out out/judge.jsonl`
- Run promptgen: `python elm-detector-probe/src/promptgen_remote.py --in data/images_dir --out out/prompts.jsonl --vlm '{"model":"qwen2-vl-7b-instruct"}'`
- Local smoke: `python main.py`

## Coding Style & Naming
- Python: 4-space indent, type hints where practical.
- Names: modules `snake_case.py`, functions `snake_case`, classes `CapWords`.
- Imports: stdlib → third-party → local; prefer explicit imports.
- Formatting: favor `black` (line length 88) and `ruff` (lint); if not installed, keep consistent style.

## Testing Guidelines
- Framework: `pytest` (add to dev deps). Structure tests under `tests/`.
- Names: files `test_*.py`; functions `test_*`.
- Run: `pytest -q` (optionally `pytest --maxfail=1 -q`). Target critical paths in `src/`.
- Coverage: aim ≥80% for pure logic; network calls should be mocked.

## Commit & PR Guidelines
- Commits: concise, imperative subject; reference scope, e.g., `feat(judge): add JSONL output`.
- PRs: include description, motivation, sample commands, and before/after notes. Link issues. Attach small screenshots or JSONL snippets when relevant.
- CI/readiness: ensure scripts run locally, no secrets in diffs, and `.env` excluded.

## Security & Configuration
- Env vars: `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api`). Use `.env`; never commit keys.
- Network calls: respect timeouts; handle 4xx/5xx with retries only where safe.
- Data: prefer JSONL outputs under `out/`; avoid committing large binaries.

