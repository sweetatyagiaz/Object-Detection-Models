"""
Run the face search pipeline.

Examples:
    python test.py                                   # build everything, then search
    python test.py --stages search plot              # photo search only (index already built)
    python test.py --stages person                   # who is this? (one centroid per folder)
    python test.py --within-person --stages search plot
                                                     # find the person first, then search their folder
    python test.py --stages recover embed index      # retry no-face photos, then rebuild
    python test.py --query ../datasets/images/Other.jpg --stages person search plot
"""
import argparse
import logging
from pathlib import Path

from utils import (Config, create_dataset, create_embeddings, create_index,
                   embed_query, filter_index_to_person, load_pickle_file,
                   plot_search_result, recover_no_face, search_image,
                   search_person, setup_logging, show_removed)

log = logging.getLogger("facesearch")

ALL_STAGES = ["dataset", "recover", "embed", "index", "removed", "person", "search", "plot"]
DEFAULT_STAGES = ["dataset", "embed", "index", "removed", "person", "search", "plot"]  # recover is opt-in

# ---------- Config (edit here) ----------
# Thresholds (strict_threshold, conf_k, dup_threshold, person_threshold) are derived from the
# model automatically. Set any of them below only if you want to override the default.
CFG = Config(
    database_dir=Path("../datasets/raw_data/"),
    crops_dir=Path("../datasets/dataset_deepface/"),
    results_dir=Path("../datasets/results/"),
    query_image=Path("../datasets/images/Tejrit.jpg"),

    model="Facenet512",            # e.g. "ArcFace": thresholds follow automatically
    detector="yunet",              # crop dataset detector
    query_detector="retinaface",   # strongest detector, since this one face drives the search
    expand=10,

    min_face_px=40,
    min_conf=0.90,

    scope="folder",                # "folder" or "global"

    top_k=12,
    top_people=5,
    min_photos_per_person=1,       # raise to 3+ to ignore folders with very few photos
    min_dist=0.0,                  # 0.05 hides the query photo itself if it is in the database
    query_face_idx=None,           # None = largest face

    # strict_threshold=0.30,
    # person_threshold=0.35,
    # dup_threshold=0.05,
    # conf_k=15.0,
)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stages", nargs="+", choices=ALL_STAGES, default=DEFAULT_STAGES)
    ap.add_argument("--query", type=Path, help="override the query image")
    ap.add_argument("--within-person", action="store_true",
                    help="photo search only inside the best-matching person's folder")
    ap.add_argument("--save-plot", type=Path, help="save the result figure to this path")
    ap.add_argument("--debug", action="store_true", help="verbose logging")
    args = ap.parse_args(argv)

    setup_logging(logging.DEBUG if args.debug else logging.INFO,
                  log_file=CFG.results_dir / "pipeline.log")
    if args.query:
        CFG.query_image = args.query
    CFG.make_dirs()
    log.info("Config: %s", CFG.describe())

    stages = set(args.stages)

    # ----- Build stages -----
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

    # ----- Query stages -----
    if not stages & {"person", "search", "plot"}:
        return

    index = load_pickle_file(CFG.index_path)     # load once, reuse for every query stage
    query = embed_query(CFG)                     # embed the query photo once
    q_box = query[1]
    matches = None

    people = []
    if "person" in stages or args.within_person:
        people = search_person(CFG, index, query=query)

    if "search" in stages or "plot" in stages:
        search_index = index
        if args.within_person:
            if people and people[0].dist < CFG.person_threshold:
                search_index = filter_index_to_person(index, people[0].person)
            else:
                log.warning("No confident person found, searching all photos instead.")
        matches, q_box = search_image(CFG, search_index, query=query)

    if "plot" in stages and matches is not None:
        plot_search_result(CFG, matches, q_box, cols=4, save_path=args.save_plot)


if __name__ == "__main__":
    main()
