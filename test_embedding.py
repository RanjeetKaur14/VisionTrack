import cv2
from insightface.app import FaceAnalysis

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(ctx_id=0)

recognition = app.models["recognition"]

img = cv2.imread(
    "saved_faces/IMG_20260604_200001.jpg"
)

img = cv2.resize(img, (112, 112))

embedding = recognition.get_feat(img)

print(type(embedding))
print(embedding.shape)