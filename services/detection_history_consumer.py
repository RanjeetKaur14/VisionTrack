from kafka import KafkaConsumer
import json

from services.milvus_service import MilvusService


consumer = KafkaConsumer(
    "detection-events",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="latest",
    group_id="detection-history-group",
    enable_auto_commit=True
)

milvus_service = MilvusService()

print("Detection History Consumer Started...")


for message in consumer:
    print("MESSAGE RECEIVED")
    print(message.value)
    
    event = json.loads(
        message.value.decode("utf-8")
    )

    print(event)

    required_fields = [
        "person_id",
        "embedding",
        "store_id",
        "camera_id",
        "pic_id",
        "timestamp",
        "image_path"
    ]

    missing_fields = [

        field

        for field in required_fields

        if field not in event

    ]

    if missing_fields:

        print(
            "OLD EVENT SKIPPED:",
            missing_fields
        )

        continue


    print("\n=== RECEIVED EVENT ===")
    print(event)
    print("======================\n")
    milvus_service.insert_event(
        person_id=event["person_id"],
        embedding=event["embedding"],
        store_id=event["store_id"],
        camera_id=event["camera_id"],
        pic_id=event["pic_id"],
        timestamp=event["timestamp"],
        image_path=event["image_path"]
    )

    print(
        f"Detection Event Stored | "
        f"Person={event['person_id']} | "
        f"Camera={event['camera_id']}"
    )

    print(
        "Total Events:",
        milvus_service.get_event_count()
    )