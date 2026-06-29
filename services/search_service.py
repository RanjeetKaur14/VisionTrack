import numpy as np
from collections import deque
import shutil
import os


from services.face_recognition_service import (
    FaceRecognitionService
)

from services.milvus_service import (
    MilvusService
)

class SearchService:

    def __init__(self):

        self.face_service = (
            FaceRecognitionService()
        )

        self.milvus_service = (
            MilvusService()
        )
        self.search_threshold = 0.40


    def get_embedding(self, image_path):

        embedding, error = (
            self.face_service.generate_search_embedding(
                image_path
            )
        )

        if embedding is None:

            self.save_invalid_face(
                image_path
            )

        return embedding, error

    def cosine_similarity(
        self,
        embedding1,
        embedding2
    ):

        return float(
            np.dot(
                embedding1,
                embedding2
            )
        )

    def cluster_embeddings(
        self,
        embedding_data,
        threshold=0.40
    ):

        n = len(embedding_data)

        graph = {
            i: []
            for i in range(n)
        }

        # Build similarity graph

        for i in range(n):

            for j in range(i + 1, n):

                similarity = self.cosine_similarity(
                    embedding_data[i]["embedding"],
                    embedding_data[j]["embedding"]
                )

                print(
                    f"{i} <-> {j} = {similarity:.4f}"
                )

                if similarity >= threshold:

                    graph[i].append(j)
                    graph[j].append(i)

        visited = set()

        clusters = []

        for i in range(n):

            if i in visited:
                continue

            queue = deque([i])

            visited.add(i)

            cluster = []

            while queue:

                node = queue.popleft()

                cluster.append(
                    embedding_data[node]
                )

                for neighbour in graph[node]:

                    if neighbour not in visited:

                        visited.add(neighbour)

                        queue.append(
                            neighbour
                        )

            clusters.append(cluster)

        return clusters

    def average_embedding(
        self,
        cluster
    ):

        embeddings = np.array(

            [
                item["embedding"]
                for item in cluster
            ]

        )

        avg = np.mean(
            embeddings,
            axis=0
        )

        avg = avg / np.linalg.norm(
            avg
        )

        return avg

    def representative_embedding(
        self,
        cluster
    ):

        center = self.average_embedding(
            cluster
        )

        best_item = None

        best_similarity = -1

        for item in cluster:

            similarity = self.cosine_similarity(

                center,

                item["embedding"]

            )

            if similarity > best_similarity:

                best_similarity = similarity

                best_item = item

        return best_item

    def search_embedding(
        self,
        embedding
    ):

        results = (
            self.milvus_service.search_person(
                embedding
            )
        )

        if len(results) == 0 or len(results[0]) == 0:

            return {

                "matched": False,

                "message":
                "Person not found"

            }

        best_match = results[0][0]

        if best_match.score < self.search_threshold:

            return {

                "matched": False,

                "message":
                "Below threshold",

                "score":
                round(
                    best_match.score,
                    4
                )

            }

        person_id = best_match.id

        person_events = (
            self.milvus_service.search_events_by_person(
                person_id
            )
        )

        person_events.sort(

            key=lambda x:
            x["timestamp"],

            reverse=True

        )

        for event in person_events:

            filename = (
                event["image_path"]
                .split("/")[-1]
            )

            event["image_url"] = (

                f"http://192.168.5.231:8000/"
                f"saved_faces/{filename}"

            )

        return {

            "matched": True,

            "person_id":
            person_id,

            "match_score":
            round(
                best_match.score,
                4
            ),

            "total_events":
            len(person_events),

            "events":
            person_events

        }

    def search_multiple(
        self,
        image_paths
    ):

        embedding_data = []

        invalid_images = []

        # -----------------------------------
        # Generate embeddings
        # -----------------------------------

        for image_path in image_paths:

            embedding, error = self.get_embedding(
                image_path
            )

            if embedding is None:

                invalid_images.append({

                    "image": os.path.basename(
                        image_path
                    ),

                    "reason": error

                })

                continue

            embedding_data.append({

                "path": image_path,

                "filename": os.path.basename(
                    image_path
                ),

                "embedding": embedding

            })

        if len(embedding_data) == 0:

            return {

                "success": False,

                "message":
                "No valid faces found.",

                "invalid_images":
                invalid_images

            }

        # -----------------------------------
        # Cluster embeddings
        # -----------------------------------

        clusters = self.cluster_embeddings(
            embedding_data
        )

        print(
            f"Detected {len(clusters)} unique people."
        )

        results = []

        # -----------------------------------
        # Search every cluster
        # -----------------------------------

        for index, cluster in enumerate(
            clusters,
            start=1
        ):

            representative = (
                self.representative_embedding(
                    cluster
                )
            )

            cluster_result = {

                "cluster_id": index,

                "representative_image":
                representative["filename"],

                "uploaded_images": [

                    item["filename"]

                    for item in cluster

                ]

            }

            search_result = (
                self.search_embedding(

                    representative["embedding"]

                )
            )

            cluster_result.update(
                search_result
            )

            results.append(
                cluster_result
            )

        return {

            "success": True,

            "total_uploaded":
            len(image_paths),

            "valid_faces":
            len(embedding_data),

            "invalid_faces":
            len(invalid_images),

            "unique_people":
            len(clusters),

            "invalid_images":
            invalid_images,

            "results":
            results

        }
    def search_person(self, image_path):

        embedding, error = self.get_embedding(
            image_path
        )

        if embedding is None:

            return {

                "success": False,

                "message": error

            }

        return self.search_embedding(
            embedding
        )
        
    def save_invalid_face(
        self,
        image_path
    ):

        os.makedirs(
            "invalid_faces",
            exist_ok=True
        )

        shutil.copy(
            image_path,
            os.path.join(
                "invalid_faces",
                os.path.basename(
                    image_path
                )
            )
        )