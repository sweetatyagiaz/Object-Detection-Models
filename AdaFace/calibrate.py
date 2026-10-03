"""
Threshold calibration for AdaFace on YOUR data.

Embeds the gallery, builds same-person (genuine) and different-person
(impostor) pairs, then reports the cosine threshold needed for target FARs.

Usage:  python calibrate.py
"""
import itertools
import logging
import random

import numpy as np

from adaface import AdaFace

logging.basicConfig(level=logging.WARNING)

MODEL_PATH = "../models/adaface_ir50.onnx"
DATABASE_DIR = "../datasets/dataset_deepface"
INDEX_PATH = "../datasets/faiss_indexes/face_index_adaface.bin"
MAPPING_PATH = "../datasets/faiss_indexes/mapping_adaface.json"

N_IMPOSTOR_PAIRS = 2_000_000
MAX_GENUINE_PER_PERSON = 100
FAR_TARGETS = [1e-1, 1e-2, 1e-3, 1e-4]

rng = np.random.default_rng(0)
random.seed(0)

model = AdaFace(MODEL_PATH, DATABASE_DIR, INDEX_PATH, MAPPING_PATH)
data = model.embed_database()
E = data["embeddings"]
labels = data["person_ids"]
N = len(E)
print(f"\n{N} embeddings, {len(set(labels.tolist()))} people")

# ---- genuine pairs (same person, different image) ----
by_person = {}
for i, p in enumerate(labels):
    by_person.setdefault(int(p), []).append(i)

genuine_pairs = []
for idxs in by_person.values():
    if len(idxs) < 2:
        continue
    pairs = list(itertools.combinations(idxs, 2))
    if len(pairs) > MAX_GENUINE_PER_PERSON:
        pairs = random.sample(pairs, MAX_GENUINE_PER_PERSON)
    genuine_pairs.extend(pairs)

if not genuine_pairs:
    raise SystemExit("No person has 2+ images, cannot compute genuine pairs.")

g = np.array(genuine_pairs)
genuine = np.einsum("ij,ij->i", E[g[:, 0]], E[g[:, 1]])

# ---- impostor pairs (different people) ----
a = rng.integers(0, N, N_IMPOSTOR_PAIRS)
b = rng.integers(0, N, N_IMPOSTOR_PAIRS)
mask = labels[a] != labels[b]
a, b = a[mask], b[mask]
impostor = np.einsum("ij,ij->i", E[a], E[b])

print(f"genuine pairs : {len(genuine):>9}   mean={genuine.mean():.3f}  "
      f"median={np.median(genuine):.3f}  p5={np.percentile(genuine, 5):.3f}")
print(f"impostor pairs: {len(impostor):>9}   mean={impostor.mean():.3f}  "
      f"p99={np.percentile(impostor, 99):.3f}  max={impostor.max():.3f}")

# ---- thresholds at target FAR ----
print("\n  FAR target | threshold |   TAR")
print("  -----------+-----------+--------")
for far in FAR_TARGETS:
    if far * len(impostor) < 10:
        print(f"  {far:>10.0e} |    n/a    |  (too few impostor pairs)")
        continue
    thr = float(np.quantile(impostor, 1 - far))
    tar = float((genuine >= thr).mean())
    print(f"  {far:>10.0e} | {thr:>9.3f} | {tar:>6.1%}")

# ---- best balanced-accuracy threshold ----
cands = np.linspace(-0.2, 0.9, 221)
bal = [((genuine >= t).mean() + (impostor < t).mean()) / 2 for t in cands]
best = int(np.argmax(bal))
print(f"\nBest balanced-accuracy threshold: {cands[best]:.3f} ({bal[best]:.1%})")
print("Use a FAR-based threshold above when false matches are costly.")
