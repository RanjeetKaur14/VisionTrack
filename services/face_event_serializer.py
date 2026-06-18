import json


class FaceEventSerializer:

    @staticmethod
    def serialize(event):

        return json.dumps({
            "store_id": event.store_id,
            "camera_id": event.camera_id,
            "pic_id": event.pic_id,
            "timestamp": event.timestamp
        })