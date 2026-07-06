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

async def upload_profile_photo_merchant(file_bytes: bytes, merchant_id: int) -> str:
    result = cloudinary.uploader.upload(
        file_bytes, 
        folder = "profile_photos-merchant",
        public_id = f"merchant_{merchant_id}",
        overwrite = True,
        transformation = [
            {"width": 400, "height": 400, "crop": "fill"},
            {"quality": "auto"},
            {"format": "webp"}
        ]
    )
    
    return result["secure_url"]

async def upload_banner_photo_merchant(file_bytes: bytes, merchant_id: int) -> str:
    result = cloudinary.uploader.upload(
        file_bytes, 
        folder = "banner_photos-merchant",
        public_id = f"merchant_{merchant_id}",
        overwrite = True,
        transformation = [
            {"quality": "auto"},
            {"format": "webp"}
        ]
    )
    
    return result["secure_url"]

# async def upload_photo_menu(file_bytes: bytes, merchant_id: int) -> str:
#     result = cloudinary.uploader.upload(
#         file_bytes, 
#         folder = "menu_photos-merchant",
#         public_id = f"merchant_{merchant_id}",
#         overwrite = True,
#         transformation = [
#             {"quality": "auto"},
#             {"format": "webp"}
#         ]
#     )
    
#     return result["secure_url"]

async def upload_menu_image(file_bytes: bytes, menu_id: int) -> str:
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="menu_images",
        public_id=f"menu_{menu_id}",
        overwrite=True,
        transformation=[
            {"width": 800, "height": 600, "crop": "fill"},
            {"quality": "auto"},
            {"format": "webp"}
        ]
    )
    return result["secure_url"]

async def upload_review_photo(file_bytes: bytes, review_id: int) -> str:
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="review_photos",
        public_id=f"review_{review_id}",
        overwrite=True,
        transformation = [
            {"width": 800, "height": 600, "crop": "fill"},
            {"quality": "auto"},
            {"format": "webp"}
        ]
    )
    return result["secure_url"]

async def delete_profile_photo(user_id: int):
    cloudinary.uploader.destroy(f"profile_photos/user_{user_id}")
    
async def delete_merchant_logo(merchant_id: int):
    cloudinary.uploader.destroy(f"profile_photos-merchant/merchant_{merchant_id}")
    
async def delete_merchant_banner(merchant_id: int):
    cloudinary.uploader.destroy(f"banner_photos-merchant/merchant_{merchant_id}")

async def delete_menu_image(menu_id: int):
    cloudinary.uploader.destroy(f"menu_images/menu_{menu_id}")
    
async def delete_review_photo(review_id: int):
    cloudinary.uploader.destroy(f"review_photos/review_{review_id}")