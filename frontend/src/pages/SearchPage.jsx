import { useEffect, useRef, useState } from "react";
import axios from "axios";

export default function SearchPage() {
  const API_BASE = `http://${window.location.hostname}:8000`;
  const [images, setImages] = useState([]);
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showInvalid, setShowInvalid] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [invalidFaces, setInvalidFaces] = useState([]);
  const fileInputRef = useRef(null);
  

  const loadDashboard = async () => {
    try {
      
      const statsResponse =  await axios.get(`${API_BASE}/stats`);
      setStats(statsResponse.data);

      const eventsResponse = await axios.get(`${API_BASE}/events`);
      setEvents(eventsResponse.data);
    } catch (error) {
      console.error("Dashboard load failed:", error);
    }
  };

  useEffect(() => {
    loadDashboard();

    const eventSource = new EventSource(`${API_BASE}/events/stream`);

    eventSource.addEventListener("new_event", (event) => {
      const data = JSON.parse(event.data);

      // Prepend the incoming SSE event — no need to re-fetch /events
      setEvents((prev) => [data, ...prev].slice(0, 20));

      // Only refresh stats counter
      axios
        .get(`${API_BASE}/stats`)
        .then((res) => setStats(res.data))
        .catch(() => {});
    });

    return () => {
      eventSource.close();
    };
  }, []);

  const searchPerson = async () => {
    if (images.length === 0) return;

    try {
      setLoading(true);
      setResult(null);

      const formData = new FormData();
      images.forEach((file) => {
        formData.append("images", file);
      });

      const response = await axios.post(`${API_BASE}/search/multiple`, formData);

      setResult(response.data);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadInvalidFaces = async () => {
    try {
      const response = await axios.get(`${API_BASE}/invalid-faces`);
      setInvalidFaces(response.data);
    } catch (error) {
      console.error("Invalid faces load failed:", error);
    }
  };

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files);
    if (selected.length > 0) setImages((prev) => [...prev, ...selected]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const dropped = Array.from(e.dataTransfer.files).filter((f) =>
      f.type.startsWith("image/")
    );
    if (dropped.length > 0) setImages((prev) => [...prev, ...dropped]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  const removeImage = (index) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
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
              events.map((event, index) => (
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
              ))
            )}
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div>

          {/* UPLOAD CARD */}
          <div
            style={{
              background: dragActive ? "#b8b8b8" : "rgb(193 193 193)",
              border: dragActive ? "2px dashed #555" : "1px solid #aaaaaa",
              padding: "15px",
              transition: "border 0.15s, background 0.15s",
            }}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <h3 style={{ marginTop: 0 }}>Search Person</h3>

            <div
              style={{
                border: "2px dashed #999",
                padding: "20px",
                textAlign: "center",
                color: "#555",
                marginBottom: "12px",
                cursor: "pointer",
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              {dragActive
                ? "Drop images here…"
                : "Drag & drop images here, or click to select"}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              style={{ display: "none" }}
              onChange={handleFileChange}
            />

            <div style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
              <button
                onClick={() => fileInputRef.current?.click()}
                style={{ flex: 1 }}
              >
                Choose Files
              </button>
              <button
                onClick={() => {
                  setImages([]);
                  setResult(null);
                }}
                style={{ flex: 1 }}
                disabled={images.length === 0}
              >
                Clear
              </button>
            </div>

            <button
              onClick={searchPerson}
              disabled={loading || images.length === 0}
              style={{ width: "100%" }}
            >
              {loading ? "Searching…" : `Search (${images.length} image${images.length !== 1 ? "s" : ""})`}
            </button>
          </div>

          {/* UPLOADED IMAGES PREVIEW */}
          {images.length > 0 && (
            <div style={cardStyle}>
              <h3 style={{ marginTop: 0 }}>
                Uploaded Images ({images.length})
              </h3>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                {images.map((file, index) => (
                  <div key={index} style={{ position: "relative" }}>
                    <img
                      src={URL.createObjectURL(file)}
                      alt=""
                      style={{
                        width: "140px",
                        height: "140px",
                        objectFit: "cover",
                        border: "1px solid #999",
                        display: "block",
                      }}
                    />
                    <button
                      onClick={() => removeImage(index)}
                      style={{
                        position: "absolute",
                        top: "2px",
                        right: "2px",
                        background: "rgba(0,0,0,0.55)",
                        color: "#fff",
                        border: "none",
                        cursor: "pointer",
                        fontSize: "12px",
                        lineHeight: 1,
                        padding: "2px 5px",
                      }}
                    >
                      ✕
                    </button>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "#444",
                        maxWidth: "140px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        marginTop: "2px",
                      }}
                    >
                      {file.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SEARCH RESULTS */}
          {result && (
            <div style={cardStyle}>
              <h3 style={{ marginTop: 0 }}>Search Results</h3>

              <p style={{ margin: "4px 0" }}>
                <b>Total Uploaded:</b> {result.total_uploaded}
              </p>
              <p style={{ margin: "4px 0" }}>
                <b>Valid Faces:</b> {result.valid_faces}
              </p>
              <p style={{ margin: "4px 0" }}>
                <b>Invalid Faces:</b> {result.invalid_faces}
              </p>
              <p style={{ margin: "4px 0" }}>
                <b>Unique People:</b> {result.unique_people}
              </p>

              <hr />

              {result.results?.map((cluster, index) => (
                <div
                  key={index}
                  style={{
                    border: "1px solid #999",
                    padding: "15px",
                    marginBottom: "20px",
                    background: "#e5e5e5",
                  }}
                >
                  <h4 style={{ marginTop: 0 }}>Cluster {cluster.cluster_id}</h4>

                  {cluster.representative_image && (
                    <p style={{ margin: "4px 0" }}>
                      <b>Representative Image:</b> {cluster.representative_image}
                    </p>
                  )}

                  {cluster.uploaded_images?.length > 0 && (
                    <>
                      <p style={{ margin: "4px 0" }}>
                        <b>Uploaded Images:</b>
                      </p>
                      <ul style={{ margin: "4px 0 8px 0", paddingLeft: "20px" }}>
                        {cluster.uploaded_images.map((img, i) => (
                          <li key={i} style={{ fontSize: "13px" }}>
                            {img}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  <p style={{ margin: "4px 0" }}>
                    <b>Matched:</b>{" "}
                    <span
                      style={{
                        color: cluster.matched ? "#1a6e1a" : "#a00",
                        fontWeight: "bold",
                      }}
                    >
                      {cluster.matched ? "Yes" : "No"}
                    </span>
                  </p>

                  {cluster.matched ? (
                    <>
                      <p style={{ margin: "4px 0" }}>
                        <b>Person ID:</b> {String(cluster.person_id)}
                      </p>
                      <p style={{ margin: "4px 0" }}>
                        <b>Match Score:</b>{" "}
                        {typeof cluster.match_score === "number"
                          ? cluster.match_score.toFixed(4)
                          : cluster.match_score}
                      </p>
                      <p style={{ margin: "4px 0" }}>
                        <b>Total Events:</b> {cluster.total_events}
                      </p>

                      {cluster.events?.length > 0 && (
                        <>
                          <h4 style={{ marginBottom: "8px" }}>Timeline</h4>
                          {cluster.events.map((event, idx) => (
                            <div
                              key={idx}
                              style={{
                                display: "flex",
                                gap: "15px",
                                marginBottom: "15px",
                                borderBottom: "1px solid #ccc",
                                paddingBottom: "10px",
                              }}
                            >
                              <img
                                src={event.image_url}
                                alt=""
                                style={{
                                  width: "120px",
                                  height: "120px",
                                  objectFit: "cover",
                                  border: "1px solid #999",
                                  flexShrink: 0,
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
                        </>
                      )}
                    </>
                  ) : (
                    <p style={{ margin: "4px 0", color: "#777", fontStyle: "italic" }}>
                      {cluster.message || "Person not found in database."}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}