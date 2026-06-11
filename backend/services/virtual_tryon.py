"""
Virtual Try-On service wrapper with abstract interface for easy model swapping.
Supports:
- Placeholder (composite image)
- Local CatVTON
- Google Colab GPU API (for free GPU acceleration)
"""
import os
import logging
import uuid
import time
import aiohttp
from typing import Dict, Optional
from abc import ABC, abstractmethod
from PIL import Image
import io

from backend.config import settings

# =============================================================================
# LOGGING SETUP
# =============================================================================
logger = logging.getLogger(__name__)


# =============================================================================
# ABSTRACT BASE CLASS (Future-Ready)
# =============================================================================
class VirtualTryOnProvider(ABC):
    """Abstract base class for virtual try-on providers."""

    @abstractmethod
    def load_model(self):
        """Load model weights/initialize service."""
        pass

    @abstractmethod
    async def generate_tryon(
        self,
        person_image_path: str,
        garment_image_path: str
    ) -> str:
        """
        Generate virtual try-on image.

        Args:
            person_image_path: Path to user's photo
            garment_image_path: Path to clothing item image

        Returns:
            Path to generated try-on image
        """
        pass

    def _create_placeholder_tryon(
        self,
        person_img: Image.Image,
        garment_img: Image.Image
    ) -> Image.Image:
        """
        Create a simple placeholder composite image (for development without real model).
        Pastes the clothing item on top of the user's photo with transparency for black background.

        Args:
            person_img: User's photo
            garment_img: Clothing item image

        Returns:
            Composite PIL Image
        """
        # Resize garment to fit person
        target_width = person_img.width // 3
        aspect_ratio = garment_img.height / garment_img.width
        target_height = int(target_width * aspect_ratio)
        garment_resized = garment_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Convert garment to RGBA
        garment_rgba = garment_resized.convert("RGBA")
        
        # Make black pixels transparent
        data = garment_rgba.getdata()
        new_data = []
        for item in data:
            # If pixel is black or very dark, make transparent
            if item[0] < 30 and item[1] < 30 and item[2] < 30:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        garment_rgba.putdata(new_data)

        # Create a copy of person image (convert to RGBA for compositing)
        result_rgba = person_img.convert("RGBA").copy()

        # Paste garment in center (adjust coordinates as needed)
        x = (result_rgba.width - target_width) // 2
        y = result_rgba.height // 4
        result_rgba.paste(garment_rgba, (x, y), mask=garment_rgba)
        
        # Convert back to RGB
        result = result_rgba.convert("RGB")

        return result


# =============================================================================
# COLAB API IMPLEMENTATION (GPU ACCELERATION)
# =============================================================================
class ColabTryOnService(VirtualTryOnProvider):
    """Google Colab-based virtual try-on provider for GPU acceleration."""

    def __init__(self):
        self.colab_api_url = os.environ.get("COLAB_API_URL", "")
        self.colab_api_key = os.environ.get("COLAB_API_KEY", "")
        self.is_model_loaded = True  # Colab handles model loading

    def load_model(self):
        """Verify Colab API connectivity."""
        logger.info("Checking Colab API configuration")
        if not self.colab_api_url:
            logger.warning("COLAB_API_URL not set - will use placeholder try-on")
        else:
            logger.info(f"Colab API configured: {self.colab_api_url}")

    async def generate_tryon(
        self,
        person_image_path: str,
        garment_image_path: str
    ) -> str:
        """
        Generate try-on image using Colab GPU.

        Args:
            person_image_path: User's photo path
            garment_image_path: Clothing item path

        Returns:
            Generated image path
        """
        start_time = time.time()

        logger.info(f"Starting Colab try-on generation: person={person_image_path}, garment={garment_image_path}")

        try:
            # If Colab API not configured, fall back to placeholder
            if not self.colab_api_url:
                logger.warning("Colab API not configured - using placeholder")
                return await self._fallback_placeholder_tryon(person_image_path, garment_image_path)

            # Upload images to Colab API
            form_data = aiohttp.FormData()
            with open(person_image_path, 'rb') as f:
                form_data.add_field('person_image', f, filename='person.jpg')
            with open(garment_image_path, 'rb') as f:
                form_data.add_field('garment_image', f, filename='garment.jpg')

            if self.colab_api_key:
                headers = {'Authorization': f'Bearer {self.colab_api_key}'}
            else:
                headers = {}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.colab_api_url,
                    data=form_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Colab API error {response.status}: {error_text}")

                    result_data = await response.read()

                    # Save result
                    output_filename = f"tryon_{uuid.uuid4().hex}.jpg"
                    output_path = os.path.join(settings.TRYON_OUTPUT_DIR, output_filename)

                    with open(output_path, 'wb') as f:
                        f.write(result_data)

                    elapsed_time = time.time() - start_time
                    logger.info(f"Colab try-on completed in {elapsed_time:.2f}s: {output_path}")
                    return output_path

        except Exception as e:
            logger.error(f"Colab try-on failed: {str(e)}, falling back to placeholder", exc_info=True)
            return await self._fallback_placeholder_tryon(person_image_path, garment_image_path)

    async def _fallback_placeholder_tryon(
        self,
        person_image_path: str,
        garment_image_path: str
    ) -> str:
        """Fallback placeholder when Colab is not available."""
        person_img = Image.open(person_image_path).convert("RGB")
        garment_img = Image.open(garment_image_path).convert("RGB")
        result_img = self._create_placeholder_tryon(person_img, garment_img)

        output_filename = f"tryon_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(settings.TRYON_OUTPUT_DIR, output_filename)
        result_img.save(output_path, quality=95)
        return output_path


# =============================================================================
# CATVTON IMPLEMENTATION (LOCAL)
# =============================================================================
class CatVTONService(VirtualTryOnProvider):
    """CatVTON implementation of the virtual try-on provider."""

    def __init__(self):
        self.model = None
        self.device = "cuda" if os.environ.get("USE_CUDA", "false").lower() == "true" else "cpu"
        self.is_model_loaded = False

    def load_model(self):
        """
        Load CatVTON model weights.
        Note: This is a placeholder for actual CatVTON implementation.
        Replace with real model loading code once CatVTON is integrated.
        """
        logger.info(f"Loading CatVTON model on {self.device}")

        # ---------------------------------------------------------------------
        # TODO: Replace this with actual CatVTON model loading
        # Example (pseudocode):
        # from catvton import CatVTONPipeline
        # self.model = CatVTONPipeline.from_pretrained(
        #     settings.CATVTON_MODEL_PATH or "catvton/CatVTON"
        # )
        # self.model = self.model.to(self.device)
        # ---------------------------------------------------------------------

        # For now, let's simulate model loading
        time.sleep(2)
        self.is_model_loaded = True
        logger.info("CatVTON model loaded successfully!")

    async def generate_tryon(
        self,
        person_image_path: str,
        garment_image_path: str
    ) -> str:
        """
        Generate try-on image using CatVTON.

        Args:
            person_image_path: User's photo path
            garment_image_path: Clothing item path

        Returns:
            Generated image path
        """
        start_time = time.time()

        logger.info(f"Starting try-on generation: person={person_image_path}, garment={garment_image_path}")

        try:
            # Validate input images
            person_img = Image.open(person_image_path).convert("RGB")
            garment_img = Image.open(garment_image_path).convert("RGB")
            logger.info(f"Input images loaded: person={person_img.size}, garment={garment_img.size}")

            # -----------------------------------------------------------------
            # TODO: Replace this with actual CatVTON inference
            # Example (pseudocode):
            # result = self.model(
            #     person_image=person_img,
            #     garment_image=garment_img
            # )
            # -----------------------------------------------------------------

            # For now, create a placeholder composite image
            result_img = self._create_placeholder_tryon(person_img, garment_img)

            # Save the result
            output_filename = f"tryon_{uuid.uuid4().hex}.jpg"
            output_path = os.path.join(settings.TRYON_OUTPUT_DIR, output_filename)
            result_img.save(output_path, quality=95)

            elapsed_time = time.time() - start_time
            logger.info(f"Try-on generation completed in {elapsed_time:.2f}s: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error generating try-on: {str(e)}", exc_info=True)
            raise


# =============================================================================
# SIMPLE IN-MEMORY JOB STORE (Replace with Redis/Mongo in production)
# =============================================================================
class TryOnJobStore:
    """Simple in-memory store for tracking try-on jobs."""

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}

    def create_job(self, user_id: str, item_id: str) -> str:
        """Create a new try-on job and return job ID."""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "job_id": job_id,
            "user_id": user_id,
            "item_id": item_id,
            "status": "processing",
            "created_at": time.time(),
            "generated_image": None,
            "error_message": None,
            "processing_time_seconds": None
        }
        logger.info(f"Created new try-on job: {job_id} for user {user_id}")
        return job_id

    def update_job(self, job_id: str, **kwargs):
        """Update an existing try-on job."""
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
            logger.info(f"Updated try-on job {job_id}: {kwargs}")

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get a try-on job by ID."""
        return self.jobs.get(job_id)


# =============================================================================
# GLOBAL INSTANCES (Singleton pattern)
# =============================================================================
tryon_provider: Optional[VirtualTryOnProvider] = None
job_store: TryOnJobStore = TryOnJobStore()


def init_tryon_service():
    """Initialize the try-on service (call once on app startup)."""
    global tryon_provider

    logger.info("Initializing Virtual Try-On service...")
    settings.ensure_directories()

    # Choose provider based on environment variables
    if os.environ.get("USE_COLAB", "false").lower() == "true":
        logger.info("Using ColabTryOnService")
        tryon_provider = ColabTryOnService()
    else:
        logger.info("Using CatVTONService (placeholder)")
        tryon_provider = CatVTONService()

    tryon_provider.load_model()
    logger.info("Virtual Try-On service initialized successfully!")


# =============================================================================
# UTILITIES
# =============================================================================
async def download_garment_image(image_url: str) -> str:
    """
    Download garment image from URL to local filesystem.

    Args:
        image_url: URL of the clothing item image

    Returns:
        Local path to downloaded image
    """
    logger.info(f"Downloading garment image: {image_url}")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(image_url) as response:
                response.raise_for_status()

                # Save image
                filename = f"garment_{uuid.uuid4().hex}.jpg"
                filepath = os.path.join(settings.UPLOADS_GARMENTS_DIR, filename)

                img_data = await response.read()
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
                img.save(filepath, quality=95)

                logger.info(f"Downloaded garment image: {filepath}")
                return filepath

    except Exception as e:
        logger.error(f"Error downloading garment image: {str(e)}")
        raise
