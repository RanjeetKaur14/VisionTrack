from kafka import KafkaConsumer
import json
import os
import time

from services.milvus_service import MilvusService


def start_consumer():

    # Wait until Kafka becomes available
    while True:
        try:

            consumer = KafkaConsumer(
                "detection-events",
                bootstrap_servers=os.getenv(
                    "KAFKA_BOOTSTRAP_SERVERS",
                    "localhost:29092"
                ),
                auto_offset_reset="earliest",
                group_id="detection-history-group",
                enable_auto_commit=True,
                value_deserializer=lambda m: m.decode("utf-8")
                
            )

            print("Detection History Consumer Connected")
            break

        except Exception as e:

            print("Waiting for Kafka...")
            print(e)

            time.sleep(5)

    milvus_service = MilvusService()

    print("Detection History Consumer Started...")

    for message in consumer:

        try:

            event = json.loads(message.value)

        except Exception as e:

            print("BAD MESSAGE:")
            print(message.value)
            print(e)

            continue

        print("\n=== RECEIVED EVENT ===")
        print(event)
        print("======================\n")

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


if __name__ == "__main__":
    start_consumer()