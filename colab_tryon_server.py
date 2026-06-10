"""
# FitSaathi Colab Virtual Try-On Server
This notebook runs a CatVTON-based virtual try-on server that you can use
for free GPU acceleration with FitSaathi!
"""
from google.colab.output import eval_js
from pyngrok import ngrok
import uvicorn
import nest_asyncio
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
import io
import os

# Apply nest_asyncio for running uvicorn in Colab
nest_asyncio.apply()

app = FastAPI(title="FitSaathi Colab Try-On Server")

# Create directories
os.makedirs("/tmp/tryons", exist_ok=True)


def create_placeholder_tryon(person_img: Image.Image, garment_img: Image.Image) -> Image.Image:
    """Create a simple placeholder try-on (replace with real CatVTON later!)"""
    # Resize garment
    target_width = person_img.width // 3
    aspect_ratio = garment_img.height / garment_img.width
    target_height = int(target_width * aspect_ratio)
    garment_resized = garment_img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    # Composite
    result = person_img.copy()
    x = (result.width - target_width) // 2
    y = result.height // 4
    result.paste(garment_resized, (x, y))

    return result


@app.post("/tryon")
async def run_tryon(person_image: UploadFile = File(...), garment_image: UploadFile = File(...)):
    """Run virtual try-on on uploaded images"""
    print("Received try-on request!")

    # Load images
    person_data = await person_image.read()
    garment_data = await garment_image.read()

    person_img = Image.open(io.BytesIO(person_data)).convert("RGB")
    garment_img = Image.open(io.BytesIO(garment_data)).convert("RGB")

    # Generate result
    result_img = create_placeholder_tryon(person_img, garment_img)

    # Save result
    output_path = "/tmp/tryons/result.jpg"
    result_img.save(output_path, quality=95)

    # Return as file response
    return FileResponse(
        output_path,
        media_type="image/jpeg",
        filename="tryon_result.jpg"
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "gpu": "available"}


def start_server():
    """Start the server and get public URL"""
    # Optionally set ngrok auth token if you have one
    # ngrok.set_auth_token("YOUR_NGROK_AUTH_TOKEN")

    # Start ngrok tunnel
    print("Starting ngrok tunnel...")
    public_tunnel = ngrok.connect(8000)
    public_url = public_tunnel.public_url
    print(f"\n🚀 Colab Try-On Server is running at: {public_url}")
    print(f"📡 Full try-on endpoint: {public_url}/tryon")
    print(f"\nAdd this URL to your FitSaathi .env file:\nCOLAB_API_URL={public_url}/tryon\nUSE_COLAB=true\n")

    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    start_server()
