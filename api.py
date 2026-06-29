from fastapi import FastAPI, UploadFile, File
from services.search_service import SearchService
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import asyncio

import json
import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.5.231:5173",
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
    return f"http://192.168.5.231:8000/{base}/{filename}"

def _save_uploaded_images(images):

    image_paths = []

    for image in images:

        # Preserve original extension
        extension = os.path.splitext(
            image.filename
        )[1]

        # Generate unique filename
        filename = (
            f"{uuid.uuid4()}{extension}"
        )

        image_path = os.path.join(
            "temp_search",
            filename
        )

        with open(
            image_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                image.file,
                buffer
            )

        image_paths.append(
            image_path
        )

    return image_paths
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
    image_path = _save_uploaded_images(
        [image]
    )[0]

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


@app.post("/search/multiple")
async def search_multiple_people(

    images: list[UploadFile] = File(...)

):

    image_paths = _save_uploaded_images(
        images
    )
    # ---------------------------------------
    # Run search in thread pool
    # ---------------------------------------

    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(

        _executor,

        search_service.search_multiple,

        image_paths

    )

    # ---------------------------------------
    # Convert large IDs to strings
    # ---------------------------------------

    if (

        result.get("success")

        and

        "results" in result

    ):

        for cluster in result["results"]:

            if (

                cluster.get("matched")

                and

                "person_id" in cluster

            ):

                cluster["person_id"] = _coerce_id(

                    cluster["person_id"]

                )

                if "events" in cluster:

                    cluster["events"] = [

                        _coerce_event(event)

                        for event in cluster["events"]

                    ]

    return result

@app.get("/stats")
def get_stats():

    try:

        future_persons = _executor.submit(
            search_service.milvus_service.get_count
        )

        future_events = _executor.submit(
            search_service.milvus_service.get_event_count
        )

        return {
            "total_persons": future_persons.result(),
            "total_events": future_events.result()
        }

    except Exception as e:

        print(
            "STATS ERROR:",
            str(e)
        )

        return {
            "total_persons": 0,
            "total_events": 0
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
            "image_url": f"http://192.168.5.231:8000/invalid_faces/{filename}"
        }

    return list(_executor.map(_make_entry, filenames))

@app.get("/events/stream")
async def stream_events():

    async def event_generator():

        from pymilvus import Collection

        last_event_id = None

        while True:

            try:

                collection_name = (
                    search_service
                    .milvus_service
                    .event_collection_name
                )

                c = Collection(collection_name)

                # ensure collection is loaded
                c.load()

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
                        key=lambda x: x.get("timestamp", ""),
                        reverse=True
                    )

                    latest = events[0]

                    current_event_id = latest.get("event_id")

                    if current_event_id != last_event_id:

                        last_event_id = current_event_id

                        filename = os.path.basename(
                            latest.get(
                                "image_path",
                                ""
                            )
                        )

                        latest["image_url"] = (
                            f"http://192.168.5.231:8000/"
                            f"saved_faces/"
                            f"{filename}"
                        )

                        latest = _coerce_event(latest)

                        yield {
                            "event": "new_event",
                            "data": json.dumps(latest)
                        }

            except Exception as e:

                print(
                    "STREAM ERROR:",
                    str(e)
                )

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