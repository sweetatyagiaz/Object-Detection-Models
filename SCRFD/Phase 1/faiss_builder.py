import os
import pickle
from collections import defaultdict

import faiss
import numpy as np


class FAISSBuilder:

    def __init__(
        self,
        dimension=512,
        m=32,
        similarity_threshold=0.998,
        max_embeddings_per_person=50
    ):

        self.dimension = dimension
        self.m = m
        self.similarity_threshold = similarity_threshold
        self.max_embeddings_per_person = max_embeddings_per_person

    def _normalize(
        self,
        embedding
    ):

        embedding = np.asarray(
            embedding,
            dtype=np.float32
        )

        norm = np.linalg.norm(
            embedding
        )

        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _select_representatives(
        self,
        records
    ):

        selected = []

        for record in records:

            embedding = record[
                "embedding"
            ]

            keep = True

            for existing in selected:

                similarity = np.dot(
                    embedding,
                    existing["embedding"]
                )

                print(
                    f"{record['image_name']} "
                    f"vs "
                    f"{existing['image_name']} "
                    f"= {similarity:.4f}"
                )

                if (
                    similarity >=
                    self.similarity_threshold
                ):
                    keep = False
                    break

            if keep:

                selected.append(
                    record
                )

            if (
                len(selected) >=
                self.max_embeddings_per_person
            ):
                break

        return selected

    def build_index(
        self,
        embeddings_file,
        index_file,
        gallery_file
    ):

        print(
            "\nLoading embeddings..."
        )

        with open(
            embeddings_file,
            "rb"
        ) as fp:

            data = pickle.load(
                fp
            )

        print(
            f"Loaded {len(data)} embeddings"
        )

        #
        # Group by person
        #
        person_embeddings = defaultdict(
            list
        )

        for item in data:

            item["embedding"] = (
                self._normalize(
                    item["embedding"]
                )
            )

            person_embeddings[
                item["person_id"]
            ].append(
                item
            )

        #
        # Remove duplicates
        #
        filtered = []

        total_before = len(
            data
        )

        for person_id in sorted(
            person_embeddings.keys()
        ):

            records = (
                person_embeddings[
                    person_id
                ]
            )

            selected = (
                self._select_representatives(
                    records
                )
            )

            filtered.extend(
                selected
            )

            print(
                f"{records[0]['person_name']}"
                f" : {len(records)}"
                f" -> {len(selected)}"
            )

        total_after = len(
            filtered
        )

        #
        # Build FAISS
        #
        index = faiss.IndexHNSWFlat(
            self.dimension,
            self.m
        )

        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = 100

        vectors = []
        gallery = []

        for idx, item in enumerate(
            filtered
        ):

            vectors.append(
                item["embedding"]
            )

            gallery.append(
                {
                    "faiss_id": idx,
                    "person_id":
                        item["person_id"],
                    "person_name":
                        item["person_name"],
                    "image_name":
                        item["image_name"],
                    "face_size":
                        item.get(
                            "face_size"
                        ),
                    "dataset_quality":
                        item.get(
                            "dataset_quality"
                        ),
                    "adaface_quality":
                        item.get(
                            "adaface_quality"
                        )
                }
            )

        vectors = np.asarray(
            vectors,
            dtype=np.float32
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

        print(
            "\n" +
            "=" * 60
        )

        print(
            "FAISS BUILD COMPLETE"
        )

        print(
            "=" * 60
        )

        print(
            f"Original Vectors : "
            f"{total_before}"
        )

        print(
            f"Filtered Vectors : "
            f"{total_after}"
        )

        print(
            f"Reduction        : "
            f"{total_before-total_after}"
        )

        print(
            f"FAISS Vectors    : "
            f"{index.ntotal}"
        )

        print(
            f"Index File       : "
            f"{index_file}"
        )

        print(
            f"Gallery File     : "
            f"{gallery_file}"
        )

        print(
            "=" * 60
        )

        return index