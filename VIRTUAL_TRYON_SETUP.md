# Virtual Try-On Setup Guide

This guide explains how to set up and use the CatVTON-powered virtual try-on feature in FitSaathi.

## Current Status

The virtual try-on feature is fully integrated with:
- ✅ Abstract provider interface (easy to swap models)
- ✅ CatVTON wrapper (placeholder implementation)
- ✅ Background task processing
- ✅ Job status polling
- ✅ React + Tailwind component
- ✅ Upload directories auto-creation

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**
   ```bash
   uvicorn backend.main:app --reload
   ```

3. **Test the endpoint**
   The API is available at `http://localhost:8080`
   - `POST /api/v1/tryon/generate` - Initiate try-on
   - `GET /api/v1/tryon/result/{job_id}` - Get results

## Current Implementation

Right now, the virtual try-on uses a simple placeholder composite:
- It takes your photo
- Takes the clothing item
- Pastes the clothing in the center

## Integrating Real CatVTON

To replace the placeholder with real CatVTON:

### Option 1: Use Hugging Face Implementation

1. **Uncomment dependencies in requirements.txt**
   ```txt
   torch>=2.0.0
   torchvision>=0.15.0
   transformers>=4.30.0
   diffusers>=0.20.0
   accelerate>=0.20.0
   ```

2. **Install dependencies**
   ```bash
   pip install torch torchvision transformers diffusers accelerate
   ```

3. **Update `backend/services/virtual_tryon.py`**

   In the `CatVTONService` class:

   ```python
   from diffusers import CatVTONPipeline
   import torch

   def load_model(self):
       logger.info(f"Loading CatVTON model on {self.device}")
       self.model = CatVTONPipeline.from_pretrained(
           "zhengchong/CatVTON",
           torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
       )
       if self.device == "cuda":
           self.model = self.model.to("cuda")
       self.is_model_loaded = True
       logger.info("CatVTON model loaded!")

   def generate_tryon(self, person_image_path, garment_image_path):
       from PIL import Image

       person_img = Image.open(person_image_path).convert("RGB")
       garment_img = Image.open(garment_image_path).convert("RGB")

       result = self.model(
           person_image=person_img,
           garment_image=garment_img
       )

       output_path = os.path.join(
           settings.TRYON_OUTPUT_DIR,
           f"tryon_{uuid.uuid4().hex}.jpg"
       )
       result.save(output_path)
       return output_path
   ```

### Option 2: Use Colab for GPU Acceleration

If you don't have a local GPU, you can:

1. **Set up a Colab notebook**
2. **Run CatVTON there**
3. **Create an API endpoint**
4. **Update `download_garment_image` function** to call your Colab API

## API Endpoints

### 1. Generate Try-On
```http
POST /api/v1/tryon/generate
Content-Type: multipart/form-data

user_id: "demo_user_123"
item_id: "SKU-001"
file: [your_photo.jpg]
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

### 2. Get Result
```http
GET /api/v1/tryon/result/{job_id}
```

Response (pending):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "generated_image": null,
  "error_message": null,
  "processing_time_seconds": null
}
```

Response (success):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "generated_image": "/uploads/tryons/tryon_abc123.jpg",
  "error_message": null,
  "processing_time_seconds": 2.45
}
```

## React Component Usage

```tsx
import VirtualTryOn from './components/VirtualTryOn';

function ProductPage() {
  const [showTryOn, setShowTryOn] = useState(false);
  const userId = "demo_user_123";

  const item = {
    item_id: "SKU-001",
    name: "Classic White Shirt",
    image_url: "/path/to/shirt.jpg",
    price_inr: 1999,
    brand: "FitSaathi"
  };

  return (
    <>
      <button onClick={() => setShowTryOn(true)}>
        Virtual Try-On
      </button>

      {showTryOn && (
        <VirtualTryOn
          item={item}
          userId={userId}
          onClose={() => setShowTryOn(false)}
        />
      )}
    </>
  );
}
```

## Architecture Overview

```
FitSaathi/
├── backend/
│   ├── services/
│   │   └── virtual_tryon.py  # Core try-on logic
│   ├── schemas.py            # Pydantic models
│   ├── config.py            # Settings
│   └── main.py              # FastAPI endpoints
├── frontend/
│   └── components/
│       └── VirtualTryOn.tsx # React UI
└── uploads/
    ├── users/              # User photos
    ├── garments/           # Downloaded clothing
    └── tryons/             # Generated results
```

## Future Enhancements

1. **IDM-VTON Integration**: Swap CatVTON with IDM-VTON for better quality
2. **Redis for Job Store**: Replace in-memory store for persistence
3. **Queue System**: Use Celery/RQ for better task management
4. **WebSockets**: Real-time updates instead of polling
5. **Batch Processing**: Handle multiple try-ons at once

## Troubleshooting

### Common Issues

**Q: The model is not loading**
A: Check if you uncommented the dependencies in requirements.txt

**Q: CUDA out of memory**
A: Reduce batch size or use CPU by setting `USE_CUDA=false`

**Q: Generated images are not saving**
A: Make sure `uploads/tryons` directory exists and is writable
