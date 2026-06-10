# Virtual Try-On Setup Guide
This guide explains how to set up and use the virtual try-on feature in FitSaathi.

## Current Status
The virtual try-on feature supports:
- ✅ **Placeholder** (simple composite image)
- ✅ **Google Colab** (free GPU acceleration)
- ✅ **Local CatVTON** (coming soon)

---

## Option 1: Quick Start with Placeholder
Just run the server! No extra setup needed.

```bash
uvicorn backend.main:app --reload
```

---

## Option 2: Colab GPU Acceleration (Free! 🚀
This is the easiest way to get high-quality try-ons with free GPU power!

### Step 1: Open Colab Notebook
1. Go to [Google Colab](https://colab.research.google.com)
2. Create a new notebook
3. Copy the contents of `colab_tryon_server.py` into the notebook
4. Set runtime type to **GPU** (Runtime → Change runtime type → Hardware accelerator: GPU)

### Step 2: Run the Server
1. Run all cells in the Colab notebook
2. Wait for ngrok to give you a public URL like: `https://abc123xyz.ngrok-free.app`

### Step 3: Configure FitSaathi
1. Update your `.env` file:
```env
USE_COLAB=true
COLAB_API_URL=https://your-ngrok-url.ngrok-free.app/tryon
```
3. Restart your FitSaathi server

### Step 4: Try It Out!
The try-ons will now use Colab's GPU!

---

## Option 3: Local CatVTON (Coming Soon)
To use local CatVTON, uncomment the dependencies in requirements.txt and follow below.

### Install Dependencies
```bash
pip install torch torchvision transformers diffusers accelerate
```

### Update virtual_tryon.py
See comments in `backend/services/virtual_tryon.py` to uncomment real CatVTON code.

---

## API Endpoints

### 1. Generate Try-On
```http
POST /api/v1/tryon/generate
Content-Type: multipart/form-data

user_id: "demo_user_123"
item_id: "SKU-001"
file: [your_photo.jpg]
```

### 2. Get Result
```http
GET /api/v1/tryon/result/{job_id}
```

---

## Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| USE_COLAB | Use Colab for GPU acceleration | false |
| COLAB_API_URL | Public URL from Colab | - |
| COLAB_API_KEY | Optional API key | - |
| TRYON_OUTPUT_DIR | Where to save try-ons | uploads/tryons |
| USE_CUDA | Use local GPU | false |

---

## Architecture
```
FitSaathi/
├── backend/
│   ├── services/
│   │   └── virtual_tryon.py  # Core try-on logic
│   ├── schemas.py            # Pydantic models
│   ├── config.py           # Settings
│   └── main.py             # API endpoints
├── frontend/
│   └── components/
│       └── VirtualTryOn.tsx  # React UI
├── uploads/
│   ├── users/              # User photos
│   ├── garments/         # Downloaded clothing
│   └── tryons/         # Generated results
└── colab_tryon_server.py  # Colab GPU server
```

---

## Future Enhancements
- Swap CatVTON with IDM-VTON for higher quality!
