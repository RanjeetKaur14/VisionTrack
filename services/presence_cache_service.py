from datetime import datetime, timedelta
import numpy as np

from services.config_service import ConfigService


class PresenceCacheService:

    def __init__(self):

        self.cache = {}

        self.config = ConfigService.load()

        self.presence_event_seconds = (
            self.config["presence"]
            ["presence_event_seconds"]
        )

    def is_present(self, person_id):

        return person_id in self.cache

    def update_person(self, person_id, embedding):

        now = datetime.now()

        if person_id not in self.cache:

            self.cache[person_id] = {
                "embedding": embedding,
                "first_seen": now,
                "last_seen": now,
                "last_presence_event": now
            }

            return "ENTERED"

        self.cache[person_id]["embedding"] = embedding
        self.cache[person_id]["last_seen"] = now

        time_since_presence_event = (
            now
            -
            self.cache[person_id][
                "last_presence_event"
            ]
        ).total_seconds()

        if (
            time_since_presence_event
            >=
            self.presence_event_seconds
        ):

            self.cache[person_id][
                "last_presence_event"
            ] = now

            return "PRESENT"

        return "INSIDE"

    def remove_expired_people(self, timeout_seconds):

        now = datetime.now()

        expired_people = []

        for person_id, data in self.cache.items():

            if now - data["last_seen"] > timedelta(
                seconds=timeout_seconds
            ):

                expired_people.append(person_id)

        for person_id in expired_people:

            print(f"LEFT: {person_id}")

            del self.cache[person_id]

    def get_cache(self):

        return self.cache

    def find_cached_person(
        self,
        embedding,
        threshold=0.60
    ):

        if embedding is None:
            return None

        print("FIND CACHED PERSON CALLED")
        print("Current Cache Keys:", self.cache.keys())

        best_person = None
        best_score = -1

        for person_id, data in self.cache.items():

            cached_embedding = data["embedding"]

            score = np.dot(
                embedding,
                cached_embedding
            )

            print("Comparing With:", person_id)
            print("Similarity:", score)

            if score > best_score:

                best_score = score
                best_person = person_id

        print("Best Person:", best_person)
        print("Best Score:", best_score)
        print("Threshold:", threshold)

        if best_score >= threshold:

            print("CACHE MATCH FOUND")

            return best_person

        print("CACHE MISS")

        return None