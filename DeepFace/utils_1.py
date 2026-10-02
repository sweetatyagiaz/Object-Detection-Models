import json, hashlib, cv2, os
import numpy as np
from pathlib import Path
from deepface import DeepFace
import json, pickle
import math
import matplotlib.pyplot as plt


# ---------- Helpers ----------
def unit(v):
    v = np.asarray(v, dtype=np.float32)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)

def confidence_pct(d=False, threshold=False, k=False):
    """Heuristic score: 50% at the threshold, ~100% near 0, ~0% far above."""
    return float(100 / (1 + np.exp(k * (d - threshold))))

def load_with_box(path, box, color):
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x, y, w, h = box
    t = max(2, img.shape[1] // 300)
    cv2.rectangle(img, (x, y), (x + w, y + h), color, t)
    return img

# ---------- Load index ----------
def load_embedding_file(EMB_PATH=False):
    if os.path.exists(EMB_PATH):
        with open(EMB_PATH, "rb") as f:
            emb = pickle.load(f)
        print(f"Successfully loaded index with {len(emb)} image entries.")
    else:
        print(f"Error: No index file found at {EMB_PATH}")
        # index = {}
        emb = False

    return emb

def create_dataset(DATABASE_DIR=False, CROPS_DIR=False, MANIFEST=False, STATE=False, 
                   DETECTOR=False, EXTS=False, MIN_FACE_PX=False, MIN_CONF=False, EXPAND=10):
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    hashes = state.setdefault("hashes", {})            # md5 -> first copy's source_rel
    exact_dupes = state.setdefault("exact_dupes", {})  # skipped file -> first copy
    no_face = set(state.setdefault("no_face", []))     # photos with no valid face

    def save():
        MANIFEST.write_text(json.dumps(manifest))
        state["no_face"] = sorted(no_face)
        STATE.write_text(json.dumps(state))

    def file_hash(p):
        h = hashlib.md5()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    all_paths = sorted(p for p in DATABASE_DIR.rglob("*") if p.suffix.lower() in EXTS)
    processed = {m["source_rel"] for m in manifest.values()} | set(exact_dupes) | no_face
    todo = [p for p in all_paths if p.relative_to(DATABASE_DIR).as_posix() not in processed]
    print(f"{len(all_paths)} images, {len(todo)} to process")

    for n, path in enumerate(todo, 1):
        if n % 25 == 0:
            save()
            print(f"{n}/{len(todo)}")

        rel = path.relative_to(DATABASE_DIR)
        rel_s = rel.as_posix()

        # Layer 1: skip byte-identical files before the slow detection
        h = file_hash(path)
        first = hashes.get(h)
        if first is not None and first != rel_s:
            exact_dupes[rel_s] = first
            continue
        hashes[h] = rel_s

        try:
            faces = DeepFace.extract_faces(
                str(path), detector_backend=DETECTOR, align=True,
                enforce_detection=True, expand_percentage=EXPAND)
        except Exception:
            faces = []

        kept = 0
        for f in faces:
            fa, conf = f["facial_area"], f.get("confidence", 1.0)
            if fa["w"] < MIN_FACE_PX or fa["h"] < MIN_FACE_PX or conf < MIN_CONF:
                continue
            stem = rel.stem if kept == 0 else f"{rel.stem}__{kept}"
            out_rel = rel.with_name(stem + ".jpg")          # same subfolders, same name
            out_path = CROPS_DIR / out_rel
            out_path.parent.mkdir(parents=True, exist_ok=True)

            img = (f["face"] * 255).clip(0, 255).astype(np.uint8)
            cv2.imwrite(str(out_path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

            manifest[out_rel.as_posix()] = {
                "source_rel": rel_s,
                "box": [fa["x"], fa["y"], fa["w"], fa["h"]],
                "conf": float(conf),
                "detector": DETECTOR,
            }
            kept += 1

        if kept == 0:
            no_face.add(rel_s)

    save()
    print(f"{len(manifest)} face crops saved in {CROPS_DIR.resolve()}")
    print(f"{len(exact_dupes)} exact duplicate files skipped, {len(no_face)} photos without a valid face")
    return True

def create_embeddings(MODEL=False, CROPS_DIR=False, MANIFEST=False, EMB_PATH=False):
    manifest = json.loads(MANIFEST.read_text())
    emb = pickle.load(open(EMB_PATH, "rb")) if EMB_PATH.exists() else {}

    todo = [n for n in manifest if n not in emb and (CROPS_DIR / n).exists()]
    print(f"{len(manifest)} crops in manifest, {len(todo)} to embed")

    failed = []
    for k, name in enumerate(todo, 1):
        try:
            rep = DeepFace.represent(str(CROPS_DIR / name), model_name=MODEL,
                                    detector_backend="skip", enforce_detection=False)[0]
            emb[name] = rep["embedding"]
        except Exception as e:
            failed.append(name)
            print("failed:", name, e)
        if k % 50 == 0:
            pickle.dump(emb, open(EMB_PATH, "wb"))
            print(f"{k}/{len(todo)}")

    pickle.dump(emb, open(EMB_PATH, "wb"))
    print(len(emb), "embedded,", len(failed), "failed")

    return True

def create_index(emb=False, EMB_PATH=False, CROPS_DIR=False, INDEX_PATH=False, 
                 DUP_THRESHOLD=False, MANIFEST=False, SCOPE = "folder"):
    # Remove duplicates and build the index
    index, groups = {}, {}    # groups: key -> (kept names, kept unit vectors)

    manifest = json.loads(MANIFEST.read_text())

    # if not emb:
        # if os.path.exists(EMB_PATH):
        #     with open(EMB_PATH, "rb") as f:
        #         emb = pickle.load(f)
        #     print(f"Successfully loaded index with {len(emb)} image entries.")
        # else:
        #     print(f"Error: No index file found at {EMB_PATH}")
        #     # index = {}
        #     return False
    
    emb = load_embedding_file(EMB_PATH=EMB_PATH) if not emb else False

    for name in sorted(emb):
        if name not in manifest or not (CROPS_DIR / name).exists():
            continue                                  # rejected or deleted in Step B
        v = unit(emb[name])
        g = Path(name).parent.as_posix() if SCOPE == "folder" else ""
        kept_names, kept_vecs = groups.setdefault(g, ([], []))

        if kept_vecs:
            d = 1 - np.array(kept_vecs) @ v
            j = int(np.argmin(d))
            if d[j] < DUP_THRESHOLD:
                index[kept_names[j]]["dupes"].append(
                    {"crop": name, "source_rel": manifest[name]["source_rel"], "dist": float(d[j])})
                continue

        index[name] = {"emb": emb[name], "dupes": [], **manifest[name]}
        kept_names.append(name)
        kept_vecs.append(v)

    n_dupes = sum(len(e["dupes"]) for e in index.values())
    print(f"{len(index)} kept, {n_dupes} duplicates skipped")
    pickle.dump(index, open(INDEX_PATH, "wb"))
    print("saved ->", INDEX_PATH.resolve())

    return True

def removed_files_list(INDEX_PATH=False):
    index = load_embedding_file(EMB_PATH=INDEX_PATH)

    if not index:
        return False
    
    pairs = [(e["dupes"][k]["dist"], name, e["dupes"][k]["crop"])
         for name, e in index.items() for k in range(len(e["dupes"]))]
    pairs.sort(reverse=True)                       # least certain duplicates first
    for d, kept, dup in pairs[:10]:
        print(f"{d:.3f}  kept={kept}  skipped={dup}")

def search_image(MODEL=False, DATABASE_DIR=False, INDEX_PATH=False, QUERY_IMAGE=False, 
                 QUERY_DETECTOR=False, 
                 EXPAND=False, QUERY_FACE_IDX=False, MIN_DIST=False, STRICT_THRESHOLD=False,
                 CONF_K=False, TOP_K=False):
    # ---------- Load index ----------
    # with open(INDEX_PATH, "rb") as f:
    #     index = pickle.load(f)
    index = load_embedding_file(EMB_PATH=INDEX_PATH)

    names = list(index.keys())
    vecs = unit(np.array([index[n]["emb"] for n in names]))
    print(f"{len(names)} face crops in index")

    # ---------- Detect and crop the face in the raw query image ----------
    q_faces = DeepFace.extract_faces(QUERY_IMAGE, detector_backend=QUERY_DETECTOR,
                                    align=True, enforce_detection=True,
                                    expand_percentage=EXPAND)
    print(f"{len(q_faces)} face(s) found in query image")

    if QUERY_FACE_IDX is None:
        q_face = max(q_faces, key=lambda f: f["facial_area"]["w"] * f["facial_area"]["h"])
    else:
        q_face = q_faces[QUERY_FACE_IDX]

    qa = q_face["facial_area"]
    q_box = (qa["x"], qa["y"], qa["w"], qa["h"])

    # ---------- Embed the query crop the same way the database crops were ----------
    crop = (q_face["face"] * 255).clip(0, 255).astype(np.uint8)
    crop_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    crop_bgr = cv2.imdecode(cv2.imencode(".jpg", crop_bgr)[1], cv2.IMREAD_COLOR)  # match saved JPEG crops

    q = unit(DeepFace.represent(crop_bgr, model_name=MODEL,
                                detector_backend="skip",
                                enforce_detection=False)[0]["embedding"])

    # ---------- Rank by cosine distance, best crop per source photo ----------
    dist = 1 - vecs @ q
    order = np.argsort(dist)

    seen, matches = set(), []
    for i in order:
        d = float(dist[i])
        if d < MIN_DIST:
            continue
        meta = index[names[i]]
        if meta["source_rel"] in seen:
            continue
        seen.add(meta["source_rel"])
        matches.append({
            "crop": names[i],
            "dist": d,
            "conf": confidence_pct(d=d, threshold=STRICT_THRESHOLD, k=CONF_K),
            "src_path": DATABASE_DIR / meta["source_rel"],
            "box": tuple(meta["box"]),
            "n_dupes": len(meta["dupes"]),
        })
        if len(matches) >= TOP_K:
            break

    # ---------- Report ----------
    n_strict = sum(m["dist"] < STRICT_THRESHOLD for m in matches)
    print(f"\n{n_strict} strict matches (< {STRICT_THRESHOLD}); showing top {len(matches)}\n")
    for i, m in enumerate(matches, 1):
        print(f"#{i:<2} d={m['dist']:.3f}  conf={m['conf']:5.1f}%  dupes={m['n_dupes']}  {m['crop']}")

    return matches, q_box

def plot_search_result(cols=4, q_box=False, matches=False, QUERY_IMAGE=False, STRICT_THRESHOLD=False):
    # cols = 4
    rows = math.ceil((1 + len(matches)) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axes = axes.flatten()

    axes[0].imshow(load_with_box(QUERY_IMAGE, q_box, (0, 0, 255)))
    axes[0].set_title("Query (face used)", color="blue", fontweight="bold")

    for i, m in enumerate(matches, 1):
        good = m["dist"] < STRICT_THRESHOLD
        folder = Path(m["crop"]).parent.as_posix()
        axes[i].imshow(load_with_box(m["src_path"], m["box"],
                                    (0, 200, 0) if good else (255, 0, 0)))
        axes[i].set_title(
            f"#{i} {'MATCH' if good else 'weak'}  d={m['dist']:.3f}  conf={m['conf']:.0f}%"
            f"  (+{m['n_dupes']} copies)\n{folder}/{m['src_path'].name[:18]}",
            fontsize=9, color="green" if good else "red")

    for ax in axes:
        ax.axis("off")
    plt.tight_layout()
    plt.show()
