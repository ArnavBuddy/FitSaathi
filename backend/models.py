from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class BodyMeasurements(BaseModel):
    shoulder_cm_range: List[float]
    chest_cm_range: List[float]
    waist_cm_range: List[float]
    hip_cm_range: List[float]
    inseam_cm_range: List[float]

class BodyData(BaseModel):
    body_type: str
    height_category: str
    shoulder_width: str
    waist_definition: str
    hip_ratio: str
    torso_length: str
    leg_length: str
    estimated_measurements: BodyMeasurements
    recommended_fits: List[str]
    avoid_fits: List[str]
    flattering_styles: List[str]
    confidence_score: float
    analysis_notes: str
    last_scanned: Optional[datetime] = None

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    body_data: Optional[BodyData] = None
    style_preferences: List[str] = []
    preferred_colors: List[str] = []
    avoided_colors: List[str] = []
    budget_inr: Dict[str, int] = {"min": 500, "max": 4000}
    gender_preference: str = "unisex"
    purchase_history: List[str] = []
    liked_items: List[str] = []
    disliked_items: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InventoryItem(BaseModel):
    item_id: str
    name: str
    brand: str
    category: str
    subcategory: str
    gender: str
    sizes_available: List[str]
    fit_type: str
    fit_chart: Dict[str, Dict[str, List[float]]]
    body_types_suited: List[str]
    body_types_avoid: List[str]
    style_tags: List[str]
    colors: List[str]
    price_inr: int
    in_stock: bool
    stock_count: int
    image_url: str
    description: str
    care_instructions: str
    style_embedding: List[float]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RecommendationLog(BaseModel):
    session_id: str
    user_id: str
    scan_result: Optional[Dict[str, Any]] = None
    items_recommended: List[str]
    items_clicked: List[str] = []
    items_purchased: List[str] = []
    feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str

class FeedbackRequest(BaseModel):
    user_id: str
    item_id: str
    action: str # like | dislike | purchase

class RecommendRequest(BaseModel):
    user_id: str
    scan_result: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
