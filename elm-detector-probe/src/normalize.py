import os, sys
sys.path.append(os.path.dirname(__file__))

import argparse, csv, glob
from PIL import Image
from tqdm import tqdm
from utils import normalize_image, save_jpeg_strip_exif, perturb_light

def iter_images(root, label):
    if not os.path.isdir(root):
        return []
    out = []
    for path in glob.glob(os.path.join(root, "*", "*")):
        if path.lower().endswith((".jpg",".jpeg",".png")):
            domain = os.path.basename(os.path.dirname(path))
            out.append((path, domain, label))
    return out

def process(images, label, out_root, split, manifest):
    for path, domain, cls in tqdm(images, desc=f"{label}-{split}"):
        im = Image.open(path)
        imn = normalize_image(im, target_long=768)

        subdir = os.path.join(out_root, split, cls, domain)
        os.makedirs(subdir, exist_ok=True)

        fname = os.path.basename(path)
        outp = os.path.join(subdir, fname)
        save_jpeg_strip_exif(imn, outp, quality=80)
        manifest.append([os.path.splitext(fname)[0], outp, cls, domain, split])

        if split == "perturbed":
            ip = perturb_light(imn)
            outp2 = os.path.join(subdir, "perturbed_" + fname)
            save_jpeg_strip_exif(ip, outp2, quality=80)
            manifest.append([os.path.splitext(fname)[0], outp2, cls, domain, "perturbed"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", required=True, help="path to data/real")
    ap.add_argument("--synthetic", nargs="+", required=True,
                    help="one or more synthetic roots (e.g. data/synthetic data/synthetic2)")
    ap.add_argument("--out", required=True, help="output dir, e.g. data/eval")
    args = ap.parse_args()

    out_root = args.out
    os.makedirs(out_root, exist_ok=True)

    manifest = []

    # real images
    real_imgs = iter_images(args.real, "real")
    process(real_imgs, "real", out_root, "clean", manifest)
    process(real_imgs, "real", out_root, "perturbed", manifest)

    # synthetic images
    for synth_root in args.synthetic:
        synth_imgs = iter_images(synth_root, "ai")
        process(synth_imgs, "ai", out_root, "clean", manifest)
        process(synth_imgs, "ai", out_root, "perturbed", manifest)

    # write manifest
    csv_path = os.path.join(out_root, "manifest.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","path","class","domain","split"])
        w.writerows(manifest)

    print(f"Written manifest with {len(manifest)} rows to {csv_path}")

if __name__ == "__main__":
    main()
