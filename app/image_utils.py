import base64
import io
from typing import Tuple

from fastapi import UploadFile
from PIL import Image

from app.core.config import settings
from app.core.exceptions import ValidationError


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
}


def validate_image_upload(image_bytes: bytes, content_type: str | None) -> None:
    if not image_bytes:
        raise ValidationError("Image file is empty")
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(f"Unsupported image type: {content_type}")


def compress_image(image_bytes: bytes, content_type: str) -> Tuple[bytes, str]:
    if len(image_bytes) <= settings.MAX_RAW_IMAGE_BYTES:
        return image_bytes, content_type

    image = Image.open(io.BytesIO(image_bytes))
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    max_side = 1280
    if max(image.size) > max_side:
        ratio = max_side / max(image.size)
        image = image.resize(
            (int(image.size[0] * ratio), int(image.size[1] * ratio)),
            Image.Resampling.LANCZOS,
        )

    buffer = io.BytesIO()
    if "png" in content_type:
        image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), "image/png"
    if "webp" in content_type:
        image.save(buffer, format="WEBP", quality=85)
        return buffer.getvalue(), "image/webp"

    image.save(buffer, format="JPEG", quality=85, optimize=True)
    return buffer.getvalue(), "image/jpeg"


def image_bytes_to_base64_url(image_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


async def process_upload_image(image: UploadFile) -> Tuple[str, str]:
    image_bytes = await image.read()
    validate_image_upload(image_bytes, image.content_type)
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return encoded, image.content_type or "image/jpeg"


def decode_and_process_image(
    image_base64: str,
    original_mime: str,
    compress: bool = False,
) -> Tuple[bytes, str]:
    raw_bytes = base64.b64decode(image_base64)
    if not compress:
        return raw_bytes, original_mime
    return compress_image(raw_bytes, original_mime)
