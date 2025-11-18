"""
Test script for location_renderer module.
"""
from pathlib import Path
from location_renderer import render_location_graphic

# Test locations
test_locations = [
    "Dayton, Ohio",
    "Columbus, Ohio",
    "Paris, France",
    "Toronto, Ontario, Canada",
    "New York, NY"
]

# Output directory
output_dir = Path("output/location_tests")
output_dir.mkdir(parents=True, exist_ok=True)

print("Testing location renderer...")
print("=" * 60)

for location in test_locations:
    print(f"\nTesting: {location}")
    output_file = output_dir / f"{location.replace(', ', '_').replace(' ', '_')}.svg"

    result = render_location_graphic(
        location_str=location,
        output_path=output_file,
        canvas_size=(144, 144)  # 0.5in at 288 DPI
    )

    if result:
        print(f"  ✓ Generated: {output_file}")
    else:
        print(f"  ✗ Failed to generate graphic")

print("\n" + "=" * 60)
print("Test complete!")
