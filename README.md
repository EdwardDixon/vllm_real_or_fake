**Elm Detector Probe**

Simple, scriptable tools to probe images with a Vision-Language Model (VLM):

- Judge whether an image looks AI-generated vs. real camera capture.
- Generate concise, SD-style prompts that describe an image.

This README assumes zero prior knowledge. Follow the Quickstart and you’ll be running in minutes.

**At A Glance**
- `elm-detector-probe/src/judge_remote.py`: Classifies images via OpenRouter VLM.
- `elm-detector-probe/src/promptgen_remote.py`: Produces image-to-text prompts via VLM.
- Requires an OpenRouter API key in `.env`.

**Requirements**
- Python 3.13+
- An OpenRouter account and API key

**Why JSONL**
- Tools emit JSON Lines (`.jsonl`) — one JSON object per line — which is easy to stream, diff, and post-process.

**Safety**
- Do not commit secrets. Keep `.env` local and out of version control.
- Be mindful of uploading sensitive images to third-party APIs.

**Quickstart**
- Create a virtual environment, add your API key, and run a sample command to generate prompts for a folder of images.

**What You’ll Get**
- Outputs like `out/prompts.jsonl` or `out/judge.jsonl` that you can parse with any JSON/CSV tool.

**Setup**
- Clone or open this repo locally.
- Pick one setup path: pip + venv (simple) or `uv` (fast resolver).

**Option A: pip + venv**
- macOS/Linux:
  - `python -m venv .venv && . .venv/bin/activate`
- Windows (PowerShell):
  - `python -m venv .venv; .\.venv\Scripts\Activate.ps1`
- Install deps:
  - `pip install -r elm-detector-probe/requirements.txt`

**Option B: uv**
- If you use `uv`, from repo root run:
  - `uv sync`

Note: Runtime scripts rely on `requests`, `pillow`, `tqdm`, `python-dotenv`, etc. Those are listed in `elm-detector-probe/requirements.txt`.

**Configure API Keys**
- Create a file named `.env` in the repo root with:
- `OPENROUTER_API_KEY=sk-or-...`
- Optional: `OPENROUTER_BASE_URL=https://openrouter.ai/api` (default used if unset)
- Get a key from your OpenRouter account dashboard.
- Never commit `.env`.

**Local Smoke Test**
- Verify your environment:
- `python main.py`
- Expected: prints `Hello from elm-detector-probe!`

**Run: Prompt Generation**
- Use `promptgen_remote.py` to turn images into semantic/style prompt JSON. It reads a directory of images (no recursion), so point it at a folder that directly contains images.
- Example (Bash/macOS/Linux):
- `python elm-detector-probe/src/promptgen_remote.py --in elm-detector-probe/data/real/outdoor --out out/prompts.jsonl --vlm '{"model":"qwen2-vl-7b-instruct"}'`
- Example (PowerShell):
- `python elm-detector-probe/src/promptgen_remote.py --in elm-detector-probe/data/real/outdoor --out out/prompts.jsonl --vlm '{"model":"qwen2-vl-7b-instruct"}'`
- Example (Windows CMD):
- `python elm-detector-probe\src\promptgen_remote.py --in elm-detector-probe\data\real\outdoor --out out\prompts.jsonl --vlm "{\"model\":\"qwen2-vl-7b-instruct\"}"`

What it does
- For each image in `--in`, calls the VLM and writes one JSON line with keys: `id`, `domain`, `real_path`, `prompt`.

Sample output line (formatted)
- `{ "id": "PXL_20220625_193744809", "domain": "outdoor", "real_path": "elm-detector-probe/data/real/outdoor/PXL_20220625_193744809.jpg", "prompt": { "semantic": "sunlit coastal path with lighthouse in distance", "style": ["photo-realistic", "natural light"], "neg": ["text", "watermark"] } }`

Input folder layout tips
- This script looks one level deep (no recursion). Pass the specific folder that has images directly inside it. For example, use `--in elm-detector-probe/data/real/outdoor` rather than the parent `.../real`.

**Run: AI vs. Real Judge**
- `judge_remote.py` classifies images as AI vs. real from a CSV. The CSV must include: `id,path,class,domain,split`.

Minimal CSV example
- Save as `out/images.csv`:
- `id,path,class,domain,split`
- `img01,elm-detector-probe/data/real/outdoor/PXL_20220625_193744809.jpg,real,outdoor,test`
- `img02,elm-detector-probe/data/real/indoor/PXL_20250904_141952088.jpg,real,indoor,test`

Run the judge
- Bash/macOS/Linux:
- `python elm-detector-probe/src/judge_remote.py --images out/images.csv --model "qwen2-vl-7b-instruct" --out out/judge.jsonl`
- Windows PowerShell:
- `python elm-detector-probe/src/judge_remote.py --images out/images.csv --model "qwen2-vl-7b-instruct" --out out/judge.jsonl`

Output format
- Each line merges your CSV row with fields: `ai_prob` (0..1), `label` (`ai` or `real`), `rationale` (≤2 short sentences), and `model`.

Sample output line (formatted)
- `{ "id": "img01", "path": ".../PXL_20220625_193744809.jpg", "class": "real", "domain": "outdoor", "split": "test", "ai_prob": 0.23, "label": "real", "rationale": "natural lens artifacts and lighting", "model": "qwen2-vl-7b-instruct" }`

Create a CSV from a folder (optional helper)
- Quick Python snippet to scan a folder and emit `out/images.csv` with required columns (domain = folder name, split = `test`):
- `python - << 'PY'
import csv, os, pathlib
indir = 'elm-detector-probe/data/real/outdoor'  # change me
rows = []
for fn in os.listdir(indir):
    if fn.lower().endswith(('.jpg','.jpeg','.png','.webp','.bmp')):
        path = os.path.join(indir, fn)
        rows.append({
            'id': pathlib.Path(fn).stem,
            'path': path,
            'class': 'real',
            'domain': os.path.basename(indir),
            'split': 'test',
        })
os.makedirs('out', exist_ok=True)
with open('out/images.csv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['id','path','class','domain','split'])
    w.writeheader(); w.writerows(rows)
print('Wrote out/images.csv with', len(rows), 'rows')
PY`

**Model Selection**
- Use any OpenRouter VLM compatible with `chat.completions` and image inputs.
- Examples: `qwen2-vl-7b-instruct` (fast, low-cost), or other VLMs available to your account.
- For `promptgen_remote.py`, pass the model via `--vlm '{"model":"..."}'`.
- For `judge_remote.py`, pass it via `--model "..."`.

**Troubleshooting**
- Missing key: ensure `.env` has `OPENROUTER_API_KEY` and you restarted your shell or reloaded env.
- Auth/401: confirm your key is active and allowed for the chosen model.
- Timeouts: large images or slow networks can hit the 120s request timeout; retry on smaller batches.
- Empty outputs: for `promptgen_remote.py`, ensure `--in` folder directly contains images (no nested subfolders). For `judge_remote.py`, confirm `path` values in CSV are valid.
- JSON argument quoting: when passing `--vlm '{"model":"..."}'`, PowerShell and Bash handle single quotes; in CMD use double quotes and escape inner quotes.

**Data & Outputs**
- Inputs: images (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`).
- Outputs: JSONL files under `out/`. Each line is a standalone JSON object.
- Suggested: do not commit `out/` for large files; treat as artifacts.

**Project Layout**
- Repo root: entry point `main.py`, packaging metadata `pyproject.toml`, lockfile `uv.lock`.
- Tools: `elm-detector-probe/src/judge_remote.py`, `elm-detector-probe/src/promptgen_remote.py`, shared utils `elm-detector-probe/src/utils.py`.
- Data (example images): `elm-detector-probe/data/...` (you can point scripts at your own folders).
- Deps: `elm-detector-probe/requirements.txt`.

**Dev Notes**
- Style: 4-space indent; prefer type hints where practical.
- Imports: stdlib → third-party → local; explicit imports.
- Formatting: prefer `black` (88 cols) and `ruff` if available; otherwise keep consistent style.
- Tests: add `pytest` in dev and place tests under `tests/` (`test_*.py`). Mock network calls.

**How It Works**
- Both scripts call OpenRouter’s `v1/chat/completions` with an image encoded as a `data:` URL, then coerce the model response into JSON.
- `judge_remote.py` writes one JSONL line per CSV row with the model’s assessment.
- `promptgen_remote.py` writes one JSONL line per image with a compact prompt JSON: `{semantic, style[], neg[]}`.

**Next Steps**
- Want a CLI wrapper, tests, or batch parallelism? Open an issue or ask for a PR plan.
