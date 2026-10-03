import pickle

import cv2
import faiss
import numpy as np
from collections import defaultdict



class FaceSearcher:

    def __init__(
        self,
        recognizer,
        index_file,
        gallery_file
    ):

        self.recognizer = recognizer

        self.index = faiss.read_index(
            index_file
        )

        with open(
            gallery_file,
            "rb"
        ) as fp:

            self.gallery = pickle.load(
                fp
            )

        print(
            f"Loaded FAISS vectors: "
            f"{self.index.ntotal}"
        )

    def search_embedding(
        self,
        embedding,
        top_k=5
    ):

        embedding = np.asarray(
            embedding,
            dtype=np.float32
        )

        norm = np.linalg.norm(
            embedding
        )

        if norm > 0:

            embedding = (
                embedding / norm
            )

        embedding = embedding.reshape(
            1,
            -1
        )

        distances, indices = (
            self.index.search(
                embedding,
                top_k
            )
        )

        results = []

        for score, idx in zip(
            distances[0],
            indices[0]
        ):

            if idx < 0:
                continue

            person = self.gallery[idx]

            results.append(
                {
                    "faiss_id": idx,
                    "score": float(score),
                    "person_id":
                        person["person_id"],
                    "person_name":
                        person["person_name"],
                    "image_name":
                        person["image_name"],
                    "face_size":
                        person.get(
                            "face_size"
                        ),
                    "dataset_quality":
                        person.get(
                            "dataset_quality"
                        ),
                    "adaface_quality":
                        person.get(
                            "adaface_quality"
                        )
                }
            )

        return results

    def search_image(
        self,
        image,
        top_k=5
    ):

        result = (
            self.recognizer
            .get_embedding(
                image
            )
        )

        if result is None:
            return []

        embedding = result[
            "embedding"
        ]

        return self.search_embedding(
            embedding,
            top_k
        )

    def search_image_file(
        self,
        image_path,
        top_k=5
    ):

        image = cv2.imread(
            image_path
        )

        if image is None:

            raise ValueError(
                f"Cannot read image: "
                f"{image_path}"
            )

        return self.search_image(
            image=image,
            top_k=top_k
        )

    def search_person(
        self,
        image=None,
        aligned_face=None,
        top_k=20,
        threshold=0.70
    ):
        """
        Search and return unique persons instead of image matches.

        Parameters
        ----------
        image : np.ndarray
            Raw image

        aligned_face : np.ndarray
            Already aligned face

        top_k : int
            Number of FAISS results

        threshold : float
            Recognition threshold

        Returns
        -------
        list
        """

        #
        # Get image matches
        #
        if aligned_face is not None:

            matches = self.search_aligned_face(
                aligned_face=aligned_face,
                top_k=top_k
            )

        else:

            matches = self.search_image(
                image=image,
                top_k=top_k
            )

        #
        # Group by person
        #
        grouped = defaultdict(list)

        for match in matches:

            grouped[
                match["person_id"]
            ].append(match)

        #
        # Create person-level results
        #
        persons = []

        for person_id, person_matches in grouped.items():

            scores = [
                item["score"]
                for item in person_matches
            ]

            best_score = max(scores)

            avg_score = (
                sum(scores) /
                len(scores)
            )

            persons.append(
                {
                    "person_id":
                        person_id,

                    "person_name":
                        person_matches[0][
                            "person_name"
                        ],

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

                    "matches":
                        len(scores)
                }
            )

        #
        # Apply threshold
        #
        persons = [
            person
            for person in persons
            if person["best_score"] >= threshold
        ]

        #
        # Sort by best score
        #
        persons.sort(
            key=lambda x:
            x["best_score"],
            reverse=True
        )

        return persons