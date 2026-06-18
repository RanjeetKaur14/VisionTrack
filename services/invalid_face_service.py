import json
import os


class InvalidFaceService:

    FILE = "invalid_faces/metadata.json"

    @classmethod
    def save(
        cls,
        filename,
        timestamp,
        reason,
        camera_id
    ):

        data = []

        if os.path.exists(cls.FILE):

            with open(cls.FILE, "r") as f:
                try:
                    data = json.load(f)
                except:
                    data = []

        data.append({
            "filename": filename,
            "timestamp": timestamp,
            "reason": reason,
            "camera_id": camera_id
        })

        with open(cls.FILE, "w") as f:
            json.dump(
                data,
                f,
                indent=2
            )