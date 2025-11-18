#!/usr/bin/env python3
"""
Complete badge generation workflow orchestrator.
Runs: prompt generation → image generation → badge generation

Uses convention-based paths for interests images:
  output/working/{event_id}/{user_id}/generated_images/interests_illustration.png
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*70}")
    print(f"▶ {description}")
    print(f"{'='*70}")

    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        return False

    print(f"\n✅ Completed: {description}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Complete badge generation workflow"
    )
    parser.add_argument(
        "--event",
        help="Filter to specific event_id (e.g., cohatch_afterhours)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate all files even if they already exist"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Complete Badge Generation Workflow")
    print("=" * 70)

    if args.event:
        print(f"Event filter: {args.event}")
    if args.force:
        print("Mode: Force regenerate all files")
    else:
        print("Mode: Smart skip (generate only missing files)")

    # Step 1: Generate AI prompts
    # Prompts are needed for images, so we generate them when generating images
    cmd = [sys.executable, str(ROOT / "scripts" / "generate_ai_prompts.py"), "--skip-professional"]
    if args.event:
        cmd.extend(["--event", args.event])
    if not run_command(cmd, "Step 1: Generate AI prompts"):
        return 1

    # Step 2: Generate images
    # Images will skip if they exist unless --force is used
    cmd = [sys.executable, str(ROOT / "scripts" / "generate_images.py"), "--interests-only"]
    if args.event:
        cmd.extend(["--event", args.event])
    if args.force:
        cmd.append("--force")
    if not run_command(cmd, "Step 2: Generate AI images"):
        return 1

    # Step 3: Generate badges
    # Uses convention-based paths to find images
    cmd = [sys.executable, str(ROOT / "scripts" / "generate_all_badges.py")]
    if not run_command(cmd, "Step 3: Generate badges"):
        return 1

    print("\n" + "=" * 70)
    print("✅ Workflow completed successfully!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
