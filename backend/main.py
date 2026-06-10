from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import logging
import os
import uuid
import json

from .config import settings
from .models import ChatRequest, FeedbackRequest, RecommendRequest
from .vision import analyze_body_photo
from .mongodb_client import mongodb_client
from .ranker import rank_items
from .agent import agent_client
from .embeddings import generate_style_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FitSaathi API", version="1.0.0")

# Absolute paths for static files and templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
INDEX_PATH = os.path.join(BASE_DIR, "frontend", "index.html")

# Load fallback inventory
FALLBACK_INVENTORY = []
fallback_path = os.path.join(BASE_DIR, "data", "sample_inventory.json")
if os.path.exists(fallback_path):
    with open(fallback_path, "r") as f:
        FALLBACK_INVENTORY = json.load(f)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.post("/api/scan")
async def scan_body(user_id: str = Form(...), file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.")
    
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB}MB.")

    analysis = await analyze_body_photo(contents)
    
    if "error" in analysis:
        return analysis

    try:
        await mongodb_client.upsert_user_body_data(user_id, analysis)
    except Exception as e:
        logger.warning(f"Could not save to DB: {e}")
    return analysis

@app.post("/api/recommend")
async def get_recommendations(request: RecommendRequest):
    user = None
    try:
        user = await mongodb_client.get_user(request.user_id)
    except Exception as e:
        logger.warning(f"Could not fetch user from DB: {e}")
    
    if not user:
        # Create a basic user if not exists for demo
        user = {
            "user_id": request.user_id,
            "body_data": request.scan_result or {"body_type": "athletic", "height_category": "regular", "estimated_measurements": {}},
            "style_preferences": [],
            "budget_inr": {"min": 500, "max": 10000},
            "gender_preference": "unisex"
        }

    body_data = request.scan_result or user.get("body_data")

    filters = request.filters or {}
    gender = filters.get("gender", user.get("gender_preference", "unisex"))
    budget_max = filters.get("budget_max", user.get("budget_inr", {}).get("max", 10000))
    style_tags = filters.get("style_tags", user.get("style_preferences", []))

    items = []
    try:
        # 1. Search by body proportions
        items = await mongodb_client.search_inventory_by_body(
            body_type=body_data.get("body_type"),
            measurements=body_data.get("estimated_measurements", {}),
            gender=gender,
            style_tags=style_tags,
            budget_max_inr=budget_max
        )

        # 2. Vector search by style (using user's style tags to generate a pseudo-embedding)
        style_embedding = generate_style_embedding(style_tags)
        vector_items = []
        try:
            vector_items = await mongodb_client.vector_search_by_style(style_embedding, gender)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}. Index might not be ready.")

        # Merge and deduplicate
        all_items_dict = {item["item_id"]: item for item in items + vector_items}
        all_items = list(all_items_dict.values())
        
        if not all_items and FALLBACK_INVENTORY:
            logger.info("Using fallback inventory data")
            # Apply filters to fallback inventory too!
            all_items = FALLBACK_INVENTORY
            
            # Apply gender filter
            if gender != "unisex":
                all_items = [
                    item for item in all_items
                    if item.get("gender") in [gender, "unisex"]
                ]
            
            # Apply budget filter
            all_items = [
                item for item in all_items
                if item.get("price_inr", 0) <= budget_max
            ]
            
            # Apply style tags filter (occasion)
            if style_tags:
                all_items = [
                    item for item in all_items
                    if len(
                        set(item.get("style_tags", [])) & set(style_tags)
                    ) > 0
                ]
                all_items.sort(
                    key=lambda item: len(
                        set(item.get("style_tags", [])) & set(style_tags)
                    ),
                    reverse=True
                )

    except Exception as e:
        logger.warning(f"DB search failed, using fallback data: {e}")
        all_items = FALLBACK_INVENTORY
        
        # Apply filters to fallback inventory too!
        if gender != "unisex":
            all_items = [
                item for item in all_items
                if item.get("gender") in [gender, "unisex"]
            ]
        
        if budget_max:
            all_items = [
                item for item in all_items
                if item.get("price_inr", 0) <= budget_max
            ]
            
        # Apply style tags filter (occasion) to exception case too
        if style_tags:
            all_items = [
                item for item in all_items
                if len(
                    set(item.get("style_tags", [])) & set(style_tags)
                ) > 0
            ]

    if not all_items:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

    # Rank items
    ranked_items = rank_items(all_items, body_data, user)
    
    return ranked_items[:12]

@app.post("/api/chat")
async def chat_with_stylist(request: ChatRequest):
    user = await mongodb_client.get_user(request.user_id)
    body_data = user.get("body_data") if user else {}
    
    response = await agent_client.chat(
        user_id=request.user_id,
        message=request.message,
        session_id=request.session_id,
        body_data=body_data
    )
    return {"response": response}

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    liked = [request.item_id] if request.action == "like" else []
    disliked = [request.item_id] if request.action == "dislike" else []
    
    await mongodb_client.update_user_preferences(request.user_id, liked=liked, disliked=disliked)
    return {"status": "success"}

@app.get("/api/user/{user_id}")
async def get_user_profile(user_id: str):
    user = await mongodb_client.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Remove ObjectId for JSON serialization
    if "_id" in user:
        user["_id"] = str(user["_id"])
    return user

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

# Serve Frontend
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(INDEX_PATH)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
