import pickle
import numpy as np

with open(
    "../../datasets/embeddings/AdaFace/embeddings_scrfd.pkl",
    "rb"
) as fp:

    data = pickle.load(fp)

embedding = data[0]["embedding"]

print(
    np.linalg.norm(
        embedding
    )
)