# Moya Backend

Backend service for **Moya**, an AI-powered accessible tourism platform designed to make travel planning more inclusive, personalized, and reliable.

Moya focuses on helping users discover tourist destinations based on their individual accessibility needs while also providing destination information, smart routing, environmental cleanliness monitoring, accessibility reviews, and community-driven contributions.

---

# Repositories

### Backend

https://github.com/lilChiie/Moya-Backend

### Web Frontend

https://github.com/lilChiie/Moya-Frontend-Web

### Mobile Frontend

https://github.com/lilChiie/Moya-Frontend-Mobile

---

## About Moya

We believe that everyone deserves the freedom to travel and explore without accessibility becoming a barrier.

Tourist destination information is widely available, but accessibility information is often difficult to find. For people with disabilities, knowing whether a destination provides wheelchair access, accessible toilets, suitable pathways, parking, and other supporting facilities can be just as important as knowing the destination itself.

Moya addresses this problem by putting **accessibility at the center of travel planning**.

Users can specify their accessibility needs and discover destinations that match those requirements. Moya then provides personalized recommendations and routes while also considering travel preferences such as budget, duration, distance, and destination cleanliness.

---

# Key Features

## 1. Accessible Tourism

Moya allows users to discover tourist destinations based on their accessibility requirements.

Accessibility information can include:

- Wheelchair accessibility
- Accessible toilets
- Accessible pathways
- Accessible parking
- Other supporting facilities

Users can select their accessibility needs and receive destinations that are relevant to them.

---

## 2. Smart Accessible Routing

Moya provides personalized destination recommendations using a Decision Support System (DSS).

The recommendation system considers multiple factors:

- Accessibility compatibility
- Budget
- Travel duration
- Distance
- Destination cleanliness

The system ranks destinations using the **Simple Additive Weighting (SAW)** method.

### DSS Criteria

| Criteria | Weight |
|---|---:|
| Accessibility | 20% |
| Budget | 25% |
| Duration | 20% |
| Distance | 25% |
| Cleanliness | 10% |
| **Total** | **100%** |

The highest-ranked destinations are selected to create the recommended itinerary.

---

## 3. Personalized Recommendation

Users can provide their travel preferences such as:

- Accessibility requirement
- Tourism category
- Budget
- Available travel duration
- Maximum travel distance
- Current location

Example request:

```json
{
    "user_id": 3,
    "accessibility_id": 8,
    "tourism_id": 3,
    "budget": 150000,
    "duration_minutes": 480,
    "max_distance_km": 50,
    "latitude": 1.136,
    "longitude": 104.029
}
```

The backend processes these preferences and calculates the suitability of available destinations.

---

# Recommendation Process

```text
User Preferences
       │
       ▼
Accessibility & Tourism Filter
       │
       ▼
Destination Candidates
       │
       ├── Accessibility
       ├── Budget
       ├── Duration
       ├── Distance
       └── Cleanliness
       │
       ▼
    DSS / SAW
       │
       ▼
Calculate Final Score
       │
       ▼
Rank Destinations
       │
       ▼
    TOP 5
       │
       ▼
Recommended Itinerary
```

Each destination receives a final score based on the weighted criteria.

---

# 4. AI-Powered Cleanliness Monitoring

Moya allows users to report environmental issues at tourist destinations.

When a user submits a report containing an image, the backend automatically processes the image using a fine-tuned **YOLO11** model.

The AI performs:

1. Image processing
2. Trash detection
3. Trash object counting
4. Bounding box generation
5. Severity score calculation

The result is stored as part of the cleanliness report.

### Processing Flow

```text
User Submits Report
        │
        ▼
     Image Upload
        │
        ▼
     YOLO11 Model
        │
        ├── Trash Detection
        ├── Object Counting
        └── Bounding Boxes
        │
        ▼
   Severity Score
        │
        ▼
   Save Report
        │
        ▼
Update Destination
Cleanliness Condition
```

---

# 5. Destination Cleanliness

Each tourist destination can receive multiple cleanliness reports.

The cleanliness score is calculated from the severity scores of reports associated with the destination.

For example:

```text
Report 1 → 0.10
Report 2 → 0.30
Report 3 → 0.20
```

Average severity:

```text
(0.10 + 0.30 + 0.20) / 3
= 0.20
```

Cleanliness score:

```text
1 - 0.20
= 0.80
```

A higher cleanliness score indicates a cleaner destination.

Because the score is calculated from the reports, a new report can change the destination's overall cleanliness condition automatically.

---

# 6. Cleanliness Status

Moya translates cleanliness conditions into an easy-to-understand status.

The destination can be classified as:

- **Safe**
- **Needs Attention**
- **Needs Treatment**

This allows users to quickly understand the current environmental condition of a destination.

For example:

```text
New Report
    │
    ▼
YOLO Detection
    │
    ▼
Severity Score
    │
    ▼
Average Destination Score
    │
    ▼
Cleanliness Status
```

The status can therefore change when additional reports are submitted.

---

# 7. Accessibility Reviews & Community Reports

Moya encourages users to contribute information about destinations.

Users can:

- Submit accessibility-related information
- Report environmental problems
- Add notes to reports
- Share their experiences
- Contribute information that can help other travelers

This creates a more community-driven and informative tourism platform.

---

# 8. Rewards & Contributions

Moya encourages users to actively contribute to the platform.

User contributions can support:

- Accessibility information
- Environmental reports
- Destination reviews
- Community participation

These contributions can be integrated with the platform's reward and leaderboard features.

---

# Technology Stack

### Backend

- Python
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended

### Database

- MySQL / MariaDB
- PyMySQL

### Artificial Intelligence

- Ultralytics YOLO11
- PyTorch
- OpenCV
- Google Gemini API

### Mapping & Location

- OpenStreetMap API
- Haversine distance calculation

---

# Requirements

Before running the backend, make sure you have:

- Python 3.12+
- pip
- MySQL / MariaDB
- Git
- Virtual Environment

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/lilChiie/Mavion-Backend.git

cd Mavion-Backend
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate the environment:

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=moya_db
DATABASE_USER=root
DATABASE_PASSWORD=

SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

GEMINI_API_KEY=your-gemini-api-key
```

Adjust the configuration according to your environment.

---

# Database Setup

Moya uses MySQL / MariaDB as its primary database.

Create the database:

```sql
CREATE DATABASE moya_db;
```

The database contains several entities including:

```text
users
tourism
accessibility
destinations
destination_tourisms
destination_accessibilities
reports
recom_requests
recom_results
itineraries
itinerary_items
notifications
```

Make sure the required database tables have been created before running the application.

---

# AI Model Setup

The YOLO model is not included directly in the repository because of its file size.

Download the model from:

```text
https://drive.google.com/drive/folders/1sJel7nqBHi5n2Tdm3ykBA3yArWow_Uj0?usp=drive_link
```

Place the model at:

```text
models/
└── yolo/
    └── best.pt
```

The final structure should be:

```text
Mavion-Backend/
│
└── models/
    └── yolo/
        └── best.pt
```

---

# YOLO Trash Severity

The trash severity score is calculated based on the number of detected trash objects.

| Detected Trash | Severity Score |
|---|---:|
| 0 - 3 | 0.10 |
| 4 - 6 | 0.30 |
| 7 - 9 | 0.50 |
| 10 - 12 | 0.70 |
| > 12 | 1.00 |

A higher severity score indicates a greater amount of detected trash.

---

# API

## Authentication

```text
POST /api/auth/register
POST /api/auth/login
```

---

## Tourism

```text
GET /api/tourism
GET /api/tourism/<id>
```

---

## Accessibility

```text
GET /api/accessibility
GET /api/accessibility/<id>
```

---

## Destinations

```text
GET /api/destinations
GET /api/destinations/<id>
```

---

## Reports

```text
GET    /api/reports
GET    /api/reports/<id>
POST   /api/reports
PUT    /api/reports/<id>
DELETE /api/reports/<id>
GET    /api/reports/trend
```

---

## Recommendation

```text
POST /api/recommendation
GET  /api/recommendation/<id>
```

---

## Ranking

```text
GET /api/ranks
```

---

## Leaderboard

```text
GET /api/leaderboard
```

---

## Profile

```text
GET /api/profile
PUT /api/profile
```

---

## Notifications

```text
GET /api/notifications
```

---

# Example: Create a Cleanliness Report

### Endpoint

```http
POST /api/reports
```

### Content-Type

```text
multipart/form-data
```

### Form Data

```text
user_id          = 3
destination_id   = 5
user_notes       = "There is a lot of plastic waste around this area."
image             = photo.jpg
```

The backend will automatically run YOLO detection on the uploaded image.

Example result:

```json
{
    "success": true,
    "message": "Report created successfully",
    "data": {
        "id": 15,
        "user_id": 3,
        "destination_id": 5,
        "detected_count": 7,
        "score": 0.5,
        "status": "pending"
    }
}
```

---

# Example: Generate Recommendation

### Endpoint

```http
POST /api/recommendation
```

### Request

```json
{
    "user_id": 3,
    "accessibility_id": 8,
    "tourism_id": 3,
    "budget": 150000,
    "duration_minutes": 480,
    "max_distance_km": 50,
    "latitude": 1.136,
    "longitude": 104.029
}
```

### Response

```json
{
    "success": true,
    "message": "Recommendation generated successfully",
    "data": {
        "request": {
            "id": 12,
            "user_id": 3,
            "accessibility_id": 8,
            "tourism_id": 3,
            "budget": 150000,
            "duration_minutes": 480,
            "max_distance_km": 50
        },
        "recommendations": [
            {
                "destination_id": 5,
                "destination_name": "Destination A",
                "rank": 1,
                "final_score": 0.8421,
                "accessibility_score": 1.0,
                "budget_score": 0.9,
                "duration_score": 0.75,
                "distance_score": 0.8,
                "cleanliness_score": 0.85,
                "distance_km": 12.4
            }
        ]
    }
}
```

---

# Running the Backend

Activate the virtual environment:

```bash
venv\Scripts\activate
```

Then run:

```bash
python app.py
```

The backend will run on:

```text
http://localhost:5000
```

---

# API Base URL

For local development:

```text
http://localhost:5000/api
```

For mobile testing, the backend can be exposed using a tunneling service such as ngrok.

Example:

```text
https://your-ngrok-url.ngrok-free.app
```

The Flutter application can then use the exposed URL as its API base URL.

---

# Development Flow

The main application flow is:

```text
User
 │
 ▼
Select Accessibility Needs
 │
 ▼
Select Tourism Preference
 │
 ▼
Set Budget, Duration & Distance
 │
 ▼
Moya Recommendation System
 │
 ▼
DSS / SAW Calculation
 │
 ▼
Top 5 Destinations
 │
 ▼
Accessible Itinerary
 │
 ▼
Explore Destination
 │
 ▼
Submit Accessibility / Cleanliness Report
 │
 ▼
YOLO Trash Detection
 │
 ▼
Destination Cleanliness Updated
```

---

# System Architecture

```text
                    Moya Mobile App
                           │
                           ▼
                    Flask REST API
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
        MySQL            YOLO11            DSS
          │                │                │
          │                ▼                ▼
          │         Trash Detection    SAW Ranking
          │                │                │
          │                ▼                ▼
          │         Severity Score     Recommendation
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                  Tourist Destinations
                           │
                           ▼
                    Moya User Experience
```

---

# Known Issues

- AI detection accuracy depends on image quality and environmental conditions.
- Very small, hidden, or partially occluded trash objects may not always be detected correctly.
- Recommendation results depend on the quality and availability of destination data.
- OpenStreetMap data availability may vary depending on location.
- AI inference requires computational resources.
- The current backend is primarily designed for development and hackathon demonstration.
- Additional optimization and security configuration may be required for production deployment.

---

# Frontend

The Moya mobile application is available in the frontend repository:

https://github.com/lilChiie/Mavion-Frontend

---

# Project Purpose

Moya was developed to support a more inclusive tourism experience by making accessibility information easier to discover and use.

The platform combines:

```text
Accessibility
      +
AI
      +
Smart Recommendation
      +
Environmental Monitoring
      +
Community Contribution
```

to create a more accessible and informed travel experience.

---

# License

Developed for the **AI Hackathon IT Del 2026 Submission**.
