"""Tests for newcode.image_utils."""

import io

from PIL import Image

from newcode.image_utils import constrain_image_dimensions


def _make_png_bytes(
    width: int, height: int, color: tuple[int, int, int] = (10, 20, 30)
) -> bytes:
    """Create an in-memory PNG image for tests."""
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _read_image_size(image_bytes: bytes) -> tuple[int, int]:
    """Read image dimensions from bytes."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        return img.size


def test_constrain_image_dimensions_passthrough_within_limits() -> None:
    image_bytes = _make_png_bytes(100, 100)

    result = constrain_image_dimensions(image_bytes)

    assert result == image_bytes


def test_constrain_image_dimensions_passthrough_exactly_at_limit() -> None:
    image_bytes = _make_png_bytes(1920, 1920)

    result = constrain_image_dimensions(image_bytes)

    assert result == image_bytes


def test_constrain_image_dimensions_passthrough_empty_bytes() -> None:
    assert constrain_image_dimensions(b"") == b""


def test_constrain_image_dimensions_passthrough_non_image_media_type() -> None:
    image_bytes = _make_png_bytes(3000, 1000)

    result = constrain_image_dimensions(image_bytes, media_type="application/pdf")

    assert result == image_bytes


def test_constrain_image_dimensions_resizes_wide_image() -> None:
    image_bytes = _make_png_bytes(3000, 1000)

    result = constrain_image_dimensions(image_bytes)

    assert _read_image_size(result) == (1920, 640)


def test_constrain_image_dimensions_resizes_tall_image() -> None:
    image_bytes = _make_png_bytes(1000, 3000)

    result = constrain_image_dimensions(image_bytes)

    assert _read_image_size(result) == (640, 1920)


def test_constrain_image_dimensions_resizes_when_both_dimensions_over() -> None:
    image_bytes = _make_png_bytes(4000, 3000)

    result = constrain_image_dimensions(image_bytes)

    assert _read_image_size(result) == (1920, 1440)


def test_constrain_image_dimensions_respects_custom_max_dim() -> None:
    image_bytes = _make_png_bytes(1200, 600)

    result = constrain_image_dimensions(image_bytes, max_dim=500)

    assert _read_image_size(result) == (500, 250)


def test_constrain_image_dimensions_handles_extreme_aspect_ratio() -> None:
    image_bytes = _make_png_bytes(1, 5000)

    result = constrain_image_dimensions(image_bytes)

    assert _read_image_size(result) == (1, 1920)


def test_constrain_image_dimensions_invalid_image_bytes_returns_original() -> None:
    corrupt_bytes = b"this is not a valid image"

    result = constrain_image_dimensions(corrupt_bytes)

    assert result == corrupt_bytes


def test_constrain_image_dimensions_media_type_none_still_processes() -> None:
    image_bytes = _make_png_bytes(3000, 1000)

    result = constrain_image_dimensions(image_bytes, media_type=None)

    assert _read_image_size(result) == (1920, 640)


def test_constrain_image_dimensions_image_media_type_processes_normally() -> None:
    image_bytes = _make_png_bytes(1000, 3000)

    result = constrain_image_dimensions(image_bytes, media_type="image/png")

    assert _read_image_size(result) == (640, 1920)
