"""
Run the face search pipeline.

Examples:
    python test.py                                  # dataset, embed, index, removed, search, plot
    python test.py --stages search plot             # only search (index already built)
    python test.py --stages recover embed index     # retry no-face photos, then rebuild
    python test.py --query ../datasets/images/Other.jpg --stages search plot

    python test.py --stages recover embed index removed search plot
"""
import argparse
import logging
from pathlib import Path

from utils import (Config, create_dataset, create_embeddings, create_index,
                   plot_search_result, recover_no_face, search_image,
                   setup_logging, show_removed)

ALL_STAGES = ["dataset", "recover", "embed", "index", "removed", "search", "plot"]
DEFAULT_STAGES = ["dataset", "embed", "index", "removed", "search", "plot"]  # recover is opt-in

# ---------- Config (edit here) ----------
CFG = Config(
    database_dir=Path("../datasets/raw_data/"),
    crops_dir=Path("../datasets/dataset_deepface/"),
    results_dir=Path("../datasets/results/"),
    query_image=Path("../datasets/images/Tejrit.jpg"),

    model="Facenet512",
    detector="yunet",              # crop dataset detector
    query_detector="retinaface",   # strongest detector, since this one face drives the search
    expand=10,

    min_face_px=40,
    min_conf=0.90,

    dup_threshold=0.05,
    scope="folder",                # "folder" or "global"

    strict_threshold=0.30,         # Facenet512 cosine; ArcFace is ~0.68
    top_k=12,
    min_dist=0.0,                  # 0.05 hides the query photo itself if it is in the database
    conf_k=15.0,                   # ArcFace: ~7
    query_face_idx=None,           # None = largest face
)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stages", nargs="+", choices=ALL_STAGES, default=DEFAULT_STAGES)
    ap.add_argument("--query", type=Path, help="override the query image")
    ap.add_argument("--save-plot", type=Path, help="save the result figure to this path")
    ap.add_argument("--debug", action="store_true", help="verbose logging")
    args = ap.parse_args(argv)

    setup_logging(logging.DEBUG if args.debug else logging.INFO,
                  log_file=CFG.results_dir / "pipeline.log")
    if args.query:
        CFG.query_image = args.query
    CFG.make_dirs()

    stages = set(args.stages)
    matches, q_box = None, None

    if "dataset" in stages:
        create_dataset(CFG)
    if "recover" in stages:
        recover_no_face(CFG, detector="retinaface", min_face_px=25, min_conf=0.80)
    if "embed" in stages:
        create_embeddings(CFG)
    if "index" in stages:
        create_index(CFG)
    if "removed" in stages:
        show_removed(CFG, top=10)
    if "search" in stages:
        matches, q_box = search_image(CFG)
    if "plot" in stages:
        if matches is None:
            matches, q_box = search_image(CFG)
        plot_search_result(CFG, matches, q_box, cols=4, save_path=args.save_plot)


if __name__ == "__main__":
    main()
