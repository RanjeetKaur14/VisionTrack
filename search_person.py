import json

from services.search_service import (
    SearchService
)

service = SearchService()

print("\n=== PERSON SEARCH ===")

image_path = input(
    "Enter image path: "
)

result = service.search_person(
    image_path
)

print("\n=== SEARCH RESULT ===")

print(
    json.dumps(
        result,
        indent=4
    )
)