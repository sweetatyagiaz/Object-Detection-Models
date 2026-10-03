"""
AdaFace Step 1: model setup + face preprocessing + embedding extraction.

Usage (from the folder that contains this file):
    python adaface_step1.py --repo ./AdaFace \
        --ckpt ./AdaFace/pretrained/adaface_ir101_webface4m.ckpt \
        --arch ir_101 --img1 a.jpg --img2 b.jpg
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


# ----------------------------------------------------------------------------
# 1. Model loading
# ----------------------------------------------------------------------------
def load_adaface(repo_dir: str, ckpt_path: str, arch: str = "ir_101", device: str = None):
    """Load a pretrained AdaFace backbone from the official repo."""
    repo_dir = str(Path(repo_dir).resolve())
    if repo_dir not in sys.path:
        sys.path.insert(0, repo_dir)

    import net  # from the AdaFace repo

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = net.build_model(arch)

    ckpt = torch.load(ckpt_path, map_location="cpu")
    state = ckpt["state_dict"] if "state_dict" in ckpt else ckpt
    # Lightning checkpoints prefix backbone weights with "model."
    state = {k[len("model."):]: v for k, v in state.items() if k.startswith("model.")}
    model.load_state_dict(state)

    model.to(device).eval()
    return model, device


# ----------------------------------------------------------------------------
# 2. Detection + alignment (MTCNN bundled in the AdaFace repo -> 112x112 RGB)
# ----------------------------------------------------------------------------
def get_aligned_face(image_path: str):
    """
    Detect the face and return a 112x112 aligned PIL RGB image, or None if no
    face is found. Uses the repo's own MTCNN + similarity-transform alignment,
    which matches how the model was trained.
    """
    from face_alignment import align  # from the AdaFace repo

    try:
        return align.get_aligned_face(str(image_path))
    except Exception as e:
        print(f"[warn] alignment failed for {image_path}: {e}")
        return None


# ----------------------------------------------------------------------------
# 3. Preprocessing: RGB PIL -> normalized BGR tensor
# ----------------------------------------------------------------------------
def to_input(pil_rgb_image: Image.Image) -> torch.Tensor:
    """
    AdaFace expects BGR channel order, scaled to [-1, 1]:
        (x / 255 - 0.5) / 0.5
    Returns a tensor of shape (1, 3, 112, 112).
    """
    arr = np.asarray(pil_rgb_image).astype(np.float32)
    bgr = arr[:, :, ::-1]                      # RGB -> BGR
    bgr = ((bgr / 255.0) - 0.5) / 0.5
    tensor = torch.from_numpy(bgr.copy()).permute(2, 0, 1).unsqueeze(0).float()
    return tensor


# ----------------------------------------------------------------------------
# 4. Embedding extraction
# ----------------------------------------------------------------------------
@torch.no_grad()
def extract_embedding(model, device, image_path: str):
    """
    Returns (embedding, quality) or (None, None) if no face detected.
      embedding: L2-normalized 512-d numpy vector
      quality:   raw feature norm (higher ~ better quality face)
    """
    face = get_aligned_face(image_path)
    if face is None:
        return None, None

    x = to_input(face).to(device)
    feat, norm = model(x)                      # AdaFace returns (feature, norm)
    feat = F.normalize(feat, dim=1)            # make sure it's unit length
    return feat.squeeze(0).cpu().numpy(), float(norm.squeeze().cpu())


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))                 # both are already unit vectors


# ----------------------------------------------------------------------------
# 5. Quick sanity test
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, help="path to cloned AdaFace repo")
    p.add_argument("--ckpt", required=True, help="path to pretrained .ckpt")
    p.add_argument("--arch", default="ir_101", choices=["ir_18", "ir_34", "ir_50", "ir_101"])
    p.add_argument("--img1", required=True)
    p.add_argument("--img2", required=True)
    args = p.parse_args()

    model, device = load_adaface(args.repo, args.ckpt, args.arch)
    print(f"Model loaded on {device}")

    e1, q1 = extract_embedding(model, device, args.img1)
    e2, q2 = extract_embedding(model, device, args.img2)

    if e1 is None or e2 is None:
        sys.exit("Could not detect a face in one of the images.")

    print(f"Embedding shape : {e1.shape}")
    print(f"Quality (norm)  : img1={q1:.2f}  img2={q2:.2f}")
    print(f"Cosine similarity: {cosine_similarity(e1, e2):.4f}")
