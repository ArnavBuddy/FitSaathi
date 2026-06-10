# FitSaathi — AI Fashion Stylist Agent

## Overview
FitSaathi is an AI-powered personal stylist that helps users find clothing that perfectly fits their body type and proportions. By analyzing a full-body photo using Gemini Vision, the agent extracts precise measurements and body characteristics to provide personalized outfit recommendations from a MongoDB-hosted inventory.

The application bridges the gap between digital shopping and physical fit, ensuring users feel confident in their style choices. It features a warm, body-positive AI assistant that explains exactly why each recommendation works for the user's unique silhouette.

## Architecture
- **Frontend**: Vanilla HTML/CSS/JS single-page application. Responsive, luxurious dark-themed UI.
- **Backend**: FastAPI (Python 3.11) serving as the orchestration layer.
- **AI Core**: 
  - **Gemini 2.0 Flash**: Used for both vision analysis and conversational styling.
  - **Vertex AI Agent Builder**: Orchestrates the stylist persona and tool usage.
- **Database**: MongoDB Atlas for inventory storage, user profiles, and vector search.
- **Deployment**: Dockerized and ready for Google Cloud Run.

## Partner Integration: MongoDB MCP
FitSaathi leverages the power of MongoDB in three critical ways:
1. **Inventory Management**: Stores 50+ clothing items with detailed fit charts and style tags.
2. **Vector Search**: Uses Atlas Vector Search to find items that match a user's style embedding, enabling semantic discovery beyond simple filters.
3. **Preference Learning**: Stores user likes/dislikes and body data to personalize future sessions.

## Quick Start (Local)
1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd fitsaathi
   cp .env.example .env
   # Fill in MONGODB_URI, GOOGLE_API_KEY, etc.
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Seed Data**:
   ```bash
   python data/seed_inventory.py
   ```
4. **Run Application**:
   ```bash
   uvicorn backend.main:app --reload
   ```

## MongoDB Atlas Setup
1. Create a free M0 cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Get your connection string and add it to `.env` as `MONGODB_URI`.
3. Create a Vector Search index on the `inventory` collection using the definition in `deploy/atlas_vector_index.json`.

## Google Cloud Setup
1. Create a GCP project and enable the Vertex AI and Gemini APIs.
2. Generate an API Key from AI Studio or use a Service Account.
3. Run the deployment script:
   ```bash
   bash deploy/cloud_run_deploy.sh
   ```

## Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | Atlas Connection String | `mongodb+srv://...` |
| `GOOGLE_API_KEY` | Gemini API Key | `AIza...` |
| `GOOGLE_PROJECT_ID`| GCP Project ID | `my-project-id` |
| `SECRET_KEY` | App security key | `super-secret` |

## API Reference
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/scan` | Analyzes body photo and saves data |
| `POST` | `/api/recommend`| Returns ranked outfit suggestions |
| `POST` | `/api/chat` | Chat with the AI Stylist |
| `GET` | `/api/user/{id}`| Retrieves user profile |
| `GET` | `/health` | API Health check |
