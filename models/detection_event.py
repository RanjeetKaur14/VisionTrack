class DetectionEvent:

    def __init__(
        self,
        person_id,
        embedding,
        store_id,
        camera_id,
        pic_id,
        timestamp,
        image_path
    ):

        self.person_id = person_id
        self.embedding = embedding

        self.store_id = store_id
        self.camera_id = camera_id
        self.pic_id = pic_id

        self.timestamp = timestamp
        self.image_path = image_path