#!/usr/bin/env python3
"""
Normalize image backgrounds to pure white by sampling edge colors.
This is a gentler approach than aggressive background removal.
"""

import argparse
from pathlib import Path
from PIL import Image
import numpy as np
from collections import Counter

ROOT = Path(__file__).parent
ASSETS_DIR = ROOT / "assets" / "event_logos"
WORKING_DIR = ROOT / "output" / "working"


def normalize_background(input_path: Path, tolerance: int = 30) -> None:
    """
    Normalize the background color to pure white by sampling edges.

    Args:
        input_path: Path to input image
        tolerance: Color difference threshold (0-255, higher = more aggressive)
    """
    img = Image.open(input_path).convert('RGB')
    img_array = np.array(img)
    height, width = img_array.shape[:2]

    # Sample pixels from all four edges
    edge_pixels = []

    # Top and bottom edges (every 10th pixel)
    edge_pixels.extend(img_array[0, ::10].tolist())
    edge_pixels.extend(img_array[-1, ::10].tolist())

    # Left and right edges (every 10th pixel)
    edge_pixels.extend(img_array[::10, 0].tolist())
    edge_pixels.extend(img_array[::10, -1].tolist())

    # Convert to tuples for counting
    edge_pixels = [tuple(p) for p in edge_pixels]

    # Find the most common edge color (likely the background)
    color_counter = Counter(edge_pixels)
    bg_color = color_counter.most_common(1)[0][0]

    # Create a mask for pixels similar to background color
    bg_array = np.array(bg_color)
    diff = np.abs(img_array.astype(int) - bg_array.astype(int))
    color_distance = np.sum(diff, axis=2)

    # Pixels within tolerance are considered background
    mask = color_distance <= tolerance

    # Replace background pixels with pure white
    img_array[mask] = [255, 255, 255]

    # Save the result
    result_img = Image.fromarray(img_array, 'RGB')
    result_img.save(input_path, 'PNG')

    pixels_changed = np.sum(mask)
    total_pixels = height * width
    percent_changed = (pixels_changed / total_pixels) * 100

    return bg_color, pixels_changed, percent_changed


def restore_from_backup(file_path: Path) -> bool:
    """Restore a file from its .bak backup if it exists."""
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
    if backup_path.exists():
        # Copy backup back to original
        import shutil
        shutil.copy2(backup_path, file_path)
        return True
    return False


def process_event_logos(tolerance: int = 30, restore: bool = False):
    """Process all PNG files in the event logos directory."""
    if not ASSETS_DIR.exists():
        print(f"Event logos directory not found: {ASSETS_DIR}")
        return

    logo_files = list(ASSETS_DIR.glob("*.png"))
    if not logo_files:
        print(f"No PNG files found in {ASSETS_DIR}")
        return

    print(f"Processing {len(logo_files)} event logo(s)...")
    for logo_path in logo_files:
        print(f"  Processing: {logo_path.name}")

        if restore:
            if restore_from_backup(logo_path):
                print(f"    Restored from backup")

        bg_color, pixels_changed, percent_changed = normalize_background(logo_path, tolerance)
        print(f"    BG color: RGB{bg_color}, normalized {pixels_changed:,} pixels ({percent_changed:.1f}%)")


def process_interest_images(event_id: str = None, tolerance: int = 30, restore: bool = False):
    """Process AI-generated interest images."""
    if not WORKING_DIR.exists():
        print(f"Working directory not found: {WORKING_DIR}")
        return

    # Find all interest illustration images
    if event_id:
        pattern = f"{event_id}/*/generated_images/interests_illustration.png"
    else:
        pattern = "*/*/generated_images/interests_illustration.png"

    image_files = list(WORKING_DIR.glob(pattern))
    if not image_files:
        print(f"No interest images found matching: {pattern}")
        return

    print(f"Processing {len(image_files)} interest image(s)...")
    for img_path in image_files:
        event = img_path.parent.parent.parent.name
        user = img_path.parent.parent.name
        print(f"  Processing: {event}/{user}")

        if restore:
            if restore_from_backup(img_path):
                print(f"    Restored from backup")

        bg_color, pixels_changed, percent_changed = normalize_background(img_path, tolerance)
        print(f"    BG color: RGB{bg_color}, normalized {pixels_changed:,} pixels ({percent_changed:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Normalize backgrounds to pure white by sampling edge colors"
    )
    parser.add_argument(
        "--logos",
        action="store_true",
        help="Process event logos in assets/event_logos/"
    )
    parser.add_argument(
        "--interests",
        action="store_true",
        help="Process AI-generated interest images"
    )
    parser.add_argument(
        "--event",
        help="Filter to specific event_id when processing interests"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process both logos and interest images"
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=30,
        help="Color difference threshold (0-255, default 30). Higher = more aggressive"
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore from .bak backups before processing"
    )

    args = parser.parse_args()

    # Default to --all if nothing specified
    if not (args.logos or args.interests or args.all):
        args.all = True

    print(f"Tolerance: {args.tolerance} (higher = more aggressive)")
    if args.restore:
        print("Will restore from backups before processing")
    print()

    if args.all or args.logos:
        process_event_logos(tolerance=args.tolerance, restore=args.restore)
        print()

    if args.all or args.interests:
        process_interest_images(event_id=args.event, tolerance=args.tolerance, restore=args.restore)


if __name__ == "__main__":
    main()
