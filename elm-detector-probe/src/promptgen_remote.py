
import os, argparse, json, requests, base64, glob
from tqdm import tqdm
from dotenv import load_dotenv
from PIL import Image
# Ensure local utils.py is importable whether run from repo root or within src
try:
    from utils import read_image_b64
except Exception:
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from utils import read_image_b64

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
        "X-Title": "elm-detector-probe"
    }
    messages = [{
        "role":"user",
        "content":[
            {"type":"text","text":PROMPT},
            {"type":"input_image","image":img_b64}
        ]
    }]
    payload = {"model": model, "messages": messages, "temperature": 0.2}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", dest="out_path", required=True)
    ap.add_argument("--vlm", dest="vlm_json", required=True, help='e.g. {"model":"qwen2-vl-7b-instruct"}')
    args = ap.parse_args()
    vlm = json.loads(args.vlm_json)
    rows = []
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
            j = json.loads(out)
        except Exception as e:
            j = {"semantic": f"{domain} scene, natural lighting", "style": ["photo-realistic"], "neg": ["text","watermark"]}
        rows.append({"id": os.path.splitext(os.path.basename(path))[0],
                     "domain": domain, "real_path": path, "prompt": j})
    with open(args.out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
