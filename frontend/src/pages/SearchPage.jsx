import { useEffect, useState } from "react";
import axios from "axios";

export default function SearchPage() {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showInvalid, setShowInvalid] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [invalidFaces, setInvalidFaces] = useState([]);

  const loadDashboard = async () => {
    console.time("LOAD_DASHBOARD");
    try {
      console.time("STATS_API");
      const statsResponse = await axios.get("http://127.0.0.1:8000/stats");
      console.timeEnd("STATS_API");
      setStats(statsResponse.data);

      console.time("EVENTS_API");
      const eventsResponse = await axios.get(
        `http://127.0.0.1:8000/events?t=${Date.now()}`
      );
      console.timeEnd("EVENTS_API");
      console.log("RAW EVENTS RESPONSE", JSON.stringify(eventsResponse.data));
      setEvents(eventsResponse.data);
    } catch (error) {
      console.log(error);
    } finally {
      console.timeEnd("LOAD_DASHBOARD");
    }
  };

  useEffect(() => {

    loadDashboard();

    const eventSource =
      new EventSource(
        "http://127.0.0.1:8000/events/stream"
      );

    eventSource.addEventListener(
      "new_event",
      (event) => {
        console.log(
          "[SSE RECEIVED]",
          new Date().toISOString()
        );

        const data = JSON.parse(
          event.data
        );

        console.log(
          "EVENT TIMESTAMP:",
          data.timestamp
        );

        console.log(
          "PARSED:",
          new Date(data.timestamp)
        );

        console.log(
          "NOW:",
          new Date()
        );

        const displayDelay =
          Date.now() -
          new Date(data.timestamp).getTime();

        console.log(
          "[DISPLAY DELAY]",
          displayDelay,
          "ms"
        );

        setEvents(prev => [
          data,
          ...prev
        ].slice(0, 20));

        // Reload dashboard and log summary after both calls complete
        (async () => {
          console.time("STATS_API");
          const statsResponse = await axios.get("http://127.0.0.1:8000/stats").catch(() => null);
          const statsMs = statsResponse ? (() => { console.timeEnd("STATS_API"); return true; })() : (() => { console.timeEnd("STATS_API"); return false; })();

          console.time("EVENTS_API");
          const eventsResponse = await axios.get(
            `http://127.0.0.1:8000/events?t=${Date.now()}`
          ).catch(() => null);
          const eventsMs = eventsResponse ? (() => { console.timeEnd("EVENTS_API"); return true; })() : (() => { console.timeEnd("EVENTS_API"); return false; })();

          if (statsResponse) setStats(statsResponse.data);
          if (eventsResponse) setEvents(eventsResponse.data);

          console.log("=== FRONTEND PERFORMANCE ===");
          console.log("Display Delay:", displayDelay, "ms");
          console.log("Stats API:     (see STATS_API timer above)");
          console.log("Events API:    (see EVENTS_API timer above)");
          console.log("Dashboard Load:(see LOAD_DASHBOARD timer above)");
          console.log("SSE Arrived:  ", new Date().toISOString());
          console.log("===========================");
        })();
      }
    );

    return () => {
      eventSource.close();
    };

  }, []);

  const searchPerson = async () => {
    if (!image) return;
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append("image", image);
      const response = await axios.post(
        "http://127.0.0.1:8000/search",
        formData
      );
      setResult(response.data);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  const loadInvalidFaces = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/invalid-faces");
      setInvalidFaces(response.data);
    } catch (error) {
      console.log(error);
    }
  };

  const cardStyle = {
    marginTop: "40px",
    background: "rgb(193 193 193)",
    border: "1px solid #aaaaaa",
    padding: "15px",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#848181a3",
        padding: "20px",
        fontFamily: "Segoe UI",
      }}
    >
      {/* HEADER */}
      <div style={{ marginBottom: "8px" }}>
        <h1 style={{ margin: 0, color: "#222", fontSize: "28px" }}>
          Face Recognition & Tracking System
        </h1>
        {stats && (
          <p style={{ color: "#555", marginTop: "6px", marginBottom: "8px" }}>
            Persons: {stats.total_persons}
            {" | "}
            Events: {stats.total_events}
            {" | "}
            
          </p>
        )}
      </div>

      <hr />
      <br />

      {/* MAIN LAYOUT */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "20px",
        }}
      >
        {/* LEFT SIDE */}
        <div>
          <h3
            style={{
              marginTop: 0,
              marginBottom: "12px",
              fontSize: "22px",
              color: "#222",
            }}
          >
            <div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
              <button onClick={() => setShowInvalid(false)}>Valid Faces</button>
              <button
                onClick={() => {
                  setShowInvalid(true);
                  loadInvalidFaces();
                }}
              >
                Invalid Faces
              </button>
            </div>
            {showInvalid ? "Invalid Face Feed" : "Recent Detection Feed"}
          </h3>

          <div
            style={{
              background: "#d5d2d2c6",
              border: "1px solid #dedddd",
            }}
          >
            {showInvalid ? (
              invalidFaces.length === 0 ? (
                <div
                  style={{
                    padding: "20px",
                    color: "#666",
                    fontStyle: "italic",
                  }}
                >
                  No invalid faces found.
                </div>
              ) : (
                invalidFaces.map((face, index) => (
                  <div
                    key={index}
                    style={{
                      display: "flex",
                      gap: "18px",
                      padding: "10px",
                      alignItems: "center",
                      borderBottom: "1px solid #d4d4d4",
                    }}
                  >
                    <img
                      src={face.image_url}
                      alt=""
                      style={{
                        width: "140px",
                        height: "140px",
                        objectFit: "cover",
                        border: "1px solid #999",
                      }}
                    />
                    <div>
                      <p>
                        <b>Reason:</b> {face.reason || "Too Small Face"}
                      </p>
                      <p>
                        <b>Camera:</b> {face.camera_id || "CAM_01"}
                      </p>
                      <p>
                        <b>Time:</b>{" "}
                        {face.timestamp
                          ? new Date(face.timestamp).toLocaleString()
                          : "Unknown"}
                      </p>
                    </div>
                  </div>
                ))
              )
            ) : (
              events.map((event, index) => {
                // Start image load timer before the element renders
                console.time(`IMG_${event.event_id}`);
                return (
                  <div
                    key={`${event.event_id}-${event.image_path}`}
                    style={{
                      display: "flex",
                      gap: "18px",
                      padding: "10px",
                      alignItems: "center",
                      borderBottom: "1px solid #d4d4d4",
                    }}
                  >
                    <img
                      src={event.image_url}
                      alt=""
                      style={{
                        width: "140px",
                        height: "140px",
                        objectFit: "cover",
                        border: "1px solid #999",
                      }}
                      onLoad={() => {
                        console.timeEnd(`IMG_${event.event_id}`);
                        console.log(
                          "[IMAGE LOADED]",
                          event.image_path,
                          new Date().toISOString()
                        );
                      }}
                    />
                    <div>
                      <p style={{ margin: "3px 0" }}>
                        <b>Person:</b> {event.person_id}
                      </p>
                      <p style={{ margin: "3px 0" }}>
                        <b>Camera:</b> {event.camera_id}
                      </p>
                      <p style={{ margin: "3px 0" }}>
                        <b>Store:</b> {event.store_id}
                      </p>
                      <p style={{ margin: "3px 0", color: "#444", fontSize: "14px" }}>
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                      <p
                        style={{
                          margin: "3px 0",
                          fontSize: "12px",
                          color: "#777",
                          fontFamily: "Consolas",
                        }}
                      >
                        {event.image_path}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div>
          {/* SEARCH */}
          <div style={{ ...cardStyle, marginBottom: "15px" }}>
            <h2 style={{ marginTop: 0 }}>Search Person</h2>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragActive(false);
                if (e.dataTransfer.files[0]) {
                  setImage(e.dataTransfer.files[0]);
                }
              }}
              style={{
                border: dragActive ? "2px solid #444" : "2px dashed #777",
                padding: "25px",
                textAlign: "center",
                background: dragActive ? "#9f9f9f" : "#b7b7b7",
                marginBottom: "15px",
              }}
            >
              Drag & Drop Image
              <br />
              <span style={{ fontSize: "12px" }}>or choose file</span>
            </div>

            <input
              type="file"
              onChange={(e) => setImage(e.target.files[0])}
            />
            <br />
            <br />
            <button
              onClick={searchPerson}
              disabled={loading}
              style={{
                background: "#444",
                color: "white",
                border: "none",
                padding: "12px 25px",
                cursor: "pointer",
                fontWeight: "600",
              }}
            >
              {loading ? "Searching..." : "Search Person"}
            </button>
          </div>

          {/* UPLOADED IMAGE */}
          {image && (
            <div style={{ ...cardStyle, marginBottom: "15px" }}>
              <h3 style={{ marginTop: 0 }}>Uploaded Image</h3>
              <img
                src={URL.createObjectURL(image)}
                alt=""
                style={{
                  width: "140px",
                  height: "140px",
                  objectFit: "cover",
                  border: "1px solid #999",
                }}
              />
            </div>
          )}

          {/* SEARCH RESULT */}
          {result?.success === false ? (
            <div style={cardStyle}>
              <h3>Search Result</h3>
              <p>{result.message}</p>
            </div>
          ) : (
            result && (
              <div style={cardStyle}>
                <h3 style={{ marginTop: 0 }}>Search Result</h3>
                <p style={{ margin: "4px 0" }}>
                  <b>ID:</b> {result.person_id}
                </p>
                <p style={{ margin: "4px 0" }}>
                  <b>Score:</b> {result.match_score}
                </p>
                <p style={{ margin: "4px 0" }}>
                  <b>Events:</b> {result.total_events}
                </p>
                <hr />
                <h4>Timeline</h4>
                {result?.events?.map((event, index) => (
                  <div
                    key={index}
                    style={{
                      display: "flex",
                      gap: "15px",
                      alignItems: "center",
                      paddingBottom: "10px",
                      marginBottom: "15px",
                      borderBottom: "1px solid #ddd",
                    }}
                  >
                    <img
                      src={event.image_url}
                      alt=""
                      style={{
                        width: "140px",
                        height: "140px",
                        objectFit: "cover",
                        border: "1px solid #999",
                      }}
                    />
                    <div>
                      <p style={{ margin: "3px 0" }}>
                        <b>Camera:</b> {event.camera_id}
                      </p>
                      <p style={{ margin: "3px 0" }}>
                        <b>Store:</b> {event.store_id}
                      </p>
                      <p style={{ margin: "3px 0", color: "#444" }}>
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}