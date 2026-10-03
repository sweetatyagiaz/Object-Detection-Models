import os
import pickle

import faiss
import numpy as np


class FAISSBuilder:

    def __init__(
        self,
        dimension=512,
        m=32
    ):

        self.dimension = dimension
        self.m = m

    def build_index(
        self,
        embeddings_file,
        index_file,
        gallery_file
    ):

        print("\nLoading embeddings...")

        with open(
            embeddings_file,
            "rb"
        ) as fp:

            data = pickle.load(fp)

        print(
            f"Loaded {len(data)} embeddings"
        )

        index = faiss.IndexHNSWFlat(
            self.dimension,
            self.m
        )

        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = 100

        vectors = []
        gallery = []

        for idx, item in enumerate(data):

            embedding = np.asarray(
                item["embedding"],
                dtype=np.float32
            )

            #
            # Normalize
            #
            norm = np.linalg.norm(
                embedding
            )

            if norm > 0:

                embedding = (
                    embedding / norm
                )

            vectors.append(
                embedding
            )

            gallery.append(
                {
                    "faiss_id": idx,
                    "person_id": item[
                        "person_id"
                    ],
                    "person_name": item[
                        "person_name"
                    ],
                    "image_name": item[
                        "image_name"
                    ],
                    "face_size": item.get(
                        "face_size"
                    ),
                    "dataset_quality": item.get(
                        "dataset_quality"
                    ),
                    "adaface_quality": item.get(
                        "adaface_quality"
                    )
                }
            )

        vectors = np.asarray(
            vectors,
            dtype=np.float32
        )

        print(
            f"Adding {len(vectors)} vectors..."
        )

        index.add(
            vectors
        )

        os.makedirs(
            os.path.dirname(
                index_file
            ),
            exist_ok=True
        )

        faiss.write_index(
            index,
            index_file
        )

        with open(
            gallery_file,
            "wb"
        ) as fp:

            pickle.dump(
                gallery,
                fp
            )

        print("\n" + "=" * 60)
        print("FAISS BUILD COMPLETE")
        print("=" * 60)

        print(
            f"Vectors      : {index.ntotal}"
        )

        print(
            f"Index File   : {index_file}"
        )

        print(
            f"Gallery File : {gallery_file}"
        )

        print("=" * 60)

        return index