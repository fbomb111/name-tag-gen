"""
Smart cropping for AI-generated interests images.
Detects content bounds and crops to remove excessive dead space while maintaining aspect ratio.
"""
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import numpy as np


def crop_interests_image(
    input_path: Path,
    output_path: Optional[Path] = None,
    target_aspect_ratio: float = 2.0,
    margin_inches: float = 0.15,
    dpi: int = 288,
    background_threshold: int = 245
) -> Path:
    """
    Crop interests image to remove dead space while maintaining aspect ratio.

    Clean API - scans for content bounds, applies standard margins, crops to target ratio.

    Args:
        input_path: Path to input image
        output_path: Path to save cropped image (defaults to input_path if None)
        target_aspect_ratio: Width/height ratio to maintain (default 2.0 for 2.7"x1.35")
        margin_inches: Standard margin around content in inches
        dpi: DPI for margin calculations (default 288)
        background_threshold: RGB threshold for detecting background (default 245)
            Pixels with all RGB values >= this are considered background

    Returns:
        Path to output file
    """
    if output_path is None:
        output_path = input_path

    # Load image
    img = Image.open(input_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Convert to numpy array for analysis
    img_array = np.array(img)

    # Detect content bounds
    content_bounds = _detect_content_bounds(img_array, background_threshold)

    if content_bounds is None:
        # No content detected, return original
        if output_path != input_path:
            img.save(output_path)
        return output_path

    # Apply margins
    margin_px = int(margin_inches * dpi)
    top, bottom, left, right = content_bounds

    top = max(0, top - margin_px)
    bottom = min(img_array.shape[0], bottom + margin_px)
    left = max(0, left - margin_px)
    right = min(img_array.shape[1], right + margin_px)

    # Crop to content + margins
    content_height = bottom - top
    content_width = right - left
    content_center_y = (top + bottom) / 2
    content_center_x = (left + right) / 2

    # Calculate exact crop dimensions for target aspect ratio
    # Try both orientations and pick the one that fits the content
    # Option A: Base on height, expand width
    crop_height_a = content_height
    crop_width_a = int(crop_height_a * target_aspect_ratio)

    # Option B: Base on width, expand height
    crop_width_b = content_width
    crop_height_b = int(crop_width_b / target_aspect_ratio)

    # Choose the option that encompasses all content (larger dimensions)
    if crop_width_a >= content_width and crop_height_a >= content_height:
        # Option A works
        final_width = crop_width_a
        final_height = crop_height_a
    elif crop_width_b >= content_width and crop_height_b >= content_height:
        # Option B works
        final_width = crop_width_b
        final_height = crop_height_b
    else:
        # Both options work, choose the smaller one (less dead space)
        if crop_width_a * crop_height_a < crop_width_b * crop_height_b:
            final_width = crop_width_a
            final_height = crop_height_a
        else:
            final_width = crop_width_b
            final_height = crop_height_b

    # Verify exact aspect ratio (adjust width to ensure perfect ratio)
    final_height = max(final_height, content_height)
    final_width = int(final_height * target_aspect_ratio)

    # Center the crop area on the content
    crop_left = int(content_center_x - final_width / 2)
    crop_right = crop_left + final_width
    crop_top = int(content_center_y - final_height / 2)
    crop_bottom = crop_top + final_height

    # Check if crop extends beyond image bounds
    img_height, img_width = img_array.shape[:2]
    needs_padding = (crop_left < 0 or crop_right > img_width or
                     crop_top < 0 or crop_bottom > img_height)

    if needs_padding:
        # Create a white canvas large enough to accommodate the crop
        canvas_width = max(final_width, img_width)
        canvas_height = max(final_height, img_height)
        canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))

        # Calculate where to paste the original image on the canvas
        paste_x = max(0, -crop_left)
        paste_y = max(0, -crop_top)
        canvas.paste(img, (paste_x, paste_y))

        # Adjust crop coordinates for the canvas
        canvas_crop_left = crop_left + paste_x
        canvas_crop_top = crop_top + paste_y
        canvas_crop_right = canvas_crop_left + final_width
        canvas_crop_bottom = canvas_crop_top + final_height

        # Crop from canvas
        cropped = canvas.crop((canvas_crop_left, canvas_crop_top,
                              canvas_crop_right, canvas_crop_bottom))
    else:
        # Crop directly from original image (no padding needed)
        cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(output_path)

    return output_path


def _detect_content_bounds(img_array: np.ndarray, threshold: int = 245) -> Optional[Tuple[int, int, int, int]]:
    """
    Detect bounds of non-background content.

    Args:
        img_array: Image as numpy array (H, W, 3)
        threshold: RGB threshold for background detection

    Returns:
        Tuple of (top, bottom, left, right) pixel indices, or None if no content
    """
    # Create mask of non-background pixels
    # A pixel is background if all RGB values >= threshold
    is_background = np.all(img_array >= threshold, axis=2)
    is_content = ~is_background

    # Find rows and columns with content
    content_rows = np.any(is_content, axis=1)
    content_cols = np.any(is_content, axis=0)

    if not np.any(content_rows) or not np.any(content_cols):
        return None

    # Find bounds
    top = np.argmax(content_rows)
    bottom = len(content_rows) - np.argmax(content_rows[::-1])
    left = np.argmax(content_cols)
    right = len(content_cols) - np.argmax(content_cols[::-1])

    return (top, bottom, left, right)


def create_backup(image_path: Path, backup_suffix: str = "_original") -> Path:
    """
    Create backup of original image before processing.

    Args:
        image_path: Path to image to backup
        backup_suffix: Suffix to add to backup filename

    Returns:
        Path to backup file
    """
    backup_path = image_path.parent / f"{image_path.stem}{backup_suffix}{image_path.suffix}"

    # Only create backup if it doesn't already exist
    if not backup_path.exists():
        img = Image.open(image_path)
        img.save(backup_path)

    return backup_path
