#!/usr/bin/env python3
"""Pre-deployment import sanity check.

Run this script before deploying to Azure to verify module paths are correct.
This validates that sys.path setup allows src/ modules to be found.
"""
import sys
import os
from pathlib import Path

# Set up path exactly as function_app.py does
HERE = Path(__file__).parent
if (HERE / "src").exists():
    sys.path.insert(0, str(HERE))

print("Validating module paths for Azure deployment...")
print(f"Working directory: {HERE}")
print(f"sys.path[0]: {sys.path[0]}")
print()

failed = False

# Check critical files exist
REQUIRED_FILES = [
    "src/utils/paths.py",
    "src/models.py",
    "lib/badge_processor.py",
    "function_app.py",
    "mocks/events.json",
    "mocks/attendees.json",
    "config/badge_templates/cohatch_networking_template.json",
]

print("Checking required files...")
for f in REQUIRED_FILES:
    path = HERE / f
    if path.exists():
        print(f"  ✓ {f}")
    else:
        print(f"  ✗ {f} - NOT FOUND")
        failed = True

print()

# Try to import the path utility (no external dependencies)
print("Validating core imports...")
try:
    from src.utils.paths import get_project_root, get_mocks_dir
    root = get_project_root()
    print(f"  ✓ src.utils.paths (project root: {root})")
except Exception as e:
    print(f"  ✗ src.utils.paths: {e}")
    failed = True

# Verify path utility returns correct paths
try:
    mocks = get_mocks_dir()
    if (mocks / "events.json").exists():
        print(f"  ✓ get_mocks_dir() resolves correctly")
    else:
        print(f"  ✗ get_mocks_dir() returned {mocks} but events.json not found there")
        failed = True
except Exception as e:
    print(f"  ✗ get_mocks_dir(): {e}")
    failed = True

print()
if failed:
    print("❌ Validation FAILED - do not deploy!")
    sys.exit(1)
else:
    print("✅ All paths validated successfully")
    sys.exit(0)
