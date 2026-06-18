from services.face_recognition_service import (
    FaceRecognitionService
)

from services.milvus_service import (
    MilvusService
)
import shutil
import os


class SearchService:

    def __init__(self):

        self.face_service = (
            FaceRecognitionService()
        )

        self.milvus_service = (
            MilvusService()
        )

    def search_person(self, image_path):

        embedding = (
            self.face_service.generate_embedding(
                image_path
            )
        )

        if embedding is None:

            self.save_invalid_face(
                image_path
            )

            return {
                "success": False,
                "message":
                "No face detected"
            }

        results = (
            self.milvus_service.search_person(
                embedding
            )
        )

        if len(results) == 0 or len(results[0]) == 0:

            return {
                "error": "Person not found"
            }

        best_match = results[0][0]
        search_threshold = 0.40

        if best_match.score < search_threshold:

            self.save_invalid_face(
                image_path
            )

            return {
                "success": False,
                "message":
                "No matching person found",
                "score":
                best_match.score
            }

        person_id = best_match.id

        person_events = (
            self.milvus_service.search_events_by_person(
                person_id
            )
        )

        if len(person_events) == 0:

            return {
                "person_id": person_id,
                "match_score": round(
                    best_match.score,
                    4
                ),
                "message": "No detection history found"
            }

        person_events.sort(
            key=lambda x: x["timestamp"],
            reverse=True
        )

        for event in person_events:

            filename = (
                event["image_path"]
                .split("/")[-1]
            )

            event["image_url"] = (
                f"http://127.0.0.1:8000/saved_faces/{filename}"
            )

        return {
            "person_id": person_id,
            "match_score": round(
                best_match.score,
                4
            ),
            "total_events": len(
                person_events
            ),
            "events": person_events
        }
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