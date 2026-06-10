import json
import random
import asyncio
import numpy as np
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from dotenv import load_dotenv

# Use httpx for async HTTP requests
try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    exit(1)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "fitsaathi")

# FitSaathi constants
FITSAATHI_CATEGORIES = {
    "tops": ["shirt", "t-shirt", "blouse", "polo", "tank-top"],
    "bottoms": ["jeans", "trousers", "shorts", "skirt", "joggers"],
    "dresses": ["maxi-dress", "midi-dress", "cocktail-dress", "sundress", "gown"],
    "outerwear": ["blazer", "jacket", "coat", "hoodie", "cardigan"],
    "footwear": ["sneakers", "boots", "loafers", "heels", "sandals"]
}

GENDERS = ["men", "women", "unisex"]
BODY_TYPES = ["pear", "hourglass", "athletic", "inverted_triangle", "rectangle", "plus"]
STYLE_TAGS = ["formal", "smart-casual", "streetwear", "minimalist", "office", "boho", "sporty"]
COLORS = ["navy", "charcoal", "beige", "black", "white", "olive", "burgundy", "teal"]

# DummyJSON configuration
DUMMYJSON_CATEGORIES = [
    "mens-shirts",
    "mens-shoes",
    "womens-dresses",
    "womens-shoes",
    "womens-bags"
]

# Global cache for DummyJSON products
DUMMY_PRODUCTS = []

# Mapping DummyJSON categories to FitSaathi categories
DUMMY_TO_FITSAATHI_CATEGORY = {
    "mens-shirts": "tops",
    "mens-shoes": "footwear",
    "womens-dresses": "dresses",
    "womens-shoes": "footwear",
    "womens-bags": "outerwear"  # Bags aren't a category, but let's map them to outerwear for diversity
}

DUMMY_TO_FITSAATHI_GENDER = {
    "mens-shirts": "men",
    "mens-shoes": "men",
    "womens-dresses": "women",
    "womens-shoes": "women",
    "womens-bags": "women"
}

def generate_embedding() -> list[float]:
    """Generate a normalized random 128-dimensional vector for style embedding"""
    embedding = np.random.rand(128).astype(np.float32)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding.tolist()

async def load_dummy_products() -> list[dict]:
    """
    Load products from DummyJSON, merge them, deduplicate, and handle errors
    
    Returns:
        List of products from DummyJSON, or empty list if API fails
    """
    logger.info("Loading products from DummyJSON...")
    all_products = []
    seen_product_ids = set()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for category in DUMMYJSON_CATEGORIES:
            url = f"https://dummyjson.com/products/category/{category}"
            try:
                logger.info(f"Fetching {category}...")
                response = await client.get(url)
                response.raise_for_status()  # Raise for HTTP errors
                data = response.json()
                
                for product in data["products"]:
                    if product["id"] not in seen_product_ids:
                        seen_product_ids.add(product["id"])
                        # Add original category info
                        product["_dummy_category"] = category
                        all_products.append(product)
                
                logger.info(f"Loaded {len(data['products'])} products from {category}")
                
            except httpx.TimeoutException:
                logger.warning(f"Request to {category} timed out")
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error for {category}: {e.response.status_code}")
            except Exception as e:
                logger.warning(f"Error fetching {category}: {e}")
    
    logger.info(f"Successfully loaded {len(all_products)} unique products from DummyJSON")
    return all_products

async def initialize_dummy_products():
    """Initialize the global DUMMY_PRODUCTS cache"""
    global DUMMY_PRODUCTS
    try:
        DUMMY_PRODUCTS = await load_dummy_products()
    except Exception as e:
        logger.error(f"Failed to load DummyJSON products: {e}")
        DUMMY_PRODUCTS = []

def generate_item(sku_id: int, category: str) -> dict:
    """
    Generate a FitSaathi inventory item using DummyJSON data if available
    
    Args:
        sku_id: Unique SKU ID for the item
        category: FitSaathi category
        
    Returns:
        Complete FitSaathi inventory item dictionary
    """
    # 1. Determine gender
    gender = random.choice(GENDERS)
    subcategory = random.choice(FITSAATHI_CATEGORIES[category])
    
    # 2. Get product from DummyJSON if available
    product = None
    if DUMMY_PRODUCTS:
        # Deterministic mapping
        product_idx = sku_id % len(DUMMY_PRODUCTS)
        product = DUMMY_PRODUCTS[product_idx]
        
        # Override gender based on DummyJSON category if it makes sense
        if "_dummy_category" in product:
            dummy_cat = product["_dummy_category"]
            if dummy_cat in DUMMY_TO_FITSAATHI_GENDER:
                gender = DUMMY_TO_FITSAATHI_GENDER[dummy_cat]

    # 3. Generate FitSaathi-specific fields
    suited = random.sample(BODY_TYPES, k=random.randint(2, 4))
    avoid = [bt for bt in BODY_TYPES if bt not in suited][:random.randint(0, 2)]

    # 4. Build item
    item = {
        "item_id": f"SKU-{sku_id:03d}",
        "category": category,
        "subcategory": subcategory,
        "gender": gender,
        "sizes_available": ["XS", "S", "M", "L", "XL", "XXL"],
        "fit_type": random.choice(["slim", "regular", "relaxed", "oversized"]),
        "fit_chart": {
            "S": {"chest_cm": [86, 90], "shoulder_cm": [38, 40], "waist_cm": [72, 76]},
            "M": {"chest_cm": [90, 94], "shoulder_cm": [40, 42], "waist_cm": [76, 80]},
            "L": {"chest_cm": [94, 98], "shoulder_cm": [42, 44], "waist_cm": [80, 84]}
        },
        "body_types_suited": suited,
        "body_types_avoid": avoid,
        "style_tags": random.sample(STYLE_TAGS, k=random.randint(2, 3)),
        "colors": random.sample(COLORS, k=random.randint(1, 3)),
        "in_stock": True,
        "stock_count": random.randint(5, 100),
        "style_embedding": generate_embedding(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gallery_images": []
    }

    # 5. Add fields from DummyJSON product if available
    if product:
        item["name"] = product["title"]
        item["brand"] = product.get("brand", "FitSaathi")
        item["description"] = product["description"]
        item["price_inr"] = int(product["price"] * 85)
        item["image_url"] = product["thumbnail"]
        item["gallery_images"] = product["images"]
    else:
        # Fallback to generated data
        item["name"] = f"{random.choice(['Premium', 'Essential', 'Urban', 'Classic'])} {subcategory.replace('-', ' ').title()}"
        item["brand"] = random.choice(["Urban Studio", "FitStyle", "TrendWay", "ModaIndia"])
        item["description"] = f"A high-quality {subcategory} perfect for your daily needs."
        item["price_inr"] = random.randint(499, 8999)
        item["image_url"] = f"https://picsum.photos/seed/fashion{sku_id:03d}/400/500"
    
    item["care_instructions"] = "Machine wash cold"

    return item

async def seed():
    """Main seeding function"""
    # 0. Load DummyJSON products first
    await initialize_dummy_products()

    # 1. Generate items
    items = []
    sku_counter = 1
    for category in FITSAATHI_CATEGORIES:
        for _ in range(10):
            items.append(generate_item(sku_counter, category))
            sku_counter += 1

    # Save to sample_inventory.json
    with open("data/sample_inventory.json", "w") as f:
        json.dump(items, f, indent=2)
    print(f"✅ Generated {len(items)} items in data/sample_inventory.json")
    if DUMMY_PRODUCTS:
        print(f"   Used DummyJSON data for {len(items)} items")

    if not MONGODB_URI:
        print("⚠️ Warning: MONGODB_URI not set. Skipping database seeding.")
        return

    print("\n🔌 Attempting to connect to MongoDB...")
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        # Ping the server to test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB!")
        
        db = client[MONGODB_DB_NAME]
        
        # 2. Insert into MongoDB
        print("📦 Dropping old inventory collection...")
        await db.inventory.drop()
        print("📦 Inserting new items...")
        await db.inventory.insert_many(items)
        print(f"✅ Inserted {len(items)} items into {MONGODB_DB_NAME}.inventory")

        # 3. Create Indexes
        await db.inventory.create_index("item_id", unique=True)
        await db.inventory.create_index([("category", 1), ("gender", 1), ("in_stock", 1)])
        print("✅ Created indexes for inventory")

        # 4. Pre-seed demo users
        demo_users = [
            {
                "user_id": "demo_user_1",
                "name": "Athletic Male",
                "email": "demo1@fitsaathi.com",
                "body_data": {
                    "body_type": "athletic",
                    "height_category": "regular",
                    "estimated_measurements": {"chest_cm_range": [94, 98], "waist_cm_range": [80, 84]},
                    "last_scanned": datetime.now(timezone.utc)
                },
                "style_preferences": ["smart-casual", "minimalist"],
                "gender_preference": "men",
                "budget_inr": {"min": 500, "max": 5000}
            },
            {
                "user_id": "demo_user_2",
                "name": "Hourglass Female",
                "email": "demo2@fitsaathi.com",
                "body_data": {
                    "body_type": "hourglass",
                    "height_category": "petite",
                    "estimated_measurements": {"chest_cm_range": [86, 90], "waist_cm_range": [68, 72]},
                    "last_scanned": datetime.now(timezone.utc)
                },
                "style_preferences": ["formal", "boho"],
                "gender_preference": "women",
                "budget_inr": {"min": 1000, "max": 8000}
            },
            {
                "user_id": "demo_user_3",
                "name": "Rectangle Male",
                "email": "demo3@fitsaathi.com",
                "body_data": {
                    "body_type": "rectangle",
                    "height_category": "tall",
                    "estimated_measurements": {"chest_cm_range": [98, 104], "waist_cm_range": [84, 90]},
                    "last_scanned": datetime.now(timezone.utc)
                },
                "style_preferences": ["streetwear", "sporty"],
                "gender_preference": "men",
                "budget_inr": {"min": 500, "max": 4000}
            }
        ]
        await db.users.drop()
        await db.users.insert_many(demo_users)
        print("✅ Pre-seeded 3 demo users")

        # Atlas Vector Search index definition (for manual creation)
        vector_index = {
            "name": "style_vector_index",
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "style_embedding",
                        "numDimensions": 128,
                        "similarity": "cosine"
                    },
                    {"type": "filter", "path": "gender"},
                    {"type": "filter", "path": "category"},
                    {"type": "filter", "path": "in_stock"}
                ]
            }
        }
        print("\n--- ATLAS VECTOR SEARCH INDEX DEFINITION ---")
        print(json.dumps(vector_index, indent=2))
        print("-------------------------------------------\n")
    except Exception as e:
        print(f"\n❌ Database Error: {e}")
        print("\nPlease check:")
        print("1. Your MONGODB_URI is correct (password should NOT have < > brackets)")
        print("2. Your IP address is whitelisted in MongoDB Atlas (Network Access tab)")
        print("3. The database user exists and has the correct permissions")

if __name__ == "__main__":
    asyncio.run(seed())
