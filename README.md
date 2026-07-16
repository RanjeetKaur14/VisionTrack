<div align="center">

# VisionTrack

### Real-Time Face Analytics Platform

A modular face recognition system built around vector similarity search, event-driven processing, and real-time identity analytics.

</div>

---

## Table of Contents

- Overview
- Problem Statement
- Solution
- Core Capabilities
- Technology Stack
- System Architecture
- Recognition Pipeline
- Project Structure
- Getting Started
- Future Work

---

# Overview

VisionTrack is a real-time face analytics platform designed for continuous identity recognition from live camera streams.

The system combines face detection, deep facial embeddings, vector similarity search, event streaming, and searchable recognition history into a single modular pipeline. Unlike traditional face recognition applications that operate on isolated images, VisionTrack models recognition as a continuous stream of events, allowing identities to be searched, tracked, and analyzed over time.

Built around a service-oriented architecture, the platform integrates YOLOv8 Face for detection, InsightFace ArcFace for facial embeddings, Milvus for vector similarity search, Apache Kafka for asynchronous event streaming, FastAPI for backend services, and React for visualization. Each subsystem is designed to operate independently, making the platform scalable, maintainable, and easy to extend.

---

# Problem Statement

Conventional surveillance systems are largely passive. Although they continuously record video, they provide limited insight into who appears, when they appeared, or where they were previously observed.

Most face recognition projects focus on recognizing a single image and returning a predicted identity. Such approaches are insufficient for real-world deployments where recognition must operate continuously across live camera feeds while maintaining searchable identity history and minimizing duplicate detections.

A practical face recognition platform should be capable of:

- Continuously processing live video streams.
- Persistently managing recognized identities.
- Reducing redundant recognition caused by consecutive frames.
- Maintaining searchable detection history.
- Supporting multiple cameras and deployment locations.
- Performing low-latency similarity search.
- Decoupling recognition from storage and downstream processing.

VisionTrack addresses these challenges through a modular, event-driven architecture centered around vector similarity search.

---

# Solution

VisionTrack transforms a live camera feed into a searchable stream of recognition events.

Each detected face is first validated to reject low-quality samples before generating a deep facial embedding using ArcFace. The embedding is then compared against previously enrolled identities stored within Milvus using cosine similarity. Based on configurable recognition thresholds, the system either associates the face with an existing identity or creates a new person record.

Recognition events are published asynchronously through Apache Kafka, allowing downstream services to process and persist event history independently of the recognition pipeline. A lightweight in-memory presence cache further reduces unnecessary database lookups by identifying recently observed individuals and suppressing duplicate recognition events across consecutive frames.

The platform exposes search and analytics services through FastAPI, enabling users to retrieve recognition history, search for individuals using one or more images, and monitor recognition events through a web dashboard.

---

# Core Capabilities

- **Real-Time Face Detection**  
  Detects faces from live camera feeds using a YOLOv8 Face detector optimized for fast inference and accurate localization.

- **Deep Face Recognition**  
  Generates normalized 512-dimensional facial embeddings using InsightFace ArcFace for robust identity matching across varying poses and lighting conditions.

- **Vector Similarity Search**  
  Stores facial embeddings in Milvus and performs approximate nearest-neighbor search using cosine similarity for low-latency recognition.

- **Event-Driven Architecture**  
  Streams recognition events through Apache Kafka, allowing recognition, storage, and search services to remain loosely coupled.

- **Presence Management**  
  Maintains an in-memory presence cache to prevent redundant recognition events and reduce unnecessary database operations.

- **Recognition History**  
  Persists every confirmed recognition event with associated metadata, including timestamp, camera identifier, image reference, and person identifier.

- **Image-Based Search**  
  Supports both single-image and multi-image search. Uploaded images are clustered before querying the vector database, improving search robustness when multiple images belong to the same individual.

- **REST API**  
  Exposes endpoints for identity search, event history, statistics, and live event streaming through FastAPI.

- **Modular Design**  
  Separates detection, recognition, storage, messaging, and search into independent services, simplifying maintenance and future extensions.
