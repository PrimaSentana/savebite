import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config (
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET
)

async def upload_profile_photo(file_bytes: bytes, user_id: int) -> str:
    result = cloudinary.uploader.upload(
        file_bytes, 
        folder = "profile_photos",
        public_id = f"user_{user_id}",
        overwrite = True,
        transformation = [
            {"width": 400, "height": 400, "crop": "fill"},
            {"quality": "auto"},
            {"format": "webp"}
        ]
    )
    
    return result["secure_url"]

async def delete_profile_photo(user_id: int):
    cloudinary.uploader.destroy(f"profile_photos/user_{user_id}")