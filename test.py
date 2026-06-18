from insightface.app import FaceAnalysis
import cv2
import time

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(128,128)
)

img = cv2.imread(
    r"saved_faces\IMG_20260610_134312_717381.jpg"
)

for i in range(10):

    start = time.time()

    faces = app.get(img)

    print(
        f"Run {i+1}: "
        f"{time.time()-start:.3f}s"
    )