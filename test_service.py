from services.face_recognition_service import FaceRecognitionService

service = FaceRecognitionService()

embedding = service.generate_embedding(
    "saved_faces/face_1.jpg"
)

if embedding is not None:
    print("Embedding Generated")
    print("Length:", len(embedding))
else:
    print("No Face Found")