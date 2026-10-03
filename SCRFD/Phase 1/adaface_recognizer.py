from adaface import AdaFace


class AdaFaceRecognizer:

    def __init__(
        self,
        model_path,
        database_dir=None,
        index_path=None,
        mapping_path=None,
        min_quality=None
    ):

        self.model = AdaFace(
            model_path=model_path,
            database_dir=database_dir,
            index_path=index_path,
            mapping_path=mapping_path,
            min_quality=min_quality
        )

    def get_embedding(
        self,
        image
    ):
        """
        Parameters
        ----------
        image : numpy.ndarray
            BGR image

        Returns
        -------
        dict | None

        Example:
        {
            "embedding": ndarray(512,),
            "quality": 17.42
        }
        """

        result = self.model.get_embedding(
            image
        )

        if result is None:
            return None

        embedding, quality = result

        return {
            "embedding": embedding,
            "quality": quality
        }

    def search_image(
        self,
        image,
        top_k=5,
        threshold=0.4
    ):
        """
        Search using image array.
        """

        return self.model.search_image(
            image=image,
            top_k=top_k,
            threshold=threshold
        )

    def search_face(
        self,
        image_path,
        top_k=5,
        threshold=0.4
    ):
        """
        Search using image path.
        """

        return self.model.search_face(
            image_path=image_path,
            top_k=top_k,
            threshold=threshold
        )

    def build_index(self):
        """
        Build FAISS index.
        """

        self.model.build_index()

    def load_index(self):
        """
        Load existing FAISS index.
        """

        self.model.load_index()