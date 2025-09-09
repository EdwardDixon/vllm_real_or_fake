
import os, argparse, csv, json, base64, requests
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api")

JUDGE_PROMPT = (
    "You are a forensics assistant. Decide if this image is AI-generated or a real camera photo.\n"
    'Return JSON only: {"ai_prob": 0..1, "label": "ai"|"real", "rationale":"<≤2 short sentences>"}.\n'
    "Consider texture regularity, lighting/optics, material edges, typography, geometry. Ignore metadata/watermarks."
)

def encode_image(path):
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode()
    return "data:image/jpeg;base64," + b

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
            {"type":"text","text":JUDGE_PROMPT},
            {"type":"input_image","image":img_b64}
        ]
    }]
    r = requests.post(url, headers=headers, json={"model": model, "messages": messages, "temperature": 0}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def coerce(out_text):
    try:
        j = json.loads(out_text)
        p = float(j.get("ai_prob", 0.5))
        lbl = j.get("label","ai" if p>=0.5 else "real")
        rat = j.get("rationale","")
        p = max(0.0, min(1.0, p))
        if lbl not in ["ai","real"]:
            lbl = "ai" if p>=0.5 else "real"
        return {"ai_prob": p, "label": lbl, "rationale": rat}
    except Exception:
        return {"ai_prob": 0.5, "label":"real", "rationale":"parse-fallback"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="CSV with id,path,class,domain,split")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = open(args.out, "w", encoding="utf-8")
    with open(args.images, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        for row in tqdm(reader):
            img_b64 = encode_image(row["path"])
            try:
                txt = call_vlm(args.model, img_b64)
            except Exception as e:
                txt = "{}"
            coerced = coerce(txt)
            out.write(json.dumps({**row, **coerced, "model": args.model}) + "\n")
    out.close()

if __name__ == "__main__":
    main()
