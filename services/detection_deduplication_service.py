from datetime import datetime, timedelta


class DetectionDeduplicationService:

    def __init__(self):

        self.last_detection = {}

    def should_store(
        self,
        person_id,
        camera_id,
        timeout_minutes=30
    ):

        key = (
            person_id,
            camera_id
        )

        now = datetime.now()

        if key not in self.last_detection:

            self.last_detection[key] = now

            return True

        last_seen = self.last_detection[key]

        if (
            now - last_seen
        ) > timedelta(
            minutes=timeout_minutes
        ):

            self.last_detection[key] = now

            return True

        return False