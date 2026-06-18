import cv2
import os
from datetime import datetime
import time

from services.face_detection_service import FaceDetectionService
from models.face_event import FaceEvent
from services.face_event_serializer import FaceEventSerializer
from services.kafka_producer_service import KafkaProducerService
from services.kafka_consumer_service import KafkaConsumerService
from services.config_service import ConfigService
from services.invalid_face_service import InvalidFaceService
from services.camera_thread_service import CameraThreadService
from services.recognition_worker import RecognitionWorker


os.makedirs("saved_faces", exist_ok=True)
os.makedirs(
    "invalid_faces",
    exist_ok=True
)

camera = CameraThreadService()
producer = KafkaProducerService()
detector = FaceDetectionService()
consumer = KafkaConsumerService()
config = ConfigService.load()

face_count = 0

CAPTURE_COOLDOWN = 2
last_capture_time = 0


def process_faces(faces):

    global face_count

    for face in faces:

        is_valid, reason = detector.validate_face(face)

        if not is_valid:

            timestamp = datetime.now().isoformat()

            invalid_name = (
                f"INVALID_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            )

            invalid_path = (
                f"invalid_faces/{invalid_name}.jpg"
            )

            cv2.imwrite(
                invalid_path,
                face
            )

            InvalidFaceService.save(
                filename=f"{invalid_name}.jpg",
                timestamp=timestamp,
                reason=reason,
                camera_id=config["camera_id"]
            )

            print(
                f"INVALID FACE SAVED: "
                f"{reason}"
            )

            continue

        processed_face = detector.preprocess_face(face)

        timestamp = datetime.now().isoformat()

        pic_id = (
            f"IMG_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        )

        filename = f"saved_faces/{pic_id}.jpg"

        cv2.imwrite(
            filename,
            processed_face
        )

        event = FaceEvent(
            store_id=config["store_id"],
            camera_id=config["camera_id"],
            pic_id=pic_id,
            timestamp=timestamp
        )

        event_data = {
            "store_id": event.store_id,
            "camera_id": event.camera_id,
            "pic_id": event.pic_id,
            "timestamp": event.timestamp
        }

        producer.publish_face_event(
            event_data
        )

        print(
            f"Saved: {filename}"
        )

        face_count += 1


worker = RecognitionWorker(
    process_faces
)


while True:

    frame = camera.get_frame()

    if frame is None:
        continue

    detections = detector.detect_faces(frame)

    faces = detector.crop_faces(
        frame,
        detections
    )

    detector.draw_boxes(
        frame,
        detections
    )

    cv2.imshow(
        "Face Detection",
        frame
    )

    current_time = time.time()

    if (
        len(faces) > 0
        and
        current_time - last_capture_time
        >= CAPTURE_COOLDOWN
    ):

        last_capture_time = current_time

        worker.add_job(
            faces.copy()
        )

        print(
            f"AUTO CAPTURE | "
            f"Faces: {len(faces)}"
        )

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break


camera.release()

cv2.destroyAllWindows()