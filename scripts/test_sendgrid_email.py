#!/usr/bin/env python3
"""
SendGrid Email Tester
Sends test email with badge PDF attachment using dynamic template
"""
import os
import sys
import base64
import json
from pathlib import Path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId
)


def send_test_email(
    to_email: str,
    badge_pdf_path: Path,
    attendee_name: str = "Test User",
    event_id: str = "cohatch_afterhours"
):
    """
    Send test email with badge PDF attachment

    Args:
        to_email: Recipient email address
        badge_pdf_path: Path to badge PDF file
        attendee_name: Name for template data
        event_id: Event ID for template data
    """

    # Get configuration from environment
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL', 'frankie@codewithcaptain.com')
    from_name = os.getenv('SENDGRID_FROM_NAME', 'Badge Generation System')
    template_id = os.getenv('SENDGRID_TEMPLATE_ID_BADGE_READY')

    if not api_key:
        print("❌ Error: SENDGRID_API_KEY environment variable not set")
        sys.exit(1)

    if not template_id or template_id == "d-xxxxxxxxxxxxx":
        print("❌ Error: SENDGRID_TEMPLATE_ID_BADGE_READY not configured")
        print("Run: python scripts/setup_sendgrid_templates.py")
        sys.exit(1)

    if not badge_pdf_path.exists():
        print(f"❌ Error: Badge PDF not found: {badge_pdf_path}")
        sys.exit(1)

    print("📧 SendGrid Email Test")
    print("=" * 60)
    print(f"To: {to_email}")
    print(f"From: {from_name} <{from_email}>")
    print(f"Template: {template_id}")
    print(f"Attachment: {badge_pdf_path.name}")
    print("=" * 60)

    # Create email message
    message = Mail(
        from_email=(from_email, from_name),
        to_emails=to_email
    )

    # Set dynamic template
    message.template_id = template_id

    # Add dynamic template data
    message.dynamic_template_data = {
        'attendee_name': attendee_name,
        'event_id': event_id,
        'preview_available': True
    }

    # Attach badge PDF
    print(f"\n📎 Attaching badge PDF ({badge_pdf_path.stat().st_size / 1024:.1f} KB)...")

    with open(badge_pdf_path, 'rb') as f:
        pdf_data = f.read()

    encoded_file = base64.b64encode(pdf_data).decode()

    attachment = Attachment(
        FileContent(encoded_file),
        FileName(f"{attendee_name.replace(' ', '_')}_badge.pdf"),
        FileType('application/pdf'),
        Disposition('attachment')
    )

    message.attachment = attachment

    # Send email
    try:
        sg = SendGridAPIClient(api_key)
        print(f"\n📤 Sending email...")

        response = sg.send(message)

        print(f"✅ Email sent successfully!")
        print(f"Status Code: {response.status_code}")
        print(f"Message ID: {response.headers.get('X-Message-Id', 'N/A')}")

        if response.status_code == 202:
            print(f"\n💡 Email accepted for delivery")
            print(f"Check {to_email} inbox in a few seconds")
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.body}")

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        sys.exit(1)


def main():
    # Configuration
    to_email = "frankievcleary@gmail.com"
    attendee_name = "Test User"
    event_id = "cohatch_afterhours"

    # Find a badge PDF to attach
    badge_dir = Path("output/badges")

    # Look for any badge PDF
    badge_pdfs = list(badge_dir.glob("*/*.pdf"))

    if not badge_pdfs:
        print("❌ No badge PDFs found in output/badges/")
        print("Run: python scripts/generate_all.py")
        sys.exit(1)

    # Use the first badge PDF found
    badge_pdf_path = badge_pdfs[0]

    print(f"\n🎫 Using badge: {badge_pdf_path}")

    # Load environment variables from local.settings.json
    local_settings_path = Path("function_app/local.settings.json")
    if local_settings_path.exists():
        with open(local_settings_path, 'r') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                if key not in os.environ:
                    os.environ[key] = value

    # Send test email
    send_test_email(
        to_email=to_email,
        badge_pdf_path=badge_pdf_path,
        attendee_name=attendee_name,
        event_id=event_id
    )


if __name__ == '__main__':
    main()
