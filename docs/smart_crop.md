# Smart Crop for Interests Images

## Overview
The smart crop module removes excessive dead space from AI-generated interests images while maintaining a consistent 2.0:1 aspect ratio.

## How It Works
1. **Content Detection** - Scans image for non-white pixels (RGB < 245)
2. **Margin Application** - Adds standard 0.15" margin around detected content
3. **Aspect Ratio Enforcement** - Expands crop area to maintain 2.0:1 ratio
4. **Output** - Saves cropped image with consistent dimensions

## Usage

### Automatic (New Images)
Smart cropping is automatically applied to all new interests images generated via `generate_images.py`:

```bash
python3 generate_images.py --interests-only
```

### Batch Process Existing Images
Process all existing images with backup creation:

```bash
# Dry run first to see what will be processed
python3 batch_crop_interests.py --dry-run

# Process all images (creates _original backups)
python3 batch_crop_interests.py
```

### Manual/Programmatic Usage
```python
from crop_interests_image import crop_interests_image, create_backup
from pathlib import Path

# Create backup first
image_path = Path("path/to/interests_illustration.png")
backup_path = create_backup(image_path)

# Crop image in-place
crop_interests_image(
    input_path=image_path,
    output_path=image_path,  # Or specify different output
    target_aspect_ratio=2.0,
    margin_inches=0.15
)
```

## Configuration

Default parameters:
- **Target aspect ratio**: 2.0:1 (width:height) for 2.7" × 1.35" display area
- **Margin**: 0.15 inches around content
- **Background threshold**: RGB ≥ 245 (near-white pixels considered background)
- **DPI**: 288 for margin calculations

## Files

- **crop_interests_image.py** - Core cropping module with clean API
- **batch_crop_interests.py** - Batch processing script for existing images
- **generate_images.py** - Integrated into image generation pipeline

## Backup Strategy

Original images are automatically backed up with `_original` suffix before first processing:
- `interests_illustration.png` - Processed/cropped version
- `interests_illustration_original.png` - Original AI-generated image

If backup exists, the image is skipped (already processed).
