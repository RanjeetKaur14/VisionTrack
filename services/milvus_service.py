from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)

import os


class MilvusService:

    def __init__(self):

        connections.connect(
            alias="default",
            host=os.getenv(
                "MILVUS_HOST",
                "localhost"
            ),
            port=os.getenv(
                "MILVUS_PORT",
                "19530"
            )
        )

        self.person_collection_name = "persons"
        self.event_collection_name = "person_events"

        self.create_person_collection()
        self.create_event_collection()

    # ==================================================
    # PERSON COLLECTION
    # ==================================================

    def create_person_collection(self):

        if utility.has_collection(
            self.person_collection_name
        ):

            collection = Collection(
                self.person_collection_name
            )

            if not collection.indexes:

                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }

                collection.create_index(
                    field_name="embedding",
                    index_params=index_params
                )

            collection.load()

            print(
                "Persons Collection Exists"
            )

            return

        fields = [

            FieldSchema(
                name="person_id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),

            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=512
            )

        ]

        schema = CollectionSchema(
            fields=fields,
            description="Known Persons"
        )

        collection = Collection(
            name=self.person_collection_name,
            schema=schema
        )

        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }

        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        collection.load()

        print(
            "Persons Collection Created"
        )

    # ==================================================
    # EVENT COLLECTION
    # ==================================================

    def create_event_collection(self):

        if utility.has_collection(
            self.event_collection_name
        ):

            collection = Collection(
                self.event_collection_name
            )

            if not collection.indexes:

                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }

                collection.create_index(
                    field_name="embedding",
                    index_params=index_params
                )

            collection.load()

            print(
                "Events Collection Exists"
            )

            return

        fields = [

            FieldSchema(
                name="event_id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),

            FieldSchema(
                name="person_id",
                dtype=DataType.INT64
            ),

            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=512
            ),

            FieldSchema(
                name="store_id",
                dtype=DataType.VARCHAR,
                max_length=100
            ),

            FieldSchema(
                name="camera_id",
                dtype=DataType.VARCHAR,
                max_length=100
            ),

            FieldSchema(
                name="pic_id",
                dtype=DataType.VARCHAR,
                max_length=255
            ),

            FieldSchema(
                name="timestamp",
                dtype=DataType.VARCHAR,
                max_length=100
            ),

            FieldSchema(
                name="image_path",
                dtype=DataType.VARCHAR,
                max_length=500
            )

        ]

        schema = CollectionSchema(
            fields=fields,
            description="Person Detection Events"
        )

        collection = Collection(
            name=self.event_collection_name,
            schema=schema
        )

        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }

        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        collection.load()

        print(
            "Events Collection Created"
        )

    # ==================================================
    # PERSON METHODS
    # ==================================================

    def insert_person(self, embedding):

        collection = Collection(
            self.person_collection_name
        )

        data = [
            embedding.tolist()
        ]

        result = collection.insert([data])

        collection.flush()

        return result.primary_keys[0]

    def search_person(self, embedding):

        collection = Collection(
            self.person_collection_name
        )

        # collection.load()

        results = collection.search(
            data=[embedding.tolist()],
            anns_field="embedding",
            param={
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            },
            limit=5
        )

        return results

    # ==================================================
    # EVENT METHODS
    # ==================================================

    def insert_event(
        self,
        person_id,
        embedding,
        store_id,
        camera_id,
        pic_id,
        timestamp,
        image_path
    ):

        collection = Collection(
            self.event_collection_name
        )

        data = [
            [person_id],
            [embedding],
            [store_id],
            [camera_id],
            [pic_id],
            [timestamp],
            [image_path]
        ]
        print("\n=== INSERT EVENT ===")
        print("PERSON ID:", person_id)
        print("PIC ID:", pic_id)
        print("TIMESTAMP:", timestamp)
        print("====================\n")

        collection.insert(data)

        # collection.flush()

    def search_events_by_person(
        self,
        person_id
    ):

        collection = Collection(
            self.event_collection_name
        )

        # collection.load()

        results = collection.query(
            expr=f"person_id == {person_id}",
            output_fields=[
                "person_id",
                "store_id",
                "camera_id",
                "pic_id",
                "timestamp",
                "image_path"
            ]
        )

        return results

    # ==================================================
    # COUNTS
    # ==================================================

    def get_count(self):

        collection = Collection(
            self.person_collection_name
        )

        return collection.num_entities

    def get_event_count(self):

        collection = Collection(
            self.event_collection_name
        )

        return collection.num_entities