from pathlib import Path

from utils import create_dataset, create_embeddings, create_index, removed_files_list, \
    search_image, plot_search_result

# ---------- Config ----------
MODEL = "Facenet512" 

DATABASE_DIR = Path("../datasets/raw_data/")
CROPS_DIR = Path("../datasets/dataset_deepface/")
MANIFEST = Path("../datasets/results/crops_manifest_deepface.json")
STATE = Path("../datasets/results/crops_state_deepface.json")   # resume info
EMB_PATH = Path(f"../datasets/results/emb_all_{MODEL}_deepface.pkl")    # every crop, before dedup
INDEX_PATH = Path(f"../datasets/results/index_{MODEL}_deepface.pkl")    # final, deduplicated
QUERY_IMAGE = "../datasets/images/Tejrit.jpg"

QUERY_DETECTOR = "retinaface"   # strongest detector, since this one face drives the search
QUERY_FACE_IDX = None           # None = largest face; or 0, 1, ... to force one

STRICT_THRESHOLD = 0.30         # Facenet512 cosine; ArcFace would be ~0.68
TOP_K = 12
MIN_DIST = 0.0                  # set to 0.05 to hide the query photo itself if it is in the database
CONF_K = 15                     # steepness of the confidence curve (ArcFace: ~7)


DETECTOR = "yunet"          # or "retinaface" for better quality
EXTS = (".jpg", ".jpeg", ".png")
MIN_FACE_PX, MIN_CONF = 40, 0.90
EXPAND = 10                 # expand_percentage, keep the same for the query image

DUP_THRESHOLD = 0.05      # cosine distance below this = same picture
SCOPE = "folder"          # "folder": dedupe within the same folder, "global": across all folders



# Create folders if not exist
CROPS_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST.parent.mkdir(parents=True, exist_ok=True)



#----------------------------------------------------
# CREATE DATASET
create_dataset(DATABASE_DIR=DATABASE_DIR, CROPS_DIR=CROPS_DIR, MANIFEST=MANIFEST, 
               STATE=STATE, DETECTOR=DETECTOR, EXTS=EXTS, MIN_FACE_PX=MIN_FACE_PX,
               MIN_CONF=MIN_CONF, EXPAND=EXPAND)


# CREATE EMBEDDINGS
# create_embeddings(MODEL=MODEL, CROPS_DIR=CROPS_DIR, MANIFEST=MANIFEST, EMB_PATH=EMB_PATH)


# CREATE INDEX
create_index(EMB_PATH=EMB_PATH, CROPS_DIR=CROPS_DIR, INDEX_PATH=INDEX_PATH, 
             DUP_THRESHOLD=DUP_THRESHOLD, MANIFEST=MANIFEST, SCOPE=SCOPE)

# SHOW REMOVE FILE LIST
removed_files_list(INDEX_PATH=INDEX_PATH)

# SEARCH IMAGE
matches, q_box = search_image(MODEL=MODEL, DATABASE_DIR=DATABASE_DIR, INDEX_PATH=INDEX_PATH, 
             QUERY_IMAGE=QUERY_IMAGE, QUERY_DETECTOR=QUERY_DETECTOR, EXPAND=EXPAND,
             QUERY_FACE_IDX=QUERY_FACE_IDX, MIN_DIST=MIN_DIST,
             STRICT_THRESHOLD=STRICT_THRESHOLD, CONF_K=CONF_K, TOP_K=TOP_K)

# PLOT SEARCH RESULT
plot_search_result(cols=4, q_box=q_box, matches=matches, QUERY_IMAGE=QUERY_IMAGE, 
                   STRICT_THRESHOLD=STRICT_THRESHOLD)