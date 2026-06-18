from services.face_recognition_service import FaceRecognitionService
from services.milvus_service import MilvusService

face_service = FaceRecognitionService()
milvus = MilvusService()

embedding = face_service.generate_embedding(
    "saved_faces/IMG_20260603_160300.jpg"
)

if embedding is not None:

    person_id = milvus.insert_embedding(
        embedding
    )

    print("Inserted ID:", person_id)

    results = milvus.search_embedding(
        embedding
    )

    for hit in results[0]:
        print("Matched ID:", hit.id)
        print("Score:", hit.score)

else:
    print("No face found")