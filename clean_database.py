from pymilvus import (
    connections,
    utility
)

connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

collections_to_delete = [
    "face_embeddings",
    "persons",
    "person_events"
]

for collection_name in collections_to_delete:

    if utility.has_collection(collection_name):

        utility.drop_collection(
            collection_name
        )

        print(
            f"{collection_name} Deleted"
        )

    else:

        print(
            f"{collection_name} Not Found"
        )

print("\nCleanup Complete")