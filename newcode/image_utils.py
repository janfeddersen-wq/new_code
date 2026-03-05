"""Image processing utilities for API compliance.

Ensures images sent to LLM APIs respect dimension limits.
The Claude API enforces a 2000px max dimension for many-image requests.
We use 1920px as default to provide a safety margin.
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Claude API max dimension for many-image requests is 2000px.
# Use 1920 for safety margin.
MAX_IMAGE_DIMENSION = 1920

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore[misc, assignment]


def constrain_image_dimensions(
    image_bytes: bytes,
    max_dim: int = MAX_IMAGE_DIMENSION,
    media_type: Optional[str] = None,
) -> bytes:
    """Resize image if any dimension exceeds max_dim, preserving aspect ratio.

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, etc.).
        max_dim: Maximum allowed width or height in pixels.
        media_type: Optional MIME type hint. If provided and not an image
                    type, returns bytes unchanged.

    Returns:
        Original bytes if within limits or PIL unavailable, resized PNG bytes otherwise.
    """
    # Skip non-image content
    if media_type and not media_type.startswith("image/"):
        return image_bytes

    if not PIL_AVAILABLE or Image is None:
        logger.debug("PIL not available, skipping image dimension check")
        return image_bytes

    if not image_bytes:
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size

        if width <= max_dim and height <= max_dim:
            return image_bytes

        # Calculate scale factor based on the larger dimension
        scale = max_dim / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Ensure minimum dimensions
        new_width = max(new_width, 1)
        new_height = max(new_height, 1)

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save as PNG to preserve quality
        output = io.BytesIO()
        resized.save(output, format="PNG", optimize=True)
        output.seek(0)

        logger.info(
            f"Constrained image dimensions from {width}x{height} "
            f"to {new_width}x{new_height} (max_dim={max_dim})"
        )
        return output.read()

    except Exception as e:
        logger.warning(f"Failed to constrain image dimensions: {e}")
        return image_bytes
