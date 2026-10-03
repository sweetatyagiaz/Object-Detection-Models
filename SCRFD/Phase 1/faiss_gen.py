from faiss_builder import FAISSBuilder

builder = FAISSBuilder(
    dimension=512,
    m=32
)

builder.build_index(
    embeddings_file="../../datasets/embeddings/AdaFace/embeddings_scrfd.pkl",
    index_file="../../datasets/FAISS/AdaFace/faiss.index",
    gallery_file="../../datasets/FAISS/AdaFace/gallery.pkl"
)
