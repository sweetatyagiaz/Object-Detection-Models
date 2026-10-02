"""
Face search pipeline built on DeepFace.

Stages (each one is resumable and cached):
    1. create_dataset     raw photos  -> aligned face crops + manifest
    2. recover_no_face    retry photos with no face using a stronger detector
    3. create_embeddings  crops       -> embeddings (cached)
    4. create_index       embeddings  -> de-duplicated index
    5. search_image       query photo -> ranked matches
    6. plot_search_result matches     -> figure
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import pickle
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # quiet TensorFlow, must be set before import

import cv2
import matplotlib.pyplot as plt
import numpy as np
from deepface import DeepFace
from tqdm import tqdm

log = logging.getLogger("facesearch")


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def setup_logging(level: int = logging.INFO, log_file: Optional[Path] = None) -> None:
    """Console logging, plus an optional log file. Safe to call more than once."""
    log.setLevel(level)
    log.propagate = False
    log.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    log.addHandler(console)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        log.addHandler(fh)


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    # Paths
    database_dir: Path = Path("../datasets/raw_data/")
    crops_dir: Path = Path("../datasets/dataset_deepface/")
    results_dir: Path = Path("../datasets/results/")
    query_image: Path = Path("../datasets/images/Tejrit.jpg")

    # Model / detectors
    model: str = "Facenet512"
    detector: str = "yunet"              # used to build the crop dataset
    query_detector: str = "retinaface"   # strongest one, a single face drives the search
    expand: int = 10                     # expand_percentage, must match for crops and query
    exts: tuple = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

    # Crop filters
    min_face_px: int = 40
    min_conf: float = 0.90

    # De-duplication
    dup_threshold: float = 0.05          # cosine distance below this = same picture
    scope: str = "folder"                # "folder" or "global"

    # Search
    strict_threshold: float = 0.30       # Facenet512 cosine; ArcFace is ~0.68
    top_k: int = 12
    min_dist: float = 0.0                # 0.05 hides the query photo itself if it is in the DB
    conf_k: float = 15.0                 # confidence curve steepness (ArcFace: ~7)
    query_face_idx: Optional[int] = None # None = largest face

    def __post_init__(self):
        for name in ("database_dir", "crops_dir", "results_dir", "query_image"):
            setattr(self, name, Path(getattr(self, name)))
        if self.scope not in ("folder", "global"):
            raise ValueError("scope must be 'folder' or 'global'")

    # Derived paths
    @property
    def manifest_path(self) -> Path:
        return self.results_dir / "crops_manifest_deepface.json"

    @property
    def state_path(self) -> Path:
        return self.results_dir / "crops_state_deepface.json"

    @property
    def emb_path(self) -> Path:
        return self.results_dir / f"emb_all_{self.model}_deepface.pkl"

    @property
    def index_path(self) -> Path:
        return self.results_dir / f"index_{self.model}_deepface.pkl"

    def make_dirs(self) -> None:
        self.crops_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class Match:
    crop: str
    dist: float
    conf: float
    src_path: Path
    box: tuple
    n_dupes: int

    @property
    def folder(self) -> str:
        return Path(self.crop).parent.as_posix()


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def unit(v) -> np.ndarray:
    """L2-normalise a vector or a matrix of row vectors."""
    v = np.asarray(v, dtype=np.float32)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def confidence_pct(d: float, threshold: float, k: float) -> float:
    """Heuristic score (not a probability): 50% at the threshold, ~100% near 0."""
    return float(100.0 / (1.0 + np.exp(k * (d - threshold))))


def _read_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _write_json(path: Path, obj) -> None:
    """Atomic write, so an interrupted run cannot corrupt the file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj))
    tmp.replace(path)


def _read_pickle(path: Path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _write_pickle(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(obj, f)
    tmp.replace(path)


def _file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _detect(img, detector: str, expand: int) -> list:
    """
    Run face detection. Returns [] when no face is found.
    Any other error (missing package, corrupt file, ...) is raised, so a
    broken setup is never mistaken for 'photo has no face'.
    """
    try:
        return DeepFace.extract_faces(
            img, detector_backend=detector, align=True,
            enforce_detection=True, expand_percentage=expand)
    except ValueError as e:
        if "could not be detected" in str(e):
            return []
        raise


def _face_to_bgr(face: np.ndarray) -> np.ndarray:
    rgb = (face * 255).clip(0, 255).astype(np.uint8)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _crop_photo(src: Path, rel: Path, cfg: Config, detector: str,
                min_px: int, min_conf: float, manifest: dict) -> int:
    """Detect faces in one photo and save the valid ones. Returns how many were kept."""
    kept = 0
    for f in _detect(str(src), detector, cfg.expand):
        fa, conf = f["facial_area"], float(f.get("confidence", 1.0))
        if fa["w"] < min_px or fa["h"] < min_px or conf < min_conf:
            continue
        stem = rel.stem if kept == 0 else f"{rel.stem}__{kept}"
        out_rel = rel.with_name(stem + ".jpg")          # same subfolders, same name
        out_path = cfg.crops_dir / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), _face_to_bgr(f["face"]))
        manifest[out_rel.as_posix()] = {
            "source_rel": rel.as_posix(),
            "box": [fa["x"], fa["y"], fa["w"], fa["h"]],
            "conf": conf,
            "detector": detector,
        }
        kept += 1
    return kept


# --------------------------------------------------------------------------- #
# Stage 1: crop dataset
# --------------------------------------------------------------------------- #
def create_dataset(cfg: Config, checkpoint_every: int = 25) -> dict:
    """Detect, align and crop faces from every raw photo (resumable)."""
    cfg.make_dirs()
    manifest = _read_json(cfg.manifest_path, {})
    state = _read_json(cfg.state_path, {})
    hashes = state.setdefault("hashes", {})             # md5 -> first copy's source_rel
    exact_dupes = state.setdefault("exact_dupes", {})   # skipped file -> first copy
    no_face = set(state.setdefault("no_face", []))

    def save():
        _write_json(cfg.manifest_path, manifest)
        state["no_face"] = sorted(no_face)
        _write_json(cfg.state_path, state)

    all_paths = sorted(p for p in cfg.database_dir.rglob("*") if p.suffix.lower() in cfg.exts)
    done = {m["source_rel"] for m in manifest.values()} | set(exact_dupes) | no_face
    todo = [p for p in all_paths if p.relative_to(cfg.database_dir).as_posix() not in done]
    log.info("Dataset: %d images found, %d to process (detector=%s)",
             len(all_paths), len(todo), cfg.detector)

    errors = 0
    for n, path in enumerate(tqdm(todo, desc="Cropping", unit="img"), 1):
        rel = path.relative_to(cfg.database_dir)
        rel_s = rel.as_posix()

        # Skip byte-identical files before the slow detection
        h = _file_hash(path)
        first = hashes.get(h)
        if first is not None and first != rel_s:
            exact_dupes[rel_s] = first
            continue
        hashes[h] = rel_s

        try:
            kept = _crop_photo(path, rel, cfg, cfg.detector,
                               cfg.min_face_px, cfg.min_conf, manifest)
        except ImportError:
            save()
            raise                                    # broken install, stop immediately
        except Exception as e:
            errors += 1
            log.warning("Error on %s: %s", rel_s, str(e)[:120])
            continue                                 # not marked as no-face, retried next run

        if kept == 0:
            no_face.add(rel_s)

        if n % checkpoint_every == 0:
            save()

    save()
    stats = {"images": len(all_paths), "crops": len(manifest),
             "exact_dupes": len(exact_dupes), "no_face": len(no_face), "errors": errors}
    log.info("Dataset done: %(crops)d crops | %(exact_dupes)d exact duplicates | "
             "%(no_face)d without a valid face | %(errors)d errors", stats)
    if errors:
        log.error("%d photos raised errors and will be retried on the next run", errors)
    if stats["images"] and stats["no_face"] / stats["images"] > 0.05:
        log.warning("%.0f%% of photos have no face. Try recover_no_face() with a stronger detector.",
                    100 * stats["no_face"] / stats["images"])
    return stats


def recover_no_face(cfg: Config, detector: str = "retinaface",
                    min_face_px: int = 25, min_conf: float = 0.80) -> dict:
    """Retry photos that produced no crop, using a stronger detector and relaxed filters."""
    manifest = _read_json(cfg.manifest_path, {})
    state = _read_json(cfg.state_path, {})
    no_face = set(state.setdefault("no_face", []))
    tried = set(state.setdefault("recovery_tried", {}).setdefault(detector, []))

    # Photos whose only crop you rejected by hand must stay rejected
    rejected = {Path(n).with_suffix("").as_posix().split("__")[0] for n in state.get("rejected", [])}

    todo = [s for s in sorted(no_face)
            if s not in tried and Path(s).with_suffix("").as_posix() not in rejected]
    log.info("Recovery: %d photos to retry with %s", len(todo), detector)

    outcome = {"recovered": 0, "found_but_filtered": 0, "not_detected": 0, "errors": 0}

    def save():
        _write_json(cfg.manifest_path, manifest)
        state["no_face"] = sorted(no_face)
        state["recovery_tried"][detector] = sorted(tried)
        _write_json(cfg.state_path, state)

    for n, rel_s in enumerate(tqdm(todo, desc=f"Recovering ({detector})", unit="img"), 1):
        rel = Path(rel_s)
        try:
            faces = _detect(str(cfg.database_dir / rel), detector, cfg.expand)
            kept = _crop_photo(cfg.database_dir / rel, rel, cfg, detector,
                               min_face_px, min_conf, manifest) if faces else 0
        except ImportError:
            save()
            raise
        except Exception as e:
            outcome["errors"] += 1
            log.warning("Error on %s: %s", rel_s, str(e)[:120])
            continue

        if kept:
            no_face.discard(rel_s)
            outcome["recovered"] += 1
        elif faces:
            outcome["found_but_filtered"] += 1
        else:
            outcome["not_detected"] += 1
        tried.add(rel_s)

        if n % 20 == 0:
            save()

    save()
    log.info("Recovery done: %s | %d photos still without a face", outcome, len(no_face))
    return outcome


# --------------------------------------------------------------------------- #
# Stage 2: embeddings
# --------------------------------------------------------------------------- #
def create_embeddings(cfg: Config, checkpoint_every: int = 50) -> dict:
    """Embed every crop in the manifest (cached and resumable)."""
    manifest = _read_json(cfg.manifest_path, {})
    emb = _read_pickle(cfg.emb_path) if cfg.emb_path.exists() else {}

    todo = [n for n in manifest if n not in emb and (cfg.crops_dir / n).exists()]
    log.info("Embeddings: %d crops in manifest, %d to embed (model=%s)",
             len(manifest), len(todo), cfg.model)

    failed = []
    for k, name in enumerate(tqdm(todo, desc="Embedding", unit="crop"), 1):
        try:
            rep = DeepFace.represent(str(cfg.crops_dir / name), model_name=cfg.model,
                                     detector_backend="skip", enforce_detection=False)[0]
            emb[name] = rep["embedding"]
        except ImportError:
            raise
        except Exception as e:
            failed.append(name)
            log.warning("Embedding failed for %s: %s", name, str(e)[:120])
        if k % checkpoint_every == 0:
            _write_pickle(cfg.emb_path, emb)

    _write_pickle(cfg.emb_path, emb)
    log.info("Embeddings done: %d total, %d failed", len(emb), len(failed))
    return emb


# --------------------------------------------------------------------------- #
# Stage 3: de-duplicated index
# --------------------------------------------------------------------------- #
def load_pickle_file(path: Path) -> dict:
    """Load an embedding or index file. Raises a clear error if it does not exist."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No file at {path.resolve()}. Run the earlier pipeline stages first.")
    data = _read_pickle(path)
    log.info("Loaded %d entries from %s", len(data), path.name)
    return data


def create_index(cfg: Config, emb: Optional[dict] = None) -> dict:
    """Drop near-identical faces (greedy) and save the final index."""
    manifest = _read_json(cfg.manifest_path, {})
    if emb is None:
        emb = load_pickle_file(cfg.emb_path)

    # Only crops that are still approved and still on disk
    names = sorted(n for n in emb if n in manifest and (cfg.crops_dir / n).exists())
    groups: dict[str, list[str]] = {}
    for n in names:
        key = Path(n).parent.as_posix() if cfg.scope == "folder" else ""
        groups.setdefault(key, []).append(n)

    index: dict = {}
    for members in groups.values():
        V = unit(np.array([emb[n] for n in members]))
        D = 1.0 - V @ V.T                                # all pairwise distances at once
        kept: list[int] = []
        for i, name in enumerate(members):
            if kept:
                dk = D[i, kept]
                j = int(np.argmin(dk))
                if dk[j] < cfg.dup_threshold:
                    index[members[kept[j]]]["dupes"].append({
                        "crop": name,
                        "source_rel": manifest[name]["source_rel"],
                        "dist": float(dk[j])})
                    continue
            index[name] = {"emb": emb[name], "dupes": [], **manifest[name]}
            kept.append(i)

    n_dupes = sum(len(e["dupes"]) for e in index.values())
    _write_pickle(cfg.index_path, index)
    log.info("Index: %d kept, %d duplicates skipped -> %s", len(index), n_dupes, cfg.index_path.resolve())
    if names and n_dupes / len(names) > 0.30:
        log.warning("%.0f%% of crops were removed as duplicates. Check with show_removed().",
                    100 * n_dupes / len(names))
    return index


def show_removed(cfg: Config, top: int = 10) -> list:
    """Log the least certain duplicates (highest distance first) for a visual check."""
    index = load_pickle_file(cfg.index_path)
    pairs = sorted(((dp["dist"], kept, dp["crop"])
                    for kept, e in index.items() for dp in e["dupes"]), reverse=True)
    if not pairs:
        log.info("No duplicates were removed.")
        return []
    log.info("Least certain duplicates (open a few to confirm they are the same picture):")
    for d, kept, dup in pairs[:top]:
        log.info("  d=%.3f  kept=%s  skipped=%s", d, kept, dup)
    return pairs[:top]


# --------------------------------------------------------------------------- #
# Stage 4: search
# --------------------------------------------------------------------------- #
def embed_query(cfg: Config, query_image: Optional[Path] = None) -> tuple[np.ndarray, tuple]:
    """Detect, crop and embed the query photo. Returns (unit vector, face box)."""
    query_image = Path(query_image or cfg.query_image)
    if not query_image.exists():
        raise FileNotFoundError(f"Query image not found: {query_image.resolve()}")

    faces = _detect(str(query_image), cfg.query_detector, cfg.expand)
    if not faces:
        raise ValueError(f"No face found in {query_image.name} with {cfg.query_detector}. "
                         "Try another detector or a clearer photo.")
    log.info("Query: %d face(s) found in %s", len(faces), query_image.name)

    if cfg.query_face_idx is None:
        face = max(faces, key=lambda f: f["facial_area"]["w"] * f["facial_area"]["h"])
    else:
        face = faces[cfg.query_face_idx]

    fa = face["facial_area"]
    box = (fa["x"], fa["y"], fa["w"], fa["h"])

    # Round-trip through JPEG so the query matches the saved database crops
    bgr = cv2.imdecode(cv2.imencode(".jpg", _face_to_bgr(face["face"]))[1], cv2.IMREAD_COLOR)
    rep = DeepFace.represent(bgr, model_name=cfg.model,
                             detector_backend="skip", enforce_detection=False)[0]
    return unit(rep["embedding"]), box


def search_image(cfg: Config, index: Optional[dict] = None,
                 query_image: Optional[Path] = None) -> tuple[list[Match], tuple]:
    """
    Rank the index against a raw query photo.
    Pass a preloaded `index` to run many queries without reloading the file.
    """
    if index is None:
        index = load_pickle_file(cfg.index_path)
    names = list(index)
    vecs = unit(np.array([index[n]["emb"] for n in names]))

    q, q_box = embed_query(cfg, query_image)
    dist = 1.0 - vecs @ q

    seen, matches = set(), []
    for i in np.argsort(dist):
        d = float(dist[i])
        if d < cfg.min_dist:
            continue
        meta = index[names[i]]
        if meta["source_rel"] in seen:                   # best crop per source photo
            continue
        seen.add(meta["source_rel"])
        matches.append(Match(
            crop=names[i], dist=d,
            conf=confidence_pct(d, cfg.strict_threshold, cfg.conf_k),
            src_path=cfg.database_dir / meta["source_rel"],
            box=tuple(meta["box"]), n_dupes=len(meta["dupes"])))
        if len(matches) >= cfg.top_k:
            break

    n_strict = sum(m.dist < cfg.strict_threshold for m in matches)
    log.info("Search: %d strict matches (< %.2f), showing top %d",
             n_strict, cfg.strict_threshold, len(matches))
    for i, m in enumerate(matches, 1):
        log.info("  #%-2d d=%.3f  conf=%5.1f%%  dupes=%d  %s", i, m.dist, m.conf, m.n_dupes, m.crop)
    return matches, q_box


# --------------------------------------------------------------------------- #
# Stage 5: plot
# --------------------------------------------------------------------------- #
def load_with_box(path: Path, box: tuple, color: tuple) -> np.ndarray:
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x, y, w, h = box
    cv2.rectangle(img, (x, y), (x + w, y + h), color, max(2, img.shape[1] // 300))
    return img


def plot_search_result(cfg: Config, matches: list[Match], q_box: tuple,
                       cols: int = 4, save_path: Optional[Path] = None, show: bool = True):
    """Query plus matches, each with its face box. Returns the figure."""
    rows = math.ceil((1 + len(matches)) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axes = np.atleast_1d(axes).flatten()
    for ax in axes:
        ax.axis("off")

    axes[0].imshow(load_with_box(cfg.query_image, q_box, (0, 0, 255)))
    axes[0].set_title("Query (face used)", color="blue", fontweight="bold")

    for ax, (i, m) in zip(axes[1:], enumerate(matches, 1)):
        good = m.dist < cfg.strict_threshold
        try:
            ax.imshow(load_with_box(m.src_path, m.box, (0, 200, 0) if good else (255, 0, 0)))
        except FileNotFoundError:
            log.warning("Missing source photo: %s", m.src_path)
            ax.text(0.5, 0.5, "file missing", ha="center")
        ax.set_title(
            f"#{i} {'MATCH' if good else 'weak'}  d={m.dist:.3f}  conf={m.conf:.0f}%"
            f"  (+{m.n_dupes} copies)\n{m.folder}/{m.src_path.name[:18]}",
            fontsize=9, color="green" if good else "red")

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        log.info("Saved figure -> %s", save_path)
    if show:
        plt.show()
    return fig
