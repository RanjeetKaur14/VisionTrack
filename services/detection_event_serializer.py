import json

class DetectionEventSerializer:

    @staticmethod
    def serialize(event):

        return {
            "person_id": event.person_id,
            "embedding": event.embedding,

            "store_id": event.store_id,
            "camera_id": event.camera_id,
            "pic_id": event.pic_id,

            "timestamp": event.timestamp,
            "image_path": event.image_path
        }