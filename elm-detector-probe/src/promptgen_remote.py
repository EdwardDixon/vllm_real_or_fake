import os, sys
sys.path.append(os.path.dirname(__file__))

import argparse, json, requests
from glob import glob
from tqdm import tqdm
from dotenv import load_dotenv
from utils import read_image_b64, parse_json_from_text

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api")

PROMPT = (
    "You are a visual prompt engineer. Given an input image, output JSON:\n"
    '{"semantic": "...", "style": ["...","..."], "neg": ["...","..."]}\n'
    "Rules: avoid brand names, exact text, and unique faces; target Stable Diffusion style prompts. "
    "Keep semantic concise.\nReturn JSON only."
)

def call_vlm(model, img_b64):
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://local",
        "X-Title": "elm-detector-probe",
        "Content-Type": "application/json",
    }
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": img_b64}},
            ],
        }
    ]
    payload = {"model": model, "messages": messages, "temperature": 0.2}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code >= 400:
        raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}", response=r)

    print("Returned: ", r.json())
    return r.json()["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", dest="out_path", required=True)
    ap.add_argument("--vlm", dest="vlm_json", required=False, help='JSON, e.g. {"model":"qwen2-vl-7b-instruct"}')
    ap.add_argument("--model", dest="model", required=False, help="VLM model name, e.g. qwen2-vl-7b-instruct")
    ap.add_argument("--on-error", choices=["record","skip","halt"], default="record",
                    help="How to handle per-item errors: record to JSONL, skip the item, or halt immediately.")
    ap.add_argument("--fail-on-error", action="store_true",
                    help="Exit with code 1 if any errors occurred (after processing).")
    args = ap.parse_args()
    if args.model:
        vlm = {"model": args.model}
    elif args.vlm_json:
        try:
            vlm = json.loads(args.vlm_json)
        except json.JSONDecodeError as e:
            raise SystemExit(
                f"--vlm JSON parse error: {e}. Tip (PowerShell): use --model qwen2-vl-7b-instruct, or escape quotes like --vlm \"{{`\"model`\":`\"qwen2-vl-7b-instruct`\"}}\""
            )
    else:
        raise SystemExit("Provide either --model <name> or --vlm '<json>'")
    rows = []
    errors = 0
    paths = []
    for domain in os.listdir(args.indir):
        dpath = os.path.join(args.indir, domain)
        if not os.path.isdir(dpath): continue
        for fn in os.listdir(dpath):
            if fn.lower().endswith((".jpg",".jpeg",".png")):
                paths.append(os.path.join(dpath, fn))

    for path in tqdm(paths):
        domain = os.path.basename(os.path.dirname(path))
        img_b64 = read_image_b64(path)
        try:
            out = call_vlm(vlm["model"], img_b64)
            j = parse_json_from_text(out)
            rec = {"id": os.path.splitext(os.path.basename(path))[0],
                   "domain": domain, "real_path": path, "prompt": j, "model": vlm["model"], "ok": True}
            rows.append(rec)
        except Exception as e:
            errors += 1
            if args.on_error == "halt":
                raise
            elif args.on_error == "skip":
                continue
            else:  # record
                rec = {"id": os.path.splitext(os.path.basename(path))[0],
                       "domain": domain, "real_path": path, "prompt": None, "model": vlm["model"],
                       "ok": False, "error": str(e)}
                rows.append(rec)
    with open(args.out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if errors and args.fail_on_error:
        sys.exit(1)

if __name__ == "__main__":
    main()
