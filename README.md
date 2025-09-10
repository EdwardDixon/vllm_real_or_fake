**Elm Detector Probe**

Compact tools to generate prompts from images, synthesize images from prompts, judge images as AI vs. real, and score results — all via OpenRouter.

**What Is OpenRouter?**
- OpenRouter is an API gateway to many AI models (text, vision, image). You use one API key and choose models by slug like `qwen/qwen-2.5-vl-7b-instruct` (VLM) or `google/gemini-2.5-flash-image-preview` (image).
- Create an account and API key at `https://openrouter.ai`. Keep your key private in `.env`.

**Setup**
- Requirements: Python 3.13+, and either `uv` or `pip`.
- Configure environment in repo root:
  - `.env` with `OPENROUTER_API_KEY=sk-or-...`
  - Optional: `OPENROUTER_BASE_URL=https://openrouter.ai/api`
- Install deps:
  - `uv sync` (recommended)
  - or `pip install -r elm-detector-probe/requirements.txt`

**Data Flow**
- promptgen → synth → normalize → judge → metrics
- `promptgen_remote.py`: VLM → prompts JSONL from real images.
- `synth_remote.py`: Image model → JPEGs from prompts.
- `normalize.py`: Resize/standardize and build an eval `manifest.csv`.
- `judge_remote.py`: VLM classifier → JSONL of AI-vs-Real.
- `metrics.py`: Summaries (AUROC, Balanced Accuracy, F1, Brier).

**Tools**
- `promptgen_remote.py`: Generate prompts from images
- `synth_remote.py`: Synthesize images from prompts
- `normalize.py`: Normalize images and create manifest
- `judge_remote.py`: Judge AI vs. real from CSV
- `metrics.py`: Summarize predictions

**Prompt Generation**
- Input: a directory whose immediate subfolders contain images (one level deep).
- Example:
- `uv run python elm-detector-probe/src/promptgen_remote.py --in elm-detector-probe/data/real --out out/prompts.real.jsonl --model qwen/qwen-2.5-vl-7b-instruct`
- Output JSONL per image: `{id, domain, real_path, prompt}`

**Synthesize Images**
- Input: prompts JSONL from promptgen.
- PowerShell:
- `uv run python .\elm-detector-probe\src\synth_remote.py --in .\out\prompts.real.jsonl --out .\elm-detector-probe\data\synthetic --model google/gemini-2.5-flash-image-preview`
- Bash/macOS/Linux:
- `uv run python elm-detector-probe/src/synth_remote.py --in out/prompts.real.jsonl --out elm-detector-probe/data/synthetic --model google/gemini-2.5-flash-image-preview`
- Output: `data/synthetic/<domain>/<id>.jpg`

**Normalize + Manifest**
- Purpose: standardize images and produce an evaluation manifest.
- Example:
- `uv run python elm-detector-probe/src/normalize.py --real elm-detector-probe/data/real --synthetic elm-detector-probe/data/synthetic --out elm-detector-probe/data/eval`
- Output: images under `data/eval/{clean,perturbed}/{real,ai}/<domain>/...` and `data/eval/manifest.csv` with header `id,path,class,domain,split`.

**Judge AI vs. Real**
- Input: CSV manifest (id,path,class,domain,split). Each `path` must be a file (not a directory).
- Example:
- `uv run python elm-detector-probe/src/judge_remote.py --images elm-detector-probe/data/eval/manifest.csv --model "qwen/qwen-2.5-vl-7b-instruct" --out out/judgements.jsonl`
- Output JSONL per row: input fields plus `{ai_prob, label, rationale, ok, model}`.

**Metrics**
- Input: judgements JSONL from judge.
- Example:
- `uv run python elm-detector-probe/src/metrics.py --preds out/judgements.jsonl --name run1`
- Prints overall and per-domain/split AUROC, Balanced Accuracy, F1, Brier.

**Model Slugs**
- Always use the full family/name slug shown in OpenRouter.
- VLM examples: `qwen/qwen-2.5-vl-7b-instruct`, `google/gemini-1.5-flash`.
- Image examples: `google/gemini-2.5-flash-image-preview`, `black-forest-labs/flux-schnell`.

**Tips & Troubleshooting**
- Secrets: keep `.env` private; do not commit.
- Paths: in CSVs, use forward slashes (`/`) for portability; ensure `path` is a file.
- PowerShell quoting: prefer `--model <slug>`. If using `--vlm`, escape inner quotes with backticks.
- Rate limits/timeouts: try smaller batches or lighter models.
- Samples: see `out/` for example JSONL outputs you can diff or parse.

**Local Smoke**
- `uv run python main.py` → prints a hello message.

**Project Layout**
- Tools live in `elm-detector-probe/src/` (see scripts above).
- Data lives under `elm-detector-probe/data/`.
- Outputs default to `out/` for JSONL artifacts.

