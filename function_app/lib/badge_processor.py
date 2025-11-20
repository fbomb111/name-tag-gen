"""
Badge Processor - Wraps the existing badge generation logic for use in Azure Functions
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any
import tempfile
import uuid

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

    def generate_badge(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a badge from form data

        Args:
            form_data: Dictionary containing attendee information from form

        Returns:
            Dictionary with:
                - pdf_bytes: Badge PDF as bytes
                - preview_image: Badge preview image as bytes (optional)
                - user_id: Generated user ID
                - attendee_name: Name from form
        """
        # Generate unique user ID
        user_id = f"user_{uuid.uuid4().hex[:8]}"

        # Parse form data into Attendee model
        attendee = self._parse_form_data(form_data, user_id)

        # Get event configuration
        event = self._load_event(form_data.get('event_id'))

        # Create EventAttendee with tag assignments
        event_attendee = self._create_event_attendee(form_data, user_id)

        # Generate AI image for interests (if provided)
        if attendee.interests or attendee.raw_interests:
            interests_image_path = self._generate_interests_image(
                attendee, event, user_id
            )
        else:
            interests_image_path = None

        # Generate badge PDF
        badge_renderer = BadgeRendererHTML(event.event_id)
        pdf_bytes = badge_renderer.render_to_bytes(event, attendee, event_attendee)

        return {
            'pdf_bytes': pdf_bytes,
            'preview_image': None,  # TODO: Generate preview if needed
            'user_id': user_id,
            'attendee_name': attendee.name
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

        events_path = Path(__file__).parent.parent.parent / "mocks" / "events.json"
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
            event_id=form_data.get('event_id'),
            user_id=user_id,
            tags=tags
        )

    def _generate_interests_image(
        self, attendee: Attendee, event: Event, user_id: str
    ) -> Path:
        """Generate AI image for attendee interests"""

        # Load template for prompt generation
        template = load_template(event.template_id)

        # Generate AI prompt
        interests_prompt = generate_interests_illustration_prompt(attendee, template)

        if not interests_prompt:
            return None

        # Generate image using Azure OpenAI
        output_dir = self.temp_dir / event.event_id / user_id / "generated_images"
        output_dir.mkdir(parents=True, exist_ok=True)

        interests_image_path = output_dir / "interests_illustration.png"

        # Call Azure OpenAI to generate image
        image_bytes = generate_image(
            prompt=interests_prompt,
            size="1536x1024",  # Horizontal format for interests illustration
            quality="medium"
        )

        # Write bytes to file
        with open(interests_image_path, 'wb') as f:
            f.write(image_bytes)

        return interests_image_path
