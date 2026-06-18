from fastapi import FastAPI, UploadFile, File
from services.search_service import SearchService
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import asyncio

import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

search_service = SearchService()

os.makedirs("invalid_faces", exist_ok=True)
os.makedirs("temp_search",   exist_ok=True)
os.makedirs("saved_faces",   exist_ok=True)

# Shared thread pool — reused across all requests
_executor = ThreadPoolExecutor(max_workers=4)

# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

MAX_SAFE_INT = 2 ** 53 - 1

def _coerce_id(value: int) -> "str | int":
    """
    Milvus AUTO_ID values are INT64 Snowflake IDs that exceed
    JavaScript's Number.MAX_SAFE_INTEGER (2^53 - 1).
    Return as string so JSON.parse() in the browser doesn't lose precision.
    """
    return str(value) if isinstance(value, int) and abs(value) > MAX_SAFE_INT else value


def _coerce_event(event: dict) -> dict:
    """Coerce all large INT64 ID fields in one event dict."""
    for field in ("event_id", "person_id"):
        if field in event:
            event[field] = _coerce_id(event[field])
    return event


def _build_image_url(image_path: str, base: str) -> str:
    filename = image_path.split("/")[-1]
    return f"http://127.0.0.1:8000/{base}/{filename}"


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.post("/search")
async def search_person(
    image: UploadFile = File(...)
):
    """
    Save the uploaded image to disk, then run face search in a
    background thread so the async event loop is never blocked.
    """
    image_path = os.path.join("temp_search", image.filename)

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Offload the CPU-bound search to the thread pool
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        search_service.search_person,
        image_path
    )

    # Coerce IDs regardless of whether result is a list or a single dict
    if isinstance(result, list):
        result = [_coerce_event(r) for r in result]
    elif isinstance(result, dict):
        result = _coerce_event(result)

    return result


@app.get("/stats")
def get_stats():
    """
    Fire both Milvus count queries in parallel — they're independent
    and each involves a network round-trip.
    """
    future_persons = _executor.submit(
        search_service.milvus_service.get_count
    )
    future_events = _executor.submit(
        search_service.milvus_service.get_event_count
    )

    return {
        "total_persons": future_persons.result(),
        "total_events":  future_events.result(),
    }


@app.get("/events")
def get_events():
    from pymilvus import Collection

    collection_name = (
        search_service
        .milvus_service
        .event_collection_name
    )

    c = Collection(collection_name)

    events = c.query(
        expr="person_id >= 0",
        output_fields=[
            "person_id",
            "camera_id",
            "store_id",
            "timestamp",
            "image_path",
            "event_id",
        ]
    )

    events.sort(
        key=lambda x: x["timestamp"],
        reverse=True
    )

    events = events[:20]

    # Build image URLs in parallel — each is a pure string op so this
    # is more illustrative than necessary, but scales if you add I/O later
    def _enrich(event: dict) -> dict:
        _coerce_event(event)
        event["image_url"] = _build_image_url(
            event["image_path"],
            "saved_faces"
        )
        return event

    events = list(_executor.map(_enrich, events))

    return events


@app.get("/invalid-faces")
def get_invalid_faces():
    """
    List directory entries in parallel so the pattern is consistent
    and ready if you later add stat/metadata calls per file.
    """
    filenames = os.listdir("invalid_faces")

    def _make_entry(filename: str) -> dict:
        return {
            "image_url": f"http://127.0.0.1:8000/invalid_faces/{filename}"
        }

    return list(_executor.map(_make_entry, filenames))

@app.get("/events/stream")
async def stream_events():

    async def event_generator():

        from pymilvus import Collection

        last_event_id = None

        while True:

            collection_name = (
                search_service
                .milvus_service
                .event_collection_name
            )

            c = Collection(collection_name)

            events = c.query(
                expr="person_id >= 0",
                output_fields=[
                    "event_id",
                    "person_id",
                    "camera_id",
                    "store_id",
                    "timestamp",
                    "image_path"
                ]
            )

            if events:

                events.sort(
                    key=lambda x: x["timestamp"],
                    reverse=True
                )

                latest = events[0]

                if latest["event_id"] != last_event_id:

                    last_event_id = latest["event_id"]

                    latest["image_url"] = (
                        f"http://127.0.0.1:8000/"
                        f"saved_faces/"
                        f"{latest['image_path'].split('/')[-1]}"
                    )

                    yield {
                        "event": "new_event",
                        "data": json.dumps(latest)
                    }

            await asyncio.sleep(0.25)

    return EventSourceResponse(
        event_generator()
    )
# ─────────────────────────────────────────
# Static mounts  (must come after routes)
# ─────────────────────────────────────────

app.mount(
    "/saved_faces",
    StaticFiles(directory="saved_faces"),
    name="saved_faces",
)
app.mount(
    "/invalid_faces",
    StaticFiles(directory="invalid_faces"),
    name="invalid_faces",
)