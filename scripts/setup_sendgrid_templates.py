#!/usr/bin/env python3
"""
SendGrid Template Creator
Creates dynamic email templates via SendGrid REST API
"""
import os
import sys
import json
import requests
from pathlib import Path


def create_sendgrid_template(api_key: str, template_name: str, html_content: str, subject: str) -> str:
    """
    Create a SendGrid dynamic template with HTML content

    Args:
        api_key: SendGrid API key
        template_name: Display name for the template
        html_content: HTML content with Handlebars variables
        subject: Email subject line (can include {{variables}})

    Returns:
        Template ID (format: d-{62 hex chars})
    """

    # Step 1: Create the template
    print(f"\n📧 Creating template: {template_name}")

    create_url = "https://api.sendgrid.com/v3/templates"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    create_payload = {
        "name": template_name,
        "generation": "dynamic"  # Dynamic templates support Handlebars
    }

    response = requests.post(create_url, headers=headers, json=create_payload)

    if response.status_code != 201:
        print(f"❌ Failed to create template: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    template_data = response.json()
    template_id = template_data['id']
    print(f"✅ Template created: {template_id}")

    # Step 2: Create a template version with HTML content
    print(f"📝 Adding HTML content to template version...")

    version_url = f"https://api.sendgrid.com/v3/templates/{template_id}/versions"

    version_payload = {
        "name": f"{template_name} - v1",
        "subject": subject,
        "html_content": html_content,
        "active": 1  # Set as active version
    }

    response = requests.post(version_url, headers=headers, json=version_payload)

    if response.status_code != 201:
        print(f"❌ Failed to create template version: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    print(f"✅ Template version created and activated")

    return template_id


def main():
    # Get API key from environment
    api_key = os.getenv('SENDGRID_API_KEY')

    if not api_key:
        print("❌ Error: SENDGRID_API_KEY environment variable not set")
        print("Please set it in your .env file or export it:")
        print("  export SENDGRID_API_KEY='your-api-key'")
        sys.exit(1)

    print("🚀 SendGrid Template Creator")
    print("=" * 60)

    # Template 1: Badge Ready Email
    badge_ready_html = """<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
      border-radius: 8px 8px 0 0;
    }
    .content {
      background: #f9fafb;
      padding: 30px;
      border-radius: 0 0 8px 8px;
    }
    .button {
      display: inline-block;
      background: #667eea;
      color: white;
      padding: 12px 30px;
      text-decoration: none;
      border-radius: 5px;
      margin: 20px 0;
    }
    .footer {
      text-align: center;
      margin-top: 30px;
      font-size: 12px;
      color: #6b7280;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🎉 Badge Ready!</h1>
  </div>
  <div class="content">
    <h2>Badge generated for {{attendee_name}}</h2>

    <p>A new badge has been generated for <strong>{{attendee_name}}</strong> for the <strong>{{event_id}}</strong> event.</p>

    {{#if preview_available}}
    <p>A preview of the badge is attached to this email.</p>
    {{/if}}

    <p>The badge PDF is attached and ready for printing.</p>

    <p><strong>Next Steps:</strong></p>
    <ul>
      <li>Download the attached PDF</li>
      <li>Print on 3" × 4" badge stock</li>
      <li>Insert into badge holder</li>
    </ul>
  </div>
  <div class="footer">
    <p>This email was sent from the automated badge generation system.</p>
    <p>🤖 Generated with Badge Generation System</p>
  </div>
</body>
</html>"""

    # Template 2: Error Notification Email
    error_notification_html = """<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      font-family: 'Courier New', monospace;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    .header {
      background: #dc2626;
      color: white;
      padding: 20px;
      border-radius: 8px 8px 0 0;
    }
    .content {
      background: #fef2f2;
      padding: 30px;
      border: 2px solid #dc2626;
      border-radius: 0 0 8px 8px;
    }
    .error-box {
      background: #fee2e2;
      border-left: 4px solid #dc2626;
      padding: 15px;
      margin: 15px 0;
      font-family: monospace;
      overflow-x: auto;
    }
    .metadata {
      background: #f3f4f6;
      padding: 15px;
      border-radius: 5px;
      margin: 15px 0;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>⚠️ Badge Generation Failed</h1>
  </div>
  <div class="content">
    <div class="metadata">
      <p><strong>Attendee:</strong> {{attendee_name}}</p>
      <p><strong>Event:</strong> {{event_id}}</p>
      <p><strong>Timestamp:</strong> {{timestamp}}</p>
    </div>

    <h2>Error Details</h2>
    <div class="error-box">
      {{error_message}}
    </div>

    <h2>Form Data</h2>
    <div class="error-box">
      <pre>{{form_data}}</pre>
    </div>

    <h2>Action Required</h2>
    <p>Please investigate this error and:</p>
    <ol>
      <li>Check Azure Function App logs</li>
      <li>Verify Azure OpenAI API status</li>
      <li>Review form data for validation issues</li>
      <li>Manually retry if needed</li>
    </ol>
  </div>
</body>
</html>"""

    # Create both templates
    badge_ready_id = create_sendgrid_template(
        api_key=api_key,
        template_name="Badge Ready - Production",
        html_content=badge_ready_html,
        subject="Badge Ready: {{attendee_name}}"
    )

    error_notification_id = create_sendgrid_template(
        api_key=api_key,
        template_name="Badge Generation Error - Production",
        html_content=error_notification_html,
        subject="Badge Generation Error - {{attendee_name}}"
    )

    # Display results
    print("\n" + "=" * 60)
    print("✅ All templates created successfully!")
    print("=" * 60)
    print("\n📋 Template IDs:\n")
    print(f"SENDGRID_TEMPLATE_ID_BADGE_READY={badge_ready_id}")
    print(f"SENDGRID_TEMPLATE_ID_ERROR={error_notification_id}")

    print("\n💡 Next Steps:\n")
    print("1. Update function_app/local.settings.json with these template IDs")
    print("2. Update Azure Function App settings:")
    print(f"\n   az functionapp config appsettings set \\")
    print(f"     --name func-name-tag-gen-66802 \\")
    print(f"     --resource-group rg-name-tag-gen \\")
    print(f"     --settings \\")
    print(f"       SENDGRID_TEMPLATE_ID_BADGE_READY={badge_ready_id} \\")
    print(f"       SENDGRID_TEMPLATE_ID_ERROR={error_notification_id}")

    print("\n3. Test with: python scripts/test_sendgrid_email.py\n")


if __name__ == '__main__':
    main()
