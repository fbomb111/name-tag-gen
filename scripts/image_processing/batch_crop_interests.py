"""
Batch process existing interests images with smart cropping.
Creates backups before modifying originals.
"""
from pathlib import Path
from crop_interests_image import crop_interests_image, create_backup


def batch_crop_interests(
    root_dir: Path = Path("output/working"),
    backup_suffix: str = "_original",
    dry_run: bool = False
):
    """
    Find and crop all existing interests images.

    Args:
        root_dir: Root directory to search for images
        backup_suffix: Suffix for backup files
        dry_run: If True, only print what would be done without modifying files
    """
    # Find all interests_illustration.png files
    image_pattern = "**/generated_images/interests_illustration.png"
    image_paths = list(root_dir.glob(image_pattern))

    print(f"Found {len(image_paths)} interests images to process")
    print("=" * 70)

    processed = 0
    skipped = 0
    errors = 0

    for img_path in image_paths:
        # Get relative path for display
        rel_path = img_path.relative_to(root_dir)

        # Check if already has backup (already processed)
        backup_path = img_path.parent / f"{img_path.stem}{backup_suffix}{img_path.suffix}"

        if backup_path.exists():
            print(f"⊘ SKIP (already processed): {rel_path}")
            skipped += 1
            continue

        if dry_run:
            print(f"⋯ WOULD PROCESS: {rel_path}")
            continue

        try:
            # Create backup
            create_backup(img_path, backup_suffix)
            print(f"  ✓ Backup created: {backup_path.name}")

            # Crop image (in-place)
            crop_interests_image(
                input_path=img_path,
                output_path=img_path,
                target_aspect_ratio=2.0,
                margin_inches=0.15
            )
            print(f"✓ PROCESSED: {rel_path}")
            processed += 1

        except Exception as e:
            print(f"✗ ERROR: {rel_path}")
            print(f"  {e}")
            errors += 1

        print()

    # Summary
    print("=" * 70)
    print(f"Summary:")
    print(f"  Processed: {processed}")
    print(f"  Skipped (already processed): {skipped}")
    print(f"  Errors: {errors}")

    if dry_run:
        print(f"\nDRY RUN - No files were modified")
        print(f"Run without --dry-run to process images")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch crop interests images")
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=Path("output/working"),
        help="Root directory to search for images (default: output/working)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying files"
    )

    args = parser.parse_args()

    batch_crop_interests(
        root_dir=args.root_dir,
        dry_run=args.dry_run
    )
