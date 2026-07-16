<div align="center">

# VisionTrack -FaceRecognition_with_Tracking

<a href="#"><img src="https://img.shields.io/badge/status-completed-success?style=flat-square"></a>

<a href="#"><img src="https://img.shields.io/badge/AI-Computer%20Vision-2563eb?style=flat-square"></a>
<a href="#"><img src="https://img.shields.io/badge/database-Milvus-0f766e?style=flat-square"></a>
<a href="#"><img src="https://img.shields.io/badge/messaging-Kafka-f97316?style=flat-square"></a>

**Detect. Recognize. Track. Search.**

*A scalable real-time face recognition pipeline built using deep learning, vector search, and event-driven architecture.*

</div>

---

# Table of Contents

- What it is
- Problem Statement
- Solution
- Features
- Tech Stack
- Pipeline
- Architecture
- Project Structure
- Getting Started
- Future Scope

---

# What it is

FaceRecognition_with_Tracking is a real-time face recognition and tracking system designed for intelligent surveillance applications.

The system detects faces from live camera feeds, generates deep facial embeddings, identifies individuals using vector similarity search, and streams recognition events through an event-driven pipeline for real-time analytics and search.

Instead of treating recognition as a standalone task, the project builds a complete recognition ecosystem combining computer vision, vector databases, distributed messaging, and REST APIs into one scalable pipeline.

---

# Problem Statement

Traditional surveillance systems primarily record video without understanding who appears across different cameras or when they were last seen.

Many face recognition projects stop after predicting an identity for a single image.

Real-world deployments require significantly more:

- Continuous recognition
- Low-latency search
- Persistent identity storage
- Multi-camera support
- Scalable event processing
- Searchable recognition history

This project addresses these challenges through an event-driven architecture centered around vector similarity search.

---

# Solution

The pipeline performs the following operations in real time:

- Detect faces from live video
- Extract facial embeddings using ArcFace
- Search identities inside Milvus Vector Database
- Create new identities when no match exists
- Publish recognition events using Kafka
- Persist recognition history
- Expose search APIs through FastAPI
- Display results through a web dashboard

The architecture separates detection, recognition, storage, and event streaming into independent services, making the system modular and scalable.

---

# Features

- Real-time face detection
- ArcFace embedding generation
- Vector similarity search using Milvus
- Identity management
- Event-driven architecture using Kafka
- Recognition history
- FastAPI search service
- Multi-camera ready architecture
- Embedding normalization
- Configurable recognition thresholds
- Modular service-based design

---

# Tech Stack

| Component | Technology |
|------------|------------|
| Language | Python |
| Face Detection | YOLOv8 Face |
| Face Recognition | InsightFace (ArcFace) |
| Vector Database | Milvus |
| Event Streaming | Apache Kafka |
| API | FastAPI |
| Image Processing | OpenCV |
| Deep Learning | ONNX Runtime |
| Serialization | JSON |
| Dashboard | React |

---

# Pipeline

```
Camera Feed
      │
      ▼
YOLO Face Detection
      │
      ▼
Face Cropping
      │
      ▼
ArcFace Embedding Generation
      │
      ▼
Embedding Normalization
      │
      ▼
Milvus Vector Search
      │
      ▼
Known Person?
 ┌──────────────┐
 │              │
Yes            No
 │              │
 ▼              ▼
Existing ID   Create Person
 │              │
 └──────┬───────┘
        ▼
Recognition Event
        ▼
Kafka Producer
        ▼
Kafka Consumer
        ▼
Event Storage
        ▼
FastAPI Search API
        ▼
React Dashboard
```

---

# Architecture

The project follows a modular service-oriented architecture.

```
Camera
   │
   ▼
Camera Service
   │
   ▼
Face Detection
   │
   ▼
Face Recognition Service
   │
   ▼
Milvus Service
   │
   ▼
Detection Event Producer
   │
   ▼
Kafka
   │
   ▼
Detection History Consumer
   │
   ▼
Search API
   │
   ▼
Dashboard
```

Each component has a single responsibility, allowing individual modules to be replaced or extended without affecting the overall pipeline.

---

# Project Structure

```
FaceRecognition_with_Tracking/

├── camera_service.py
├── camera_thread_service.py
├── face_recognition_service.py
├── FaceProcessor.py
├── recognition_worker.py
├── kafka_producer_service.py
├── detection_event_producer.py
├── detection_history_consumer.py
├── milvus_service.py
├── config_service.py
├── main.py
└── README.md
```

---

# Getting Started

Clone the repository

```bash
git clone https://github.com/<username>/FaceRecognition_with_Tracking.git

cd FaceRecognition_with_Tracking
```

Install dependencies

```bash
pip install -r requirements.txt
```

Start Kafka

```bash
docker compose up
```

Start Milvus

```bash
docker compose up
```

Run the application

```bash
python main.py
```

---

# Future Scope

- Distributed multi-camera deployment
- Face enrollment dashboard
- Temporal face tracking
- GPU inference optimization
- Face quality assessment
- Real-time alert system
- Person re-identification
- Edge deployment
- Cloud synchronization
- Analytics dashboard

---

<div align="center">

### Built with Computer Vision, Deep Learning and Distributed Systems.

</div>
