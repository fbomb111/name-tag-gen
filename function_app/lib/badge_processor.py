"""
Badge Processor - Wraps the existing badge generation logic for use in Azure Functions
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any
import tempfile
import uuid

# Add function_app (or wwwroot in Azure) to path for imports
# This allows importing from src/ which is synced to function_app/src/
_function_dir = Path(__file__).parent.parent  # function_app/ or /home/site/wwwroot/
if (_function_dir / "src").exists():
    sys.path.insert(0, str(_function_dir))
else:
    # Local dev fallback - src/ is in project root
    sys.path.insert(0, str(_function_dir.parent))

from src.utils.paths import get_mocks_dir, get_working_dir
from src.models import Event, Attendee, EventAttendee
from src.renderers.badge_renderer_html import BadgeRendererHTML
from scripts.generate_ai_prompts import (
    generate_interests_illustration_prompt,
    load_template
)
from scripts.generate_images import generate_image


class BadgeProcessor:
    """Processes badge generation requests from form submissions"""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "badge_generation"
        self.temp_dir.mkdir(exist_ok=True)

    def generate_badge(self, form_data: Dict[str, Any], force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Generate a badge from form data

        Args:
            form_data: Dictionary containing attendee information from form
            force_regenerate: If True, regenerate AI image even if cached

        Returns:
            Dictionary with:
                - pdf_bytes: Badge PDF as bytes
                - preview_image: Badge preview image as bytes (optional)
                - user_id: Generated user ID
                - attendee_name: Name from form
        """
        import logging

        # Generate unique user ID
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        logging.info(f"[1/4] Generated user ID: {user_id}")

        # Parse form data into Attendee model
        attendee = self._parse_form_data(form_data, user_id)
        logging.info(f"[2/4] Parsed attendee data for: {attendee.name}")

        # Get event configuration
        event = self._load_event(form_data.get('event_id'))
        logging.info(f"[2/4] Loaded event: {event.display_name}")

        # Create EventAttendee with tag assignments
        event_attendee = self._create_event_attendee(form_data, user_id)
        logging.info(f"[2/4] Created event attendee with {len(event_attendee.tags)} tags")

        # Generate AI image for interests (if provided)
        if attendee.interests or attendee.raw_interests:
            logging.info(f"[3/4] Starting AI image generation...")
            interests_image_path = self._generate_interests_image(
                attendee, event, user_id, force=force_regenerate
            )
            logging.info(f"[3/4] ✓ AI image generated successfully")
        else:
            interests_image_path = None
            logging.info(f"[3/4] No interests provided, skipping AI image generation")

        # Generate badge PDF
        logging.info(f"[4/4] Rendering badge PDF...")

        # Determine if we're running in deployed function or local dev
        function_dir = Path(__file__).parent.parent  # function_app/
        project_root = function_dir.parent  # name-tag-gen/

        # For deployed function, look in function_app/config
        # For local dev, look in project root config
        if (function_dir / "config").exists():
            template_dir = function_dir / "config" / "html_templates" / "professional"
            assets_dir = function_dir
        else:
            template_dir = project_root / "config" / "html_templates" / "professional"
            assets_dir = project_root

        # Resolve logo paths - check function_app first (deployed), then project root (local)
        def resolve_logo_path(relative_path: str) -> str:
            if not relative_path:
                return None
            # Try function_app location (deployed)
            deployed_path = function_dir / relative_path
            if deployed_path.exists():
                return str(deployed_path)
            # Fall back to project root (local dev)
            local_path = project_root / relative_path
            if local_path.exists():
                return str(local_path)
            logging.warning(f"Logo not found: {relative_path}")
            return None

        event_logo_absolute = resolve_logo_path(event.logo_path)
        sponsor_logo_absolute = resolve_logo_path(event.sponsor_logo_path)

        badge_renderer = BadgeRendererHTML(
            template_dir=template_dir,
            event_id=event.event_id,
            event_name=event.display_name,
            event_date=event.date,
            sponsor=event.sponsor,
            event_logo_path=event_logo_absolute,
            sponsor_logo_path=sponsor_logo_absolute,
            tags=event.tags
        )
        pdf_bytes = badge_renderer.render_to_bytes(event, attendee, event_attendee)
        logging.info(f"[4/4] ✓ Badge PDF rendered ({len(pdf_bytes)} bytes)")

        return {
            'pdf_bytes': pdf_bytes,
            'preview_image': None,  # TODO: Generate preview if needed
            'user_id': user_id,
            'attendee_name': attendee.name,
            'event_name': event.display_name
        }

    def _parse_form_data(self, form_data: Dict[str, Any], user_id: str) -> Attendee:
        """Convert form data to Attendee model"""

        # Parse interests from comma-separated string or list
        raw_interests = form_data.get('interests', '')
        if isinstance(raw_interests, str):
            interests = [i.strip() for i in raw_interests.split(',') if i.strip()]
        else:
            interests = raw_interests

        return Attendee(
            id=user_id,
            name=form_data.get('name', ''),
            title=form_data.get('title'),
            company=form_data.get('company'),
            location=form_data.get('location'),
            profile_url=form_data.get('profile_url'),
            preferred_social_platform=form_data.get('preferred_social_platform'),
            social_handle=form_data.get('social_handle'),
            pronouns=form_data.get('pronouns'),
            raw_interests=raw_interests,
            interests=interests,
            interests_normalized=interests,  # TODO: Add normalization logic if needed
            testing_notes=[]
        )

    def _load_event(self, event_id: str) -> Event:
        """Load event configuration from JSON file"""
        import json

        events_path = get_mocks_dir() / "events.json"
        with open(events_path, 'r') as f:
            events = json.load(f)

        for event_data in events:
            if event_data['event_id'] == event_id:
                return Event(**event_data)

        raise ValueError(f"Event not found: {event_id}")

    def _create_event_attendee(
        self, form_data: Dict[str, Any], user_id: str
    ) -> EventAttendee:
        """Create EventAttendee from form data with tag assignments"""

        # Extract tag assignments from form data
        # Assuming tags are passed as a dictionary like:
        # {"Committee": "Innovation & Transformation", "Years": "5-9 years", ...}
        tags = form_data.get('tags', {})

        return EventAttendee(
            user_id=user_id,
            tags=tags
        )

    def _generate_interests_image(
        self, attendee: Attendee, event: Event, user_id: str, force: bool = False
    ) -> Path:
        """Generate AI image for attendee interests"""
        import logging

        # For local development, save to project's output/working directory
        # so the badge renderer can find the image using its convention-based path.
        # NOTE: In production Azure Functions, we'll need to refactor to:
        # 1. Generate image bytes in memory
        # 2. Upload to Azure Blob Storage
        # 3. Pass URL/bytes to renderer instead of relying on local filesystem
        output_dir = get_working_dir(event.event_id, user_id) / "generated_images"
        output_dir.mkdir(parents=True, exist_ok=True)

        interests_image_path = output_dir / "interests_illustration.png"

        # Check if image already exists (skip if not forcing)
        if interests_image_path.exists() and not force:
            logging.info(f"Using cached interests image: {interests_image_path}")
            return interests_image_path

        # Load template for prompt generation
        template = load_template(event.template_id)

        # Generate AI prompt
        interests_prompt = generate_interests_illustration_prompt(attendee, template)

        if not interests_prompt:
            return None

        logging.info(f"Generating new interests image for {attendee.name}")

        # Call Azure OpenAI to generate image
        image_bytes = generate_image(
            prompt=interests_prompt,
            size="1536x1024",  # Horizontal format for interests illustration
            quality="medium"
        )

        # Write bytes to file
        with open(interests_image_path, 'wb') as f:
            f.write(image_bytes)

        logging.info(f"Interests image saved to: {interests_image_path}")

        return interests_image_path
