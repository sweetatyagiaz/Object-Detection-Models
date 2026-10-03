import faiss

index = faiss.read_index(
    "../../datasets/FAISS/AdaFace/faiss.index"
)

print(
    index.ntotal
)