"""
AdaFace (ONNX) + FAISS person search.

Fixes vs. the original version:
  * BGR input (AdaFace is trained on BGR; cv2.imread already gives BGR)
  * Face detection + 5-point alignment (insightface) with a safe fallback
  * Batched embedding extraction
  * Exact IndexFlatIP search (no approximate misses on small/medium galleries)
  * Person-level aggregation done on a larger candidate pool, THEN top_k
  * Quality score (feature norm) stored per image, optional quality filter
  * Clear warnings instead of silent skips

Dataset layout (unchanged):
    database_dir/
        1.Alice/ img1.jpg, img2.jpg ...
        2.Bob/   ...

Requirements:
    pip install onnxruntime(-gpu) faiss-cpu opencv-python numpy insightface
"""
import json
import logging
import os
from collections import defaultdict

import cv2
import faiss
import numpy as np
import onnxruntime as ort

log = logging.getLogger("adaface")
IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


class AdaFace:
    INPUT_SIZE = (112, 112)
    DIMENSION = 512

    def __init__(
        self,
        model_path,
        database_dir,
        index_path,
        mapping_path,
        providers=None,
        use_detector=True,
        det_size=(640, 640),
        fallback_on_no_face=True,
        batch_size=32,
        min_quality=None,
    ):
        """
        use_detector        : detect + align faces with insightface (recommended).
        fallback_on_no_face : if no face is detected (e.g. very tight crops),
                              pad to square and resize instead of skipping.
        min_quality         : drop gallery images whose feature norm is below this
                              (only works if the ONNX model outputs the norm).
        """
        self.database_dir = database_dir
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.fallback_on_no_face = fallback_on_no_face
        self.batch_size = batch_size
        self.min_quality = min_quality

        wanted = providers or ["CUDAExecutionProvider", "CPUExecutionProvider"]
        available = ort.get_available_providers()
        providers = [p for p in wanted if p in available] or ["CPUExecutionProvider"]

        self.session = ort.InferenceSession(model_path, providers=providers)
        inp = self.session.get_inputs()[0]
        self.input_name = inp.name
        self.output_names = [o.name for o in self.session.get_outputs()]

        # Fixed-batch ONNX exports (batch dim is an int) must run one by one.
        first_dim = inp.shape[0]
        self._max_batch = 1 if isinstance(first_dim, int) else batch_size
        if len(self.output_names) < 2:
            log.warning(
                "ONNX model has a single output: feature norm (quality) is not "
                "available, quality filtering will be ineffective."
            )

        self.detector = None
        self._face_align = None
        if use_detector:
            try:
                from insightface.app import FaceAnalysis
                from insightface.utils import face_align

                self.detector = FaceAnalysis(
                    name="buffalo_l",
                    allowed_modules=["detection"],
                    providers=providers,
                )
                self.detector.prepare(
                    ctx_id=0 if "CUDAExecutionProvider" in providers else -1,
                    det_size=det_size,
                )
                self._face_align = face_align
            except Exception as e:
                log.warning(f"insightface unavailable ({e}); using resize fallback only.")

        self.index = None
        self.mapping = []

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------
    def _pad_resize(self, image):
        """Pad to square (keeps aspect ratio) then resize to 112x112."""
        h, w = image.shape[:2]
        s = max(h, w)
        top = (s - h) // 2
        left = (s - w) // 2
        image = cv2.copyMakeBorder(
            image, top, s - h - top, left, s - w - left,
            cv2.BORDER_CONSTANT, value=(0, 0, 0),
        )
        return cv2.resize(image, self.INPUT_SIZE)

    def align(self, image):
        """BGR image -> aligned 112x112 BGR face, or None."""
        if self.detector is not None:
            img = image
            # Detectors struggle with tiny crops: add a border for context.
            if max(img.shape[:2]) < 256:
                pad = int(0.5 * max(img.shape[:2]))
                img = cv2.copyMakeBorder(
                    img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0)
                )
            faces = self.detector.get(img)
            if faces:
                face = max(
                    faces,
                    key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
                )
                return self._face_align.norm_crop(img, face.kps, image_size=112)
            if not self.fallback_on_no_face:
                return None
        return self._pad_resize(image)

    def preprocess(self, aligned_bgr):
        """Aligned 112x112 BGR uint8 -> (3,112,112) float32 in [-1, 1]. Stays BGR."""
        x = aligned_bgr.astype(np.float32)
        x = x / 127.5 - 1.0
        return np.transpose(x, (2, 0, 1))

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------
    def _embed_aligned(self, faces):
        """List of aligned BGR faces -> (embeddings (n,512), quality (n,))."""
        embs, quals = [], []
        for i in range(0, len(faces), self._max_batch):
            chunk = faces[i:i + self._max_batch]
            batch = np.stack([self.preprocess(f) for f in chunk]).astype(np.float32)
            outs = self.session.run(self.output_names, {self.input_name: batch})
            feat = outs[0].astype(np.float32).reshape(len(chunk), -1)
            raw_norm = np.linalg.norm(feat, axis=1)
            if len(outs) > 1:
                q = outs[1].astype(np.float32).reshape(-1)
            else:
                q = raw_norm
            feat = feat / np.maximum(raw_norm[:, None], 1e-12)
            embs.append(feat)
            quals.append(q)
        return np.concatenate(embs), np.concatenate(quals)

    def get_embedding(self, image):
        """BGR image -> (embedding (512,), quality) or None if no usable face."""
        face = self.align(image)
        if face is None:
            return None
        e, q = self._embed_aligned([face])
        return e[0], float(q[0])

    # ------------------------------------------------------------------
    # Gallery
    # ------------------------------------------------------------------
    def _collect_gallery(self):
        items = []
        for person_dir in sorted(os.listdir(self.database_dir)):
            person_path = os.path.join(self.database_dir, person_dir)
            if not os.path.isdir(person_path):
                continue
            try:
                pid_str, name = person_dir.split(".", 1)
                person_id = int(pid_str)
            except ValueError:
                log.warning(f"Skipping folder '{person_dir}' (expected '<id>.<name>')")
                continue
            for root, _, files in os.walk(person_path):
                for f in sorted(files):
                    if f.lower().endswith(IMG_EXT):
                        items.append((person_id, name.strip(), os.path.join(root, f)))
        return items

    def embed_database(self):
        """
        Embed every gallery image. Returns a dict with:
        embeddings (N,512), quality (N,), person_ids (N,), names, images.
        """
        items = self._collect_gallery()
        log.info(f"Found {len(items)} gallery images")

        embs, quals, meta = [], [], []
        skipped = 0
        bs = self.batch_size

        for start in range(0, len(items), bs):
            faces, ok = [], []
            for it in items[start:start + bs]:
                img = cv2.imread(it[2])
                face = None if img is None else self.align(img)
                if face is None:
                    skipped += 1
                    log.warning(f"Skipped (unreadable / no face): {it[2]}")
                    continue
                faces.append(face)
                ok.append(it)
            if faces:
                e, q = self._embed_aligned(faces)
                embs.append(e)
                quals.append(q)
                meta.extend(ok)
            print(f"  embedded {min(start + bs, len(items))}/{len(items)}", end="\r")
        print()

        if not embs:
            raise RuntimeError("No embeddings produced. Check dataset path and images.")

        return {
            "embeddings": np.concatenate(embs).astype(np.float32),
            "quality": np.concatenate(quals).astype(np.float32),
            "person_ids": np.array([m[0] for m in meta]),
            "names": [m[1] for m in meta],
            "images": [m[2] for m in meta],
            "skipped": skipped,
        }

    def build_index(self):
        data = self.embed_database()
        keep = np.ones(len(data["embeddings"]), dtype=bool)
        if self.min_quality is not None:
            keep = data["quality"] >= self.min_quality
            print(f"Quality filter removed {int((~keep).sum())} images")

        embeddings = np.ascontiguousarray(data["embeddings"][keep])
        if len(embeddings) == 0:
            raise RuntimeError("All images were filtered out by min_quality.")

        # Exact inner-product index (== cosine, vectors are unit length).
        self.index = faiss.IndexFlatIP(self.DIMENSION)
        self.index.add(embeddings)

        idx = np.where(keep)[0]
        self.mapping = [
            {
                "person_id": int(data["person_ids"][i]),
                "name": data["names"][i],
                "image": data["images"][i],
                "quality": float(data["quality"][i]),
            }
            for i in idx
        ]
        self.save_index()
        print(f"Indexed {len(embeddings)} embeddings "
              f"({len(set(m['person_id'] for m in self.mapping))} people), "
              f"skipped {data['skipped']}")

    def save_index(self):
        for path in (self.index_path, self.mapping_path):
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.mapping_path, "w") as f:
            json.dump(self.mapping, f, indent=2)

    def load_index(self):
        self.index = faiss.read_index(self.index_path)
        with open(self.mapping_path) as f:
            self.mapping = json.load(f)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search_image(self, image, top_k=5, threshold=0.4, pool=None):
        """
        image     : BGR numpy image
        top_k     : number of PEOPLE to return
        threshold : minimum best_score for a person to be returned (None = no cut)
        pool      : number of nearest gallery images to inspect (default max(50, 10*top_k))
        """
        if self.index is None:
            self.load_index()

        res = self.get_embedding(image)
        if res is None:
            return []
        query, _ = res
        query = query.reshape(1, -1).astype(np.float32)

        pool = min(pool or max(50, top_k * 10), self.index.ntotal)
        sims, ids = self.index.search(query, pool)

        persons = defaultdict(list)
        for score, idx in zip(sims[0], ids[0]):
            if idx < 0:
                continue
            m = self.mapping[int(idx)]
            persons[m["person_id"]].append(
                {"score": float(score), "name": m["name"], "image": m["image"]}
            )

        results = []
        for pid, matches in persons.items():
            matches.sort(key=lambda x: x["score"], reverse=True)
            best = matches[0]
            if threshold is not None and best["score"] < threshold:
                continue
            top3 = [x["score"] for x in matches[:3]]
            results.append(
                {
                    "person_id": pid,
                    "name": best["name"],
                    "best_score": round(best["score"], 4),
                    "mean_top3": round(float(np.mean(top3)), 4),
                    "matched_images": len(matches),
                    "best_image": best["image"],
                }
            )

        results.sort(key=lambda x: x["best_score"], reverse=True)
        return results[:top_k]

    def search_face(self, image_path, top_k=5, threshold=0.4):
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Cannot load image: {image_path}")
        return self.search_image(image, top_k=top_k, threshold=threshold)

    def search_from_faiss(
        self,
        image_path,
        top_k=5,
        threshold=0.4,
        person_level=True,
    ):
        """
        Search an image using existing FAISS index files.

        Parameters
        ----------
        image_path : str
            Query image path
        top_k : int
            Number of results
        threshold : float
            Minimum similarity score
        person_level : bool
            Aggregate by person or return raw image matches
        """

        # Load index if not loaded
        if self.index is None:
            self.load_index()

        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(
                f"Unable to load image: {image_path}"
            )

        result = self.get_embedding(image)
        if result is None:
            return []

        query_embedding, quality = result

        query_embedding = (
            query_embedding
            .reshape(1, -1)
            .astype(np.float32)
        )

        scores, indices = self.index.search(
            query_embedding,
            min(100, self.index.ntotal)
        )

        if not person_level:
            matches = []

            for score, idx in zip(scores[0], indices[0]):

                if idx < 0:
                    continue

                if score < threshold:
                    continue

                meta = self.mapping[idx]

                matches.append({
                    "person_id": meta["person_id"],
                    "name": meta["name"],
                    "score": round(float(score), 4),
                    "image": meta["image"],
                    "quality": meta.get("quality")
                })

            return matches[:top_k]

        # Person aggregation
        persons = defaultdict(list)

        for score, idx in zip(scores[0], indices[0]):

            if idx < 0:
                continue

            meta = self.mapping[idx]

            persons[meta["person_id"]].append({
                "score": float(score),
                "name": meta["name"],
                "image": meta["image"]
            })

        results = []

        for person_id, matches in persons.items():

            matches.sort(
                key=lambda x: x["score"],
                reverse=True
            )

            best = matches[0]

            if best["score"] < threshold:
                continue

            top3 = [
                m["score"]
                for m in matches[:3]
            ]

            results.append({
                "person_id": person_id,
                "name": best["name"],
                "best_score": round(best["score"], 4),
                "avg_score": round(
                    float(np.mean(top3)),
                    4
                ),
                "matched_images": len(matches),
                "best_image": best["image"]
            })

        results.sort(
            key=lambda x: x["best_score"],
            reverse=True
        )

        return results[:top_k]
