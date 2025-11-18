#!/usr/bin/env python3
"""Create simple PNG event logos for hosting organizations."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGOS_DIR = ROOT / "assets" / "event_logos"
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

def create_ohio_business_meetup_logo():
    """Create AfterHours at COHATCH logo (professional event - navy/gold theme)."""
    img = Image.new('RGB', (400, 400), color='#3D405B')
    draw = ImageDraw.Draw(img)

    # Draw Ohio state outline (simplified) with business symbols
    # Draw a handshake symbol
    draw.ellipse([100, 180, 150, 230], fill='#F2CC8F')
    draw.ellipse([250, 180, 300, 230], fill='#F2CC8F')
    draw.rectangle([145, 190, 255, 220], fill='#F2CC8F')

    # Draw company name
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text1 = "OHIO"
    bbox1 = draw.textbbox((0, 0), text1, font=font_large)
    text1_width = bbox1[2] - bbox1[0]
    draw.text(((400 - text1_width) / 2, 260), text1, fill='white', font=font_large)

    text2 = "Small Business"
    bbox2 = draw.textbbox((0, 0), text2, font=font_small)
    text2_width = bbox2[2] - bbox2[0]
    draw.text(((400 - text2_width) / 2, 310), text2, fill='#F2CC8F', font=font_small)

    text3 = "MEETUP"
    bbox3 = draw.textbbox((0, 0), text3, font=font_small)
    text3_width = bbox3[2] - bbox3[0]
    draw.text(((400 - text3_width) / 2, 350), text3, fill='white', font=font_small)

    img.save(LOGOS_DIR / "ohio_business_meetup.png")
    print(f"✅ Created ohio_business_meetup.png")


def create_spring_block_party_logo():
    """Create Spring Block Party logo (neighborhood event - coral/teal theme)."""
    img = Image.new('RGB', (400, 400), color='#FF6B6B')
    draw = ImageDraw.Draw(img)

    # Draw party/celebration symbols
    # Draw houses
    draw.polygon([(100, 140), (160, 80), (220, 140)], fill='#4ECDC4')
    draw.rectangle([120, 140, 200, 200], fill='#4ECDC4')
    draw.rectangle([135, 155, 155, 175], fill='#FF6B6B')
    draw.rectangle([165, 155, 185, 175], fill='#FF6B6B')

    # Draw a sun/celebration symbol
    draw.ellipse([260, 100, 320, 160], fill='#FFB347')

    # Draw confetti dots
    colors = ['#9B59B6', '#4ECDC4', '#FFB347', '#F0FFF4']
    positions = [(80, 220), (180, 230), (280, 210), (320, 240)]
    for pos, color in zip(positions, colors):
        draw.ellipse([pos[0], pos[1], pos[0]+20, pos[1]+20], fill=color)

    # Draw text
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text1 = "SPRING"
    bbox1 = draw.textbbox((0, 0), text1, font=font_large)
    text1_width = bbox1[2] - bbox1[0]
    draw.text(((400 - text1_width) / 2, 270), text1, fill='white', font=font_large)

    text2 = "Block Party"
    bbox2 = draw.textbbox((0, 0), text2, font=font_small)
    text2_width = bbox2[2] - bbox2[0]
    draw.text(((400 - text2_width) / 2, 330), text2, fill='#4ECDC4', font=font_small)

    img.save(LOGOS_DIR / "spring_block_party.png")
    print(f"✅ Created spring_block_party.png")


if __name__ == "__main__":
    print("Creating event logos for hosting organizations...")
    create_ohio_business_meetup_logo()
    create_spring_block_party_logo()
    print("\n✅ All event logos created successfully!")
