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

        # thresholds
        self.min_det_score = 0.6
        self.min_face_size = 80
        self.blur_threshold = 20

        self.min_eye_distance = 25
        self.max_nose_offset = 20


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
            return None, "IMAGE_NONE"

        t2 = time.time()

        faces = self.app.get(image)

        print(
            f"[PID {os.getpid()}] "
            f"APP.GET: {time.time()-t2:.3f}s"
        )

        if len(faces) == 0:
            print("NO FACE")
            return None, "NO_FACE"

        face = faces[0]

        #################################
        # Detection confidence
        #################################

        print(
            f"DET SCORE: {face.det_score:.3f}"
        )

        if face.det_score < self.min_det_score:
            print("LOW CONFIDENCE FACE")

            return None, "LOW_CONFIDENCE"

        #################################
        # Face size
        #################################

        bbox = face.bbox.astype(int)

        x1, y1, x2, y2 = bbox

        width = x2 - x1
        height = y2 - y1

        print(
            f"FACE SIZE: {width}x{height}"
        )

        if width < self.min_face_size or height < self.min_face_size:
            print("FACE TOO SMALL")

            return None, "SMALL_FACE"

        #################################
        # Safe crop
        #################################

        h, w = image.shape[:2]

        x1 = max(0, x1)
        y1 = max(0, y1)

        x2 = min(w, x2)
        y2 = min(h, y2)

        face_crop = image[
            y1:y2,
            x1:x2
        ]

        if face_crop.size == 0:
            print("EMPTY CROP")

            return None, "INVALID_CROP"

        #################################
        # Blur detection
        #################################

        gray = cv2.cvtColor(
            face_crop,
            cv2.COLOR_BGR2GRAY
        )

        blur_score = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        print(
            f"BLUR SCORE: {blur_score:.2f}"
        )

        if blur_score < self.blur_threshold:
            print("BLURRY FACE")

            return None, "BLURRY"

        #################################
        # Keypoints
        #################################

        kps = face.kps

        left_eye = kps[0]
        right_eye = kps[1]
        nose = kps[2]

        #################################
        # Eye distance
        #################################

        eye_distance = abs(
            right_eye[0] - left_eye[0]
        )

        print(
            f"EYE DISTANCE: {eye_distance:.2f}"
        )

        if eye_distance < self.min_eye_distance:

            print("SIDE PROFILE")

            return None, "SIDE_PROFILE"

        #################################
        # Nose offset
        #################################

        face_center = (
            x1 + x2
        ) / 2

        nose_offset = abs(
            nose[0] - face_center
        )

        print(
            f"NOSE OFFSET: {nose_offset:.2f}"
        )

        if nose_offset > self.max_nose_offset:

            print("EXTREME POSE")

            return None, "SIDE_PROFILE"

        #################################
        # Embedding
        #################################

        t3 = time.time()

        embedding = face.normed_embedding

        print(
            f"[PID {os.getpid()}] "
            f"EMBED ACCESS: {time.time()-t3:.6f}s"
        )

        print(
            f"[PID {os.getpid()}] "
            f"TOTAL: {time.time()-t0:.3f}s"
        )

        return embedding, None