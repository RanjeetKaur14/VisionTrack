from dataclasses import dataclass


@dataclass
class FaceEvent:
    store_id: str
    camera_id: str
    pic_id: str
    timestamp: str