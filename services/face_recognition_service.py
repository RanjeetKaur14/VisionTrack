import cv2
from insightface.app import FaceAnalysis
import time
import os

class FaceRecognitionService:

    def __init__(self):

        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=[
                "CPUExecutionProvider"
            ]
        )

        self.app.prepare(
            ctx_id=-1,
            det_size=(128, 128)
        )


    def generate_embedding(self, image_path):

        t0 = time.time()

        print(f"[PID {os.getpid()}] START")

        t1 = time.time()

        image = cv2.imread(image_path)

        print(
            f"[PID {os.getpid()}] "
            f"IMREAD: {time.time()-t1:.3f}s"
        )

        if image is None:
            print("IMAGE NONE")
            return None

        t2 = time.time()

        faces = self.app.get(image)

        print(
            f"[PID {os.getpid()}] "
            f"APP.GET: {time.time()-t2:.3f}s"
        )

        if len(faces) == 0:
            print("NO FACE")
            return None

        t3 = time.time()

        embedding = faces[0].normed_embedding

        print(
            f"[PID {os.getpid()}] "
            f"EMBED ACCESS: {time.time()-t3:.6f}s"
        )

        print(
            f"[PID {os.getpid()}] "
            f"TOTAL: {time.time()-t0:.3f}s"
        )

        return embedding