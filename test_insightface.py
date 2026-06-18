import cv2
from insightface.app import FaceAnalysis

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

img = cv2.imread(
    "saved_faces/IMG_20260604_200001.jpg"
)
img = cv2.resize(img, (640, 640))

print("Shape:", img.shape)

cv2.imshow("Test Image", img)
cv2.waitKey(0)

faces = app.get(img)

print("Faces:", len(faces))