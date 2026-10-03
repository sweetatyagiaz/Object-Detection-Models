import os
import cv2
import json
import faiss
import numpy as np
import onnxruntime as ort

from collections import defaultdict


class AdaFace:

    INPUT_SIZE = (112, 112)
    DIMENSION = 512

    def __init__(
        self,
        model_path,
        database_dir,
        index_path,
        mapping_path,
        providers=None
    ):
        self.model_path = model_path
        self.database_dir = database_dir
        self.index_path = index_path
        self.mapping_path = mapping_path

        if providers is None:
            providers = [
                "CUDAExecutionProvider",
                "CPUExecutionProvider"
            ]

        self.session = ort.InferenceSession(
            model_path,
            providers=providers
        )

        self.input_name = (
            self.session.get_inputs()[0].name
        )

        self.output_name = (
            self.session.get_outputs()[0].name
        )

        self.index = None
        self.mapping = {}

    def preprocess(
        self,
        image
    ):
        image = cv2.resize(
            image,
            self.INPUT_SIZE
        )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        image = image.astype(
            np.float32
        )

        image = image / 127.5 - 1.0

        image = np.transpose(
            image,
            (2, 0, 1)
        )

        image = np.expand_dims(
            image,
            axis=0
        )

        return image

    def get_embedding(
        self,
        image
    ):
        image = self.preprocess(
            image
        )

        embedding = self.session.run(
            [self.output_name],
            {
                self.input_name: image
            }
        )[0]

        embedding = embedding.flatten()

        embedding = (
            embedding /
            np.linalg.norm(
                embedding
            )
        )

        return embedding.astype(
            np.float32
        )

    def build_index(self):

        embeddings = []
        mapping = {}

        faiss_id = 0

        for person_dir in sorted(
            os.listdir(self.database_dir)
        ):

            person_path = os.path.join(
                self.database_dir,
                person_dir
            )

            if not os.path.isdir(person_path):
                continue

            try:

                person_id = int(
                    person_dir.split(".")[0]
                )

                person_name = (
                    person_dir.split(".", 1)[1]
                )

            except Exception:
                continue

            print(
                f"Processing: {person_name}"
            )

            for root, _, files in os.walk(
                person_path
            ):

                for file in files:

                    if not file.lower().endswith(
                        (
                            ".jpg",
                            ".jpeg",
                            ".png"
                        )
                    ):
                        continue

                    image_path = os.path.join(
                        root,
                        file
                    )

                    image = cv2.imread(
                        image_path
                    )

                    if image is None:
                        continue

                    embedding = (
                        self.get_embedding(
                            image
                        )
                    )

                    embeddings.append(
                        embedding
                    )

                    mapping[
                        str(faiss_id)
                    ] = {
                        "person_id":
                        person_id,

                        "name":
                        person_name.strip(),

                        "image":
                        image_path
                    }

                    faiss_id += 1

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32
        )

        print(
            f"Embeddings Shape: "
            f"{embeddings.shape}"
        )

        #
        # IMPORTANT
        #
        faiss.normalize_L2(
            embeddings
        )

        self.index = faiss.IndexHNSWFlat(
            self.DIMENSION,
            32,
            faiss.METRIC_INNER_PRODUCT
        )

        self.index.hnsw.efConstruction = 200
        self.index.hnsw.efSearch = 100

        self.index.add(
            embeddings
        )

        self.mapping = mapping

        self.save_index()

        print(
            f"Total Embeddings: "
            f"{len(embeddings)}"
        )

        print(
            "FAISS Index Saved"
        )

    def save_index(
        self
    ):
        os.makedirs(
            os.path.dirname(
                self.index_path
            ),
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            self.index_path
        )

        with open(
            self.mapping_path,
            "w"
        ) as file:

            json.dump(
                self.mapping,
                file,
                indent=4
            )

    def load_index(
        self
    ):
        self.index = (
            faiss.read_index(
                self.index_path
            )
        )

        with open(
            self.mapping_path,
            "r"
        ) as file:

            self.mapping = (
                json.load(
                    file
                )
            )

    def search_face(
        self,
        image_path,
        top_k=5,
        threshold=0.65
    ):

        if self.index is None:
            self.load_index()

        image = cv2.imread(
            image_path
        )

        if image is None:
            raise Exception(
                f"Cannot load image: "
                f"{image_path}"
            )

        query_embedding = (
            self.get_embedding(
                image
            )
        )

        query_embedding = (
            query_embedding
            .reshape(1, -1)
            .astype(np.float32)
        )

        #
        # IMPORTANT
        #
        faiss.normalize_L2(
            query_embedding
        )

        similarities, indices = (
            self.index.search(
                query_embedding,
                top_k
            )
        )

        persons = defaultdict(
            list
        )

        for score, idx in zip(
            similarities[0],
            indices[0]
        ):

            if idx < 0:
                continue

            score = float(score)

            if score < threshold:
                continue

            person = self.mapping.get(
                str(idx)
            )

            if person is None:
                continue

            persons[
                person["person_id"]
            ].append(
                {
                    "score": score,
                    "name": person["name"],
                    "image": person["image"]
                }
            )

        results = []

        for person_id, matches in (
            persons.items()
        ):

            best_score = max(
                x["score"]
                for x in matches
            )

            avg_score = (
                sum(
                    x["score"]
                    for x in matches
                )
                /
                len(matches)
            )

            results.append(
                {
                    "person_id":
                    person_id,

                    "name":
                    matches[0]["name"],

                    "best_score":
                    round(
                        best_score,
                        4
                    ),

                    "avg_score":
                    round(
                        avg_score,
                        4
                    ),

                    "matched_images":
                    len(matches)
                }
            )

        results.sort(
            key=lambda x:
            x["best_score"],
            reverse=True
        )

        return results