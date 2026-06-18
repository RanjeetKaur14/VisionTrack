import json
import csv
import os
import time
from datetime import datetime

from services.face_recognition_service import FaceRecognitionService
from services.milvus_service import MilvusService
from services.presence_cache_service import PresenceCacheService
from services.config_service import ConfigService
from models.detection_event import DetectionEvent

from services.detection_event_serializer import (
    DetectionEventSerializer
)

from services.detection_event_producer import (
    DetectionEventProducer
)

from services.detection_deduplication_service import (
    DetectionDeduplicationService
)

LOGS_DIR = "logs"
PERFORMANCE_CSV = os.path.join(LOGS_DIR, "performance.csv")

CSV_HEADERS = [
    "log_time",
    "pic_id",
    "event_timestamp",
    "consumer_start",
    "kafka_delay",
    "embedding_time",
    "cache_time",
    "milvus_time",
    "insert_time",
    "kafka_publish_time",
    "total_pipeline_time",
]


def _ensure_logs_dir():
    """Create logs/ directory and CSV with headers if they don't exist."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(PERFORMANCE_CSV):
        with open(PERFORMANCE_CSV, "w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADERS)


def log_performance(
    pic_id,
    event_timestamp,
    consumer_start,
    kafka_delay,
    embedding_time,
    cache_time,
    milvus_time,
    insert_time,
    kafka_publish_time,
    total_pipeline_time,
):
    """Append one performance row to logs/performance.csv."""
    _ensure_logs_dir()
    row = [
        datetime.now().isoformat(timespec="milliseconds"),  # log_time
        pic_id,
        event_timestamp,
        consumer_start.isoformat(timespec="milliseconds"),
        f"{kafka_delay:.6f}",
        f"{embedding_time:.6f}",
        f"{cache_time:.6f}",
        f"{milvus_time:.6f}",
        f"{insert_time:.6f}",
        f"{kafka_publish_time:.6f}",
        f"{total_pipeline_time:.6f}",
    ]
    with open(PERFORMANCE_CSV, "a", newline="") as f:
        csv.writer(f).writerow(row)


class KafkaConsumerService:

    def __init__(self):

        self.face_service = FaceRecognitionService()
        self.milvus_service = MilvusService()
        self.presence_cache = PresenceCacheService()
        self.detection_producer = DetectionEventProducer()
        self.detection_dedup = (
            DetectionDeduplicationService()
        )
        self.config = ConfigService.load()

        # Ensure logs directory + CSV exist at startup
        _ensure_logs_dir()

        print(
            "Total Embeddings:",
            self.milvus_service.get_count()
        )

    def consume(self, event):
        total_start = time.time()
        consumer_start = datetime.now()

        # Performance accumulators (0 = not used in this path)
        embedding_time = 0.0
        cache_time = 0.0
        milvus_time = 0.0
        insert_time = 0.0
        kafka_publish_time = 0.0

        existing_threshold = (
            self.config["recognition"]
            ["existing_threshold"]
        )

        new_threshold = (
            self.config["recognition"]
            ["new_threshold"]
        )

        self.presence_cache.remove_expired_people(
            self.config["presence"]["timeout_seconds"]
        )

        event_data = json.loads(event)

        print("\n=== EVENT RECEIVED ===")
        print(event)

        # --- Kafka delay ---
        event_timestamp = event_data["timestamp"]
        # Support both numeric (Unix epoch) and ISO string timestamps
        if isinstance(event_timestamp, (int, float)):
            event_dt = datetime.fromtimestamp(event_timestamp)
        else:
            event_dt = datetime.fromisoformat(str(event_timestamp))
        kafka_delay = (consumer_start - event_dt).total_seconds()

        image_path = f"saved_faces/{event_data['pic_id']}.jpg"

        print("Image Path:", image_path)
        embedding_start = time.time()
        embedding = self.face_service.generate_embedding(
            image_path
        )
        embedding_time = time.time() - embedding_start
        print(
            f"EMBEDDING TIME: "
            f"{embedding_time:.3f}s"
        )
        if embedding is None:

            print("No Face Found")

            total_pipeline_time = time.time() - total_start
            log_performance(
                pic_id=event_data["pic_id"],
                event_timestamp=event_timestamp,
                consumer_start=consumer_start,
                kafka_delay=kafka_delay,
                embedding_time=embedding_time,
                cache_time=cache_time,
                milvus_time=milvus_time,
                insert_time=insert_time,
                kafka_publish_time=kafka_publish_time,
                total_pipeline_time=total_pipeline_time,
            )
            _print_performance_summary(
                kafka_delay, embedding_time, cache_time,
                milvus_time, insert_time, kafka_publish_time,
                total_pipeline_time,
            )
            return

        print("\nChecking Cache...")
        cache_start = time.time()
        cached_person = (
            self.presence_cache.find_cached_person(
                embedding
            )
        )
        cache_time = time.time() - cache_start

        print(
            f"CACHE SEARCH TIME: "
            f"{cache_time:.3f}s"
        )

        if cached_person is not None:

            print(
                "CACHE HIT:",
                cached_person
            )

            status = (
                self.presence_cache.update_person(
                    cached_person,
                    embedding
                )
            )
            if status == "PRESENT":

                detection_event = DetectionEvent(
                    person_id=cached_person,
                    embedding=embedding.tolist(),
                    store_id=event_data["store_id"],
                    camera_id=event_data["camera_id"],
                    pic_id=event_data["pic_id"],
                    timestamp=event_data["timestamp"],
                    image_path=image_path
                )

                serialized_detection_event = (
                    DetectionEventSerializer.serialize(
                        detection_event
                    )
                )

                self.detection_producer.publish_detection_event(
                    serialized_detection_event
                )

                print("PRESENCE EVENT STORED")

            print(
                "Presence Status:",
                status
            )

            total_pipeline_time = time.time() - total_start
            log_performance(
                pic_id=event_data["pic_id"],
                event_timestamp=event_timestamp,
                consumer_start=consumer_start,
                kafka_delay=kafka_delay,
                embedding_time=embedding_time,
                cache_time=cache_time,
                milvus_time=milvus_time,
                insert_time=insert_time,
                kafka_publish_time=kafka_publish_time,
                total_pipeline_time=total_pipeline_time,
            )
            _print_performance_summary(
                kafka_delay, embedding_time, cache_time,
                milvus_time, insert_time, kafka_publish_time,
                total_pipeline_time,
            )

            if status == "INSIDE":

                if os.path.exists(image_path):
                    os.remove(image_path)
                    print("Deleted duplicate image")
            return

        if embedding is None:
            print("No Face Found")
            return

        print("Embedding Generated")
        milvus_start = time.time()
        results = self.milvus_service.search_person(
            embedding
        )
        milvus_time = time.time() - milvus_start
        print(
            f"MILVUS SEARCH TIME: "
            f"{milvus_time:.3f}s"
        )

        print("Embedding Length:", len(embedding))
        print("Raw Results:", results)
        print("Number of result groups:", len(results))

        if len(results) == 0 or len(results[0]) == 0:

            print("No matches found in Milvus")
            insert_start = time.time()
            new_id = self.milvus_service.insert_person(
                embedding
            )
            insert_time = time.time() - insert_start
            print(
                f"INSERT PERSON TIME: "
                f"{insert_time:.3f}s"
            )

            detection_event = DetectionEvent(
                person_id=new_id,
                embedding=embedding.tolist(),
                store_id=event_data["store_id"],
                camera_id=event_data["camera_id"],
                pic_id=event_data["pic_id"],
                timestamp=event_data["timestamp"],
                image_path=image_path
            )

            serialized_detection_event = (
                DetectionEventSerializer.serialize(
                    detection_event
                )
            )

            publish_start = time.time()
            self.detection_producer.publish_detection_event(
                serialized_detection_event
            )
            kafka_publish_time = time.time() - publish_start

            self.presence_cache.update_person(
                new_id,
                embedding
            )

            print("Inserted New Person:", new_id)
            print("Detection Event Stored")

            print("\n=== CACHE ===")
            for person_id, data in self.presence_cache.get_cache().items():

                print(
                    f"Person={person_id}, "
                    f"First Seen={data['first_seen']}, "
                    f"Last Seen={data['last_seen']}"
                )

            total_pipeline_time = time.time() - total_start
            log_performance(
                pic_id=event_data["pic_id"],
                event_timestamp=event_timestamp,
                consumer_start=consumer_start,
                kafka_delay=kafka_delay,
                embedding_time=embedding_time,
                cache_time=cache_time,
                milvus_time=milvus_time,
                insert_time=insert_time,
                kafka_publish_time=kafka_publish_time,
                total_pipeline_time=total_pipeline_time,
            )
            _print_performance_summary(
                kafka_delay, embedding_time, cache_time,
                milvus_time, insert_time, kafka_publish_time,
                total_pipeline_time,
            )
            return

        best_match = results[0][0]

        print("Image:", event_data["pic_id"])
        print("Matched ID:", best_match.id)
        print("Distance:", best_match.distance)
        print("Score:", best_match.score)

        print("======================")

        print("\nTop Matches:")

        for hit in results[0]:

            print(
                f"ID={hit.id}, "
                f"Score={hit.distance}"
            )

        score = best_match.score

        print("\n=== DECISION ===")
        print(f"Best Score: {score:.4f}")

        if score >= existing_threshold:

            print("EXISTING PERSON")
            print("Matched Person:", best_match.id)

            detection_event = DetectionEvent(
                person_id=best_match.id,
                embedding=embedding.tolist(),
                store_id=event_data["store_id"],
                camera_id=event_data["camera_id"],
                pic_id=event_data["pic_id"],
                timestamp=event_data["timestamp"],
                image_path=image_path
            )

            serialized_detection_event = (
                DetectionEventSerializer.serialize(
                    detection_event
                )
            )

            if self.detection_dedup.should_store(
                best_match.id,
                event_data["camera_id"]
            ):

                publish_start = time.time()
                self.detection_producer.publish_detection_event(
                    serialized_detection_event
                )
                kafka_publish_time = time.time() - publish_start
                # print(serialized_detection_event)
                print(
                    "Detection Event Stored"
                )

            else:

                print(
                    "Detection Event Ignored"
                )

            status = self.presence_cache.update_person(
                best_match.id,
                embedding
            )

            print("Presence Status:", status)

            print("\n=== CACHE ===")
            for person_id, data in self.presence_cache.get_cache().items():

                print(
                    f"Person={person_id}, "
                    f"First Seen={data['first_seen']}, "
                    f"Last Seen={data['last_seen']}"
                )

            print("Presence Status:", status)

        elif score <= new_threshold:

            print("NEW PERSON")
            insert_start = time.time()
            new_id = self.milvus_service.insert_person(
                embedding
            )
            insert_time = time.time() - insert_start
            print(
                f"INSERT PERSON TIME: "
                f"{insert_time:.3f}s"
            )
            detection_event = DetectionEvent(
                person_id=new_id,
                embedding=embedding.tolist(),
                store_id=event_data["store_id"],
                camera_id=event_data["camera_id"],
                pic_id=event_data["pic_id"],
                timestamp=event_data["timestamp"],
                image_path=image_path
            )

            serialized_detection_event = (
                DetectionEventSerializer.serialize(
                    detection_event
                )
            )
            publish_start = time.time()
            self.detection_producer.publish_detection_event(
                serialized_detection_event
            )
            kafka_publish_time = time.time() - publish_start
            print(
                f"KAFKA PUBLISH TIME: "
                f"{kafka_publish_time:.3f}s"
            )

            self.presence_cache.update_person(
                new_id,
                embedding
            )

            print("Image:", event_data["pic_id"])
            print("Created Person:", new_id)

            print("Detection Event Stored")

        else:

            print("BORDERLINE MATCH")

            print(
                "Potential Existing Person:",
                best_match.id
            )

            print(
                "No new person created."
            )

        total_pipeline_time = time.time() - total_start
        print("================")
        print(
            f"TOTAL PIPELINE TIME: "
            f"{total_pipeline_time:.3f}s"
        )

        log_performance(
            pic_id=event_data["pic_id"],
            event_timestamp=event_timestamp,
            consumer_start=consumer_start,
            kafka_delay=kafka_delay,
            embedding_time=embedding_time,
            cache_time=cache_time,
            milvus_time=milvus_time,
            insert_time=insert_time,
            kafka_publish_time=kafka_publish_time,
            total_pipeline_time=total_pipeline_time,
        )
        _print_performance_summary(
            kafka_delay, embedding_time, cache_time,
            milvus_time, insert_time, kafka_publish_time,
            total_pipeline_time,
        )


def _print_performance_summary(
    kafka_delay,
    embedding_time,
    cache_time,
    milvus_time,
    insert_time,
    kafka_publish_time,
    total_pipeline_time,
):
    print("\n=== PERFORMANCE SUMMARY ===")
    print(f"Kafka Delay:   {kafka_delay:.3f}s")
    print(f"Embedding:     {embedding_time:.3f}s")
    print(f"Cache:         {cache_time:.3f}s")
    print(f"Milvus:        {milvus_time:.3f}s")
    print(f"Insert:        {insert_time:.3f}s")
    print(f"Kafka Publish: {kafka_publish_time:.3f}s")
    print(f"Total:         {total_pipeline_time:.3f}s")
    print("===========================")