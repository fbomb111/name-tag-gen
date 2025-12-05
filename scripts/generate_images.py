#!/usr/bin/env python3
"""
Generate AI images using Azure OpenAI GPT Image 1.
Reads prompts from output/ai_prompts and generates corresponding images.
"""
import os
import json
import base64
import time
import argparse
from pathlib import Path
from typing import Literal
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.image_processing.crop_interests_image import crop_interests_image
from src.utils.paths import PROJECT_ROOT as ROOT, get_working_dir

# Load environment variables
load_dotenv()

# Lazy initialization - don't create directories at import time (fails in Azure's read-only filesystem)
_working_dir = None

def _get_working_dir_lazy():
    """Get working directory lazily (only when needed, not at import time)."""
    global _working_dir
    if _working_dir is None:
        _working_dir = get_working_dir()
    return _working_dir

# Azure OpenAI settings - loaded lazily to allow module import without env vars
API_VERSION = "2025-04-01-preview"
DEPLOYMENT_NAME = "gpt-image-1"


def _get_azure_config():
    """Get Azure OpenAI configuration, raising error if not configured.

    Supports two naming conventions:
    - Local dev: AZUREAI_API_CUSTOM_API_KEY, AZUREAI_API_CUSTOM_BASE_URL
    - Azure: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
    """
    # Try both naming conventions
    api_key = os.getenv("AZUREAI_API_CUSTOM_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    base_url = os.getenv("AZUREAI_API_CUSTOM_BASE_URL") or os.getenv("AZURE_OPENAI_ENDPOINT")

    if not api_key or not base_url:
        raise ValueError(
            "Missing Azure OpenAI credentials. "
            "Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in Azure Function App settings, "
            "or AZUREAI_API_CUSTOM_API_KEY and AZUREAI_API_CUSTOM_BASE_URL in local .env file."
        )

    endpoint_url = f"{base_url.rstrip('/')}/openai/deployments/{DEPLOYMENT_NAME}/images/generations?api-version={API_VERSION}"
    return api_key, endpoint_url


def generate_image(
    prompt: str,
    size: Literal["1024x1024", "1536x1024", "1024x1536"] = "1024x1024",
    quality: Literal["low", "medium", "high"] = "medium",
    output_format: Literal["png", "jpg"] = "png",
) -> bytes:
    """
    Generate an image using Azure OpenAI GPT Image 1.

    Args:
        prompt: The text prompt describing the image to generate
        size: Image dimensions (1024x1024, 1536x1024, or 1024x1536)
        quality: Image quality (low, medium, high)
        output_format: Output format (png or jpg)

    Returns:
        bytes: The generated image data
    """
    api_key, endpoint_url = _get_azure_config()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_compression": 100,
        "output_format": output_format,
        "n": 1
    }

    import logging
    import time

    logging.info(f"  Calling Azure OpenAI API (size: {size}, quality: {quality})...")
    start_time = time.time()

    try:
        response = requests.post(endpoint_url, headers=headers, json=payload, timeout=120)
    except requests.exceptions.Timeout:
        raise Exception("Azure OpenAI API request timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error calling Azure OpenAI API: {str(e)}")

    elapsed = time.time() - start_time
    logging.info(f"  Azure OpenAI API responded in {elapsed:.1f}s (status: {response.status_code})")

    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")

    result = response.json()

    # Decode base64 image data
    b64_json = result["data"][0]["b64_json"]
    image_data = base64.b64decode(b64_json)

    return image_data


def normalize_background_to_white(image_path: Path, tolerance: int = 30) -> None:
    """
    Normalize the background color to pure white by sampling edges and replacing similar colors.
    Uses flood fill from edges to avoid replacing enclosed background areas.

    Args:
        image_path: Path to the image file to process
        tolerance: Color difference threshold (0-255, higher = more aggressive)
    """
    from PIL import Image
    import numpy as np
    from collections import Counter

    print(f"  🔄 Normalizing background to white...")

    img = Image.open(image_path).convert('RGB')
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

    print(f"  Detected background color: RGB{bg_color}")

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
    result_img.save(image_path, 'PNG')

    pixels_changed = np.sum(mask)
    total_pixels = height * width
    percent_changed = (pixels_changed / total_pixels) * 100

    print(f"  ✨ Normalized {pixels_changed:,} pixels ({percent_changed:.1f}%) to white")


def process_attendee_prompts(event_id: str, user_id: str, skip_professional: bool = False, skip_interests: bool = False, remove_bg: bool = True, force: bool = False):
    """
    Process prompts for a single attendee and generate images.

    Args:
        event_id: Event ID (e.g. cohatch_afterhours)
        user_id: User ID (e.g. user_001)
        skip_professional: If True, skip generating professional visuals
        skip_interests: If True, skip generating interests illustrations
        remove_bg: If True, normalize backgrounds to pure white
        force: If True, regenerate images even if they already exist
    """
    print(f"\n{'='*70}")
    print(f"Processing: {event_id}/{user_id}")
    print(f"{'='*70}")

    # Paths
    working_dir = _get_working_dir_lazy()
    prompts_dir = working_dir / event_id / user_id / "ai_prompts"
    output_dir = working_dir / event_id / user_id / "generated_images"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process professional visual prompt
    if not skip_professional:
        prof_prompt_path = prompts_dir / "professional_visual_prompt.txt"
        output_path = output_dir / "professional_visual.png"

        if prof_prompt_path.exists():
            # Check if image already exists
            if output_path.exists() and not force:
                print(f"\n1. ⏭️  Skipping professional visual (already exists)")
                print(f"  Use --force to regenerate")
            else:
                print(f"\n1. Generating professional visual (1024x1024)...")
                prompt = prof_prompt_path.read_text(encoding="utf-8")

                try:
                    image_data = generate_image(
                        prompt=prompt,
                        size="1024x1024",
                        quality="high"
                    )

                    output_path.write_bytes(image_data)
                    print(f"  ✅ Saved: {output_path.relative_to(ROOT)}")

                    # Normalize background to white
                    if remove_bg:
                        normalize_background_to_white(output_path)

                    # Rate limiting - wait between requests
                    time.sleep(2)

                except Exception as e:
                    print(f"  ❌ Error: {e}")
    else:
        print(f"\n1. Skipping professional visual (--interests-only flag)")

    # Process interests illustration prompt
    if not skip_interests:
        interests_prompt_path = prompts_dir / "interests_illustration_prompt.txt"
        output_path = output_dir / "interests_illustration.png"

        if interests_prompt_path.exists():
            # Check if image already exists
            if output_path.exists() and not force:
                print(f"\n2. ⏭️  Skipping interests illustration (already exists)")
                print(f"  Use --force to regenerate")
            else:
                print(f"\n2. Generating interests illustration (1536x1024 horizontal)...")
                prompt = interests_prompt_path.read_text(encoding="utf-8")

                try:
                    image_data = generate_image(
                        prompt=prompt,
                        size="1536x1024",  # Horizontal format for interests
                        quality="high"
                    )

                    output_path.write_bytes(image_data)
                    print(f"  ✅ Saved: {output_path.relative_to(ROOT)}")

                    # Normalize background to white
                    if remove_bg:
                        normalize_background_to_white(output_path)

                    # Smart crop to remove dead space
                    print(f"  🔄 Smart cropping to remove dead space...")
                    crop_interests_image(
                        input_path=output_path,
                        output_path=output_path,
                        target_aspect_ratio=2.0,
                        margin_inches=0.15
                    )
                    print(f"  ✨ Cropped to maintain 2.0:1 aspect ratio")

                    # Rate limiting - wait between requests
                    time.sleep(2)

                except Exception as e:
                    print(f"  ❌ Error: {e}")
    else:
        print(f"\n2. Skipping interests illustration (--professional-only flag)")


def main():
    """Generate all images from prompts."""
    parser = argparse.ArgumentParser(description="Generate AI images using Azure OpenAI GPT Image 1")
    parser.add_argument(
        "--professional-only",
        action="store_true",
        help="Only generate professional visual images (skip interests)"
    )
    parser.add_argument(
        "--interests-only",
        action="store_true",
        help="Only generate interests illustration images (skip professional)"
    )
    parser.add_argument(
        "--event",
        help="Filter to specific event_id (e.g., cohatch_afterhours)"
    )
    parser.add_argument(
        "--no-remove-bg",
        action="store_true",
        help="Don't normalize backgrounds to white"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate images even if they already exist"
    )
    args = parser.parse_args()

    # Validate flags
    if args.professional_only and args.interests_only:
        print("❌ Error: Cannot use both --professional-only and --interests-only flags")
        return

    working_dir = _get_working_dir_lazy()

    print("="*70)
    print("Azure OpenAI Image Generator (GPT Image 1)")
    print("="*70)
    print(f"Output Directory: {working_dir.relative_to(ROOT)}")

    if args.professional_only:
        print("Mode: Professional visuals only")
    elif args.interests_only:
        print("Mode: Interests illustrations only")
    else:
        print("Mode: All images (professional + interests)")

    if args.event:
        print(f"Event filter: {args.event}")

    remove_bg = not args.no_remove_bg
    print(f"Background normalization: {'enabled' if remove_bg else 'disabled'}")

    # Find all event directories
    if not working_dir.exists():
        print("\n❌ No working directory found! Run generate_ai_prompts.py first.")
        return

    # Collect all event/user pairs to process
    attendees_to_process = []
    for event_dir in working_dir.iterdir():
        if not event_dir.is_dir():
            continue

        # Skip if event filter specified and doesn't match
        if args.event and event_dir.name != args.event:
            continue

        # Find all user directories in this event
        for user_dir in event_dir.iterdir():
            if not user_dir.is_dir():
                continue

            # Check if ai_prompts directory exists
            if (user_dir / "ai_prompts").exists():
                attendees_to_process.append((event_dir.name, user_dir.name))

    if not attendees_to_process:
        print("\n❌ No attendee prompt directories found!")
        return

    print(f"\nFound {len(attendees_to_process)} attendee(s) to process")

    # Process each attendee
    for event_id, user_id in sorted(attendees_to_process):
        try:
            process_attendee_prompts(
                event_id,
                user_id,
                skip_professional=args.interests_only,
                skip_interests=args.professional_only,
                remove_bg=remove_bg,
                force=args.force
            )
        except Exception as e:
            print(f"\n❌ Failed to process {event_id}/{user_id}: {e}")
            continue

    print("\n" + "="*70)
    print("✅ Image generation complete!")
    print(f"📁 Images saved to: {working_dir.relative_to(ROOT)}")
    print("="*70)

    print("\nNext steps:")
    print("1. Review generated images in output/working/")
    print("2. Use generate_badges.py to create final badges")


if __name__ == "__main__":
    main()
