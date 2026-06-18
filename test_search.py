from services.search_service import SearchService

search = SearchService()

result = search.search_person(
    "saved_faces/IMG_20260606_160545.jpg"
)

print(result)