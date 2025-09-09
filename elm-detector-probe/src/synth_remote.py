import os, sys
sys.path.append(os.path.dirname(__file__))

import argparse, json, requests, base64
from tqdm import tqdm
from dotenv import load_dotenv
from utils import save_b64_jpg

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api")

def call_image_gen(model, prompt):
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://local",
        "X-Title": "elm-detector-probe"
    }
    payload = {
        "model": model,
        "messages": [{"role":"user","content":prompt}],
        "modalities": ["image", "text"]
    }
    r = requests.post(url, headers=headers, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()

    message = data["choices"][0]["message"]

    # New: handle `images`
    if "images" in message and message["images"]:
        img_obj = message["images"][0]
        img_url = img_obj["image_url"]["url"]

        if img_url.startswith("data:image"):
            # direct base64
            b64 = img_url.split(",",1)[1]
            return b64
        else:
            # fetch from URL
            img = requests.get(img_url, timeout=180).content
            return base64.b64encode(img).decode()

    raise RuntimeError(f"No image found in response: {json.dumps(message)[:200]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--out", dest="out_dir", required=True)
    ap.add_argument("--model", required=True, help="e.g., stability-ai/sdxl")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    with open(args.in_path, "r", encoding="utf-8") as f:
        for line in tqdm(f):
            try:
                row = json.loads(line)
            except Exception as e:
                print(f"[ERROR] Skipping malformed line: {e}", file=sys.stderr)
                continue

            # Skip rows without a usable prompt
            if "prompt" not in row or not row["prompt"] or isinstance(row["prompt"], str) and row["prompt"].startswith("error"):
                print(f"[SKIP] {row.get('id')} has no valid prompt", file=sys.stderr)
                continue

            prompt = row["prompt"].get("semantic") if isinstance(row["prompt"], dict) and "semantic" in row["prompt"] else row["prompt"]
            if not prompt:
                print(f"[SKIP] {row.get('id')} empty prompt structure", file=sys.stderr)
                continue

            neg = None
            if isinstance(row["prompt"], dict) and "neg" in row["prompt"]:
                neg = ", ".join(row["prompt"]["neg"])

            out_path = os.path.join(args.out_dir, row["domain"], f"{row['id']}.jpg")
            try:
                b64 = call_image_gen(args.model, prompt)
                save_b64_jpg(b64, out_path)
            except Exception as e:
                print(f"[ERROR] {row.get('id')} ({args.model}): {e}", file=sys.stderr)
                continue

if __name__ == "__main__":
    main()
