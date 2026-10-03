import pickle

with open(
    "../../datasets/embeddings/AdaFace/embeddings_scrfd.pkl",
    "rb"
) as fp:

    data = pickle.load(fp)

print(len(data))

print(
    data[0]["person_name"]
)

print(
    data[0]["embedding"].shape
)