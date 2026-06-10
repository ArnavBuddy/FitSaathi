from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class MongoDBClient:
    def __init__(self):
        if settings.MONGODB_URI:
            try:
                self.client = AsyncIOMotorClient(settings.MONGODB_URI)
                self.db = self.client[settings.MONGODB_DB_NAME]
                self.users = self.db.users
                self.inventory = self.db.inventory
                self.recommendations_log = self.db.recommendations_log
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                self.client = None
                self.db = None
                self.users = None
                self.inventory = None
                self.recommendations_log = None
        else:
            self.client = None
            self.db = None
            self.users = None
            self.inventory = None
            self.recommendations_log = None

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.users:
            return None
        return await self.users.find_one({"user_id": user_id})

    async def upsert_user_body_data(self, user_id: str, body_data: Dict[str, Any]) -> None:
        if not self.users:
            return
        body_data["last_scanned"] = datetime.now(timezone.utc)
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"body_data": body_data, "updated_at": datetime.now(timezone.utc)}},
            upsert=True
        )

    async def search_inventory_by_body(
        self,
        body_type: str,
        measurements: Dict[str, Any],
        gender: str,
        style_tags: List[str],
        budget_max_inr: int,
        exclude_skus: List[str] = [],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        if not self.inventory:
            return []
        
        pipeline = [
            {
                "$match": {
                    "in_stock": True,
                    "gender": {"$in": [gender, "unisex"]},
                    "price_inr": {"$lte": budget_max_inr},
                    "item_id": {"$nin": exclude_skus}
                }
            },
            {
                "$addFields": {
                    "style_tag_overlap": {
                        "$size": {"$setIntersection": ["$style_tags", style_tags]}
                    }
                }
            },
            {"$sort": {"style_tag_overlap": -1, "price_inr": 1}},
            {"$limit": limit}
        ]
        cursor = self.inventory.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    async def vector_search_by_style(
        self,
        style_embedding: List[float],
        gender: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        if not self.inventory:
            return []
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "style_vector_index",
                        "path": "style_embedding",
                        "queryVector": style_embedding,
                        "numCandidates": 100,
                        "limit": limit,
                        "filter": {"gender": {"$in": [gender, "unisex"]}}
                    }
                }
            ]
            cursor = self.inventory.aggregate(pipeline)
            return await cursor.to_list(length=limit)
        except Exception as e:
            print(f"Vector search failed (index might not be created yet): {e}")
            return []

    async def get_items_by_skus(self, skus: List[str]) -> List[Dict[str, Any]]:
        if not self.inventory:
            return []
        cursor = self.inventory.find({"item_id": {"$in": skus}})
        return await cursor.to_list(length=len(skus))

    async def log_recommendation(self, session_id: str, user_id: str, scan_result: Optional[Dict[str, Any]], items: List[str]) -> None:
        if not self.recommendations_log:
            return
        log_entry = {
            "session_id": session_id,
            "user_id": user_id,
            "scan_result": scan_result,
            "items_recommended": items,
            "items_clicked": [],
            "items_purchased": [],
            "feedback": None,
            "created_at": datetime.now(timezone.utc)
        }
        await self.recommendations_log.insert_one(log_entry)

    async def update_user_preferences(self, user_id: str, liked: List[str] = [], disliked: List[str] = []) -> None:
        if not self.users:
            return
        update_doc = {"$set": {"updated_at": datetime.now(timezone.utc)}}
        if liked:
            update_doc["$addToSet"] = {"liked_items": {"$each": liked}}
        if disliked:
            if "$addToSet" in update_doc:
                update_doc["$addToSet"]["disliked_items"] = {"$each": disliked}
            else:
                update_doc["$addToSet"] = {"disliked_items": {"$each": disliked}}
        
        await self.users.update_one({"user_id": user_id}, update_doc, upsert=True)

mongodb_client = MongoDBClient()
