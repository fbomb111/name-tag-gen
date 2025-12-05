#!/usr/bin/env python3
"""Standalone test for SendGrid email sending."""
import os
import sys
import base64
from pathlib import Path

# Load env vars from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"')

api_key = os.getenv('SENDGRID_API_KEY')
from_email = os.getenv('SENDGRID_FROM_EMAIL')
template_id = os.getenv('SENDGRID_TEMPLATE_ID_BADGE_READY')

print(f"API Key: {api_key[:20]}..." if api_key else "API Key: NOT SET")
print(f"From Email: {from_email}")
print(f"Template ID: {template_id}")
print()

if not api_key:
    print("ERROR: SENDGRID_API_KEY not set")
    sys.exit(1)

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

sg = SendGridAPIClient(api_key)

# Create a simple test PDF
test_pdf = b"%PDF-1.4 test content - this is a placeholder"

to_email = "frankie@codewithcaptain.com"

message = Mail(
    from_email=from_email,
    to_emails=to_email
)

# Use template
if template_id:
    print(f"Using template: {template_id}")
    message.template_id = template_id
    message.dynamic_template_data = {
        'attendee_name': 'Test User',
        'event_id': 'test_event',
        'preview_available': False
    }
else:
    print("No template - using plain text")
    message.subject = "Test Badge Email"
    message.plain_text_content = "This is a test email from the badge system."

# Attach PDF
pdf_attachment = Attachment()
pdf_attachment.file_content = FileContent(base64.b64encode(test_pdf).decode())
pdf_attachment.file_name = FileName("test_badge.pdf")
pdf_attachment.file_type = FileType('application/pdf')
pdf_attachment.disposition = Disposition('attachment')
message.attachment = [pdf_attachment]

print(f"Sending test email to: {to_email}")
print()

try:
    response = sg.send(message)
    print(f"✓ Status Code: {response.status_code}")
    print(f"✓ Response Body: {response.body}")
    if response.status_code in (200, 202):
        print(f"\n✅ Email sent successfully to {to_email}")
    else:
        print(f"\n⚠️ Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
