import cv2
from ultralytics import YOLO


class FaceDetectionService:

    def __init__(self):
        self.model = YOLO("models/yolov8n-face-lindevs.pt")

    def detect_faces(self, frame):

        detections = []

        results = self.model(frame, verbose=False)

        for result in results:
            
            for box in result.boxes:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                h, w = frame.shape[:2]

                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)

                detections.append((x1, y1, x2, y2))

        return detections

    def crop_faces(self, frame, detections):

        faces = []

        h, w = frame.shape[:2]

        for x1, y1, x2, y2 in detections:

            face_width = x2 - x1
            face_height = y2 - y1

            padding = int(
                0.15 * max(face_width, face_height)
            )

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            size = max(face_width, face_height) + (2 * padding)

            nx1 = max(0, cx - size // 2)
            ny1 = max(0, cy - size // 2)
            nx2 = min(w, cx + size // 2)
            ny2 = min(h, cy + size // 2)

            face_crop = frame[ny1:ny2, nx1:nx2]

            if face_crop.size != 0:
                faces.append(face_crop)

        return faces

    def validate_face(self, face):

        if face.size == 0:
            return False, "empty_face"

        face_h, face_w = face.shape[:2]

        if face_w < 120 or face_h < 120:

            print(
                f"Rejected Small Face: "
                f"{face_w} x {face_h}"
            )

            return False, "too_small"

        return True, "valid"

    def preprocess_face(self, face):
        return face

    def draw_boxes(self, frame, detections):

        for x1, y1, x2, y2 in detections:

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

        return frame