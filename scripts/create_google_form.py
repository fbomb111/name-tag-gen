#!/usr/bin/env python3
"""
Google Form Creator for Badge Generation
Creates a pre-configured Google Form with all required fields for badge generation.

Prerequisites:
1. Create a Google Cloud project at https://console.cloud.google.com/
2. Enable Google Forms API: https://console.cloud.google.com/apis/library/forms.googleapis.com
3. Create OAuth 2.0 credentials (Desktop App type)
4. Download credentials.json to this directory

Usage:
    python scripts/create_google_form.py

The script will:
1. Open browser for Google OAuth authentication (first time only)
2. Create a new Google Form with all badge fields
3. Output the form URL and Apps Script code
"""
import os
import sys
import json
from pathlib import Path

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ Missing Google API dependencies. Install with:")
    print("   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# OAuth scopes needed for Forms API
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive.file'
]

# Form configuration
FORM_TITLE = "Event Badge Registration"
FORM_DESCRIPTION = """Register for your personalized event badge!

Your badge will include:
- Your name and professional info
- AI-generated illustration based on your interests
- QR code linking to your profile

Please fill out all required fields below."""

# Questions to create (in order)
QUESTIONS = [
    {
        "title": "Full Name",
        "description": "Your name as it should appear on the badge",
        "type": "TEXT",
        "required": True,
        "payload_field": "name"
    },
    {
        "title": "Email Address",
        "description": "We'll send your badge to this email",
        "type": "TEXT",
        "required": True,
        "payload_field": "email"
    },
    {
        "title": "Job Title",
        "description": "Your current role or position",
        "type": "TEXT",
        "required": True,
        "payload_field": "title"
    },
    {
        "title": "Company",
        "description": "Your company or organization name",
        "type": "TEXT",
        "required": True,
        "payload_field": "company"
    },
    {
        "title": "Location",
        "description": "City, State (e.g., Columbus, OH)",
        "type": "TEXT",
        "required": True,
        "payload_field": "location"
    },
    {
        "title": "Interests",
        "description": "List 3-5 hobbies or interests (comma-separated). These will be illustrated on your badge!",
        "type": "PARAGRAPH",
        "required": True,
        "payload_field": "interests"
    },
    {
        "title": "LinkedIn Profile URL",
        "description": "Your LinkedIn profile link (for QR code on badge)",
        "type": "TEXT",
        "required": False,
        "payload_field": "profile_url"
    },
    {
        "title": "Pronouns",
        "description": "Optional: Your preferred pronouns (e.g., she/her, he/him, they/them)",
        "type": "TEXT",
        "required": False,
        "payload_field": "pronouns"
    },
    {
        "title": "Preferred Social Platform",
        "description": "Which platform should we link to?",
        "type": "DROPDOWN",
        "required": False,
        "payload_field": "preferred_social_platform",
        "options": ["LinkedIn", "Twitter/X", "Instagram", "GitHub", "Other"]
    },
    {
        "title": "Social Media Handle",
        "description": "Your handle/username on the selected platform",
        "type": "TEXT",
        "required": False,
        "payload_field": "social_handle"
    },
    # Event-specific tag questions (for cohatch_afterhours)
    {
        "title": "Committee",
        "description": "Which committee are you part of?",
        "type": "DROPDOWN",
        "required": False,
        "payload_field": "tags.Committee",
        "options": [
            "Innovation & Transformation Council",
            "Workforce Development Council",
            "Small Business Council",
            "Young Professionals Council",
            "Government Affairs Council",
            "Diversity & Inclusion Council",
            "None"
        ]
    },
    {
        "title": "Years as Member",
        "description": "How long have you been a member?",
        "type": "DROPDOWN",
        "required": False,
        "payload_field": "tags.Years as Member",
        "options": [
            "Less than 1 year",
            "1-4 years",
            "5-9 years",
            "10+ years"
        ]
    },
    {
        "title": "Industry",
        "description": "Your primary industry",
        "type": "DROPDOWN",
        "required": False,
        "payload_field": "tags.Industry",
        "options": [
            "Technology",
            "Healthcare",
            "Finance",
            "Manufacturing",
            "Education",
            "Professional Services",
            "Retail",
            "Real Estate",
            "Non-Profit",
            "Government",
            "Other"
        ]
    },
    {
        "title": "Membership Level",
        "description": "Your membership tier",
        "type": "DROPDOWN",
        "required": False,
        "payload_field": "tags.Membership Level",
        "options": [
            "Individual",
            "Small Business",
            "Corporate",
            "Corporate Plus",
            "Premier"
        ]
    }
]


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None
    token_path = Path(__file__).parent / 'token.json'
    credentials_path = Path(__file__).parent / 'credentials.json'

    # Check for existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing OAuth token...")
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                print("❌ credentials.json not found!")
                print("\nTo create credentials:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop App type)")
                print("3. Download and save as: scripts/credentials.json")
                sys.exit(1)

            print("🌐 Opening browser for Google authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print("✅ Credentials saved to token.json")

    return creds


def create_form(service):
    """Create a new Google Form with all questions."""
    print(f"\n📝 Creating form: {FORM_TITLE}")

    # Create empty form
    form = {
        "info": {
            "title": FORM_TITLE,
            "documentTitle": FORM_TITLE
        }
    }

    result = service.forms().create(body=form).execute()
    form_id = result['formId']
    print(f"✅ Form created: {form_id}")

    # Build batch update request for description and questions
    requests = []

    # Add description
    requests.append({
        "updateFormInfo": {
            "info": {
                "description": FORM_DESCRIPTION
            },
            "updateMask": "description"
        }
    })

    # Add questions
    for i, q in enumerate(QUESTIONS):
        question_item = {
            "createItem": {
                "item": {
                    "title": q["title"],
                    "description": q.get("description", ""),
                    "questionItem": {
                        "question": {
                            "required": q.get("required", False)
                        }
                    }
                },
                "location": {"index": i}
            }
        }

        # Set question type
        if q["type"] == "TEXT":
            question_item["createItem"]["item"]["questionItem"]["question"]["textQuestion"] = {
                "paragraph": False
            }
        elif q["type"] == "PARAGRAPH":
            question_item["createItem"]["item"]["questionItem"]["question"]["textQuestion"] = {
                "paragraph": True
            }
        elif q["type"] == "DROPDOWN":
            question_item["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"] = {
                "type": "DROP_DOWN",
                "options": [{"value": opt} for opt in q.get("options", [])]
            }

        requests.append(question_item)

    # Execute batch update
    print(f"📋 Adding {len(QUESTIONS)} questions...")

    batch_update = {"requests": requests}
    service.forms().batchUpdate(formId=form_id, body=batch_update).execute()

    print("✅ All questions added")

    return form_id


def get_form_questions(service, form_id):
    """Get the created form with question IDs."""
    form = service.forms().get(formId=form_id).execute()
    return form


def generate_apps_script(form_id, questions_map):
    """Generate customized Apps Script code with question mappings."""

    script = f'''/**
 * Badge Generation Webhook for Google Forms
 * Auto-generated by create_google_form.py
 *
 * Form ID: {form_id}
 */

// Configuration
const AZURE_FUNCTION_URL = "https://func-name-tag-gen-66802.azurewebsites.net/api/process-badge";
const EVENT_ID = "cohatch_afterhours";  // Update this for each event

/**
 * Trigger function - runs when form is submitted
 */
function onFormSubmit(e) {{
  try {{
    Logger.log("Form submitted at: " + new Date());

    const formResponse = e.response;
    const itemResponses = formResponse.getItemResponses();

    const payload = buildPayload(itemResponses);
    const response = sendToAzureFunction(payload);

    Logger.log("Badge generation triggered successfully");
    Logger.log("Response: " + response.getContentText());

  }} catch (error) {{
    Logger.log("ERROR: " + error.toString());
  }}
}}

/**
 * Build JSON payload from form responses
 * Question mappings auto-generated based on form structure
 */
function buildPayload(itemResponses) {{
  const payload = {{
    event_id: EVENT_ID,
    tags: {{}}
  }};

  itemResponses.forEach(function(itemResponse) {{
    const question = itemResponse.getItem().getTitle();
    const answer = itemResponse.getResponse();

    switch(question) {{
'''

    # Add case statements for each question
    for q in QUESTIONS:
        field = q["payload_field"]
        title = q["title"]

        if field.startswith("tags."):
            tag_name = field.replace("tags.", "")
            script += f'''      case "{title}":
        payload.tags["{tag_name}"] = answer;
        break;

'''
        else:
            script += f'''      case "{title}":
        payload.{field} = answer;
        break;

'''

    script += '''      default:
        Logger.log("Unmapped question: " + question);
    }
  });

  return payload;
}

/**
 * Send payload to Azure Function
 */
function sendToAzureFunction(payload) {
  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  Logger.log("Sending to: " + AZURE_FUNCTION_URL);
  Logger.log("Payload: " + JSON.stringify(payload, null, 2));

  const response = UrlFetchApp.fetch(AZURE_FUNCTION_URL, options);
  const statusCode = response.getResponseCode();

  if (statusCode !== 200) {
    throw new Error("Azure Function returned status " + statusCode + ": " + response.getContentText());
  }

  return response;
}

/**
 * Test function - use to test without submitting form
 */
function testWebhook() {
  const testPayload = {
    event_id: EVENT_ID,
    name: "Test User",
    email: "test@example.com",
    title: "Software Engineer",
    company: "Test Corp",
    location: "Columbus, OH",
    interests: "coding, hiking, photography",
    profile_url: "https://linkedin.com/in/testuser",
    pronouns: "they/them",
    preferred_social_platform: "LinkedIn",
    social_handle: "testuser",
    tags: {
      "Committee": "Innovation & Transformation Council",
      "Years as Member": "5-9 years",
      "Industry": "Technology",
      "Membership Level": "Corporate Plus"
    }
  };

  Logger.log("Testing webhook...");
  const response = sendToAzureFunction(testPayload);
  Logger.log("Test successful!");
  Logger.log("Response: " + response.getContentText());
}
'''

    return script


def main():
    print("🚀 Google Form Creator for Badge Generation")
    print("=" * 60)

    # Get credentials
    creds = get_credentials()

    # Build Forms API service
    try:
        service = build('forms', 'v1', credentials=creds)
    except HttpError as error:
        print(f"❌ API Error: {error}")
        sys.exit(1)

    # Create form
    form_id = create_form(service)

    # Get form with question IDs
    form = get_form_questions(service, form_id)

    # Build question map
    questions_map = {}
    if 'items' in form:
        for item in form['items']:
            if 'questionItem' in item:
                questions_map[item['title']] = item['itemId']

    # Generate Apps Script
    apps_script = generate_apps_script(form_id, questions_map)

    # Save Apps Script to file
    script_path = Path(__file__).parent.parent / 'output' / 'google_form_webhook.js'
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, 'w') as f:
        f.write(apps_script)

    # Output results
    form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    response_url = f"https://docs.google.com/forms/d/{form_id}/viewform"

    print("\n" + "=" * 60)
    print("✅ Form created successfully!")
    print("=" * 60)

    print(f"\n📝 Form URLs:")
    print(f"   Edit form:    {form_url}")
    print(f"   Response URL: {response_url}")

    print(f"\n📋 Apps Script saved to:")
    print(f"   {script_path}")

    print("\n" + "=" * 60)
    print("🔧 NEXT STEPS - Set up the webhook trigger:")
    print("=" * 60)
    print("""
1. Open the form in edit mode:
   """ + form_url + """

2. Click the three dots (⋮) → Script editor

3. Delete any existing code

4. Copy and paste the contents of:
   """ + str(script_path) + """

5. Save the project (name it "Badge Generation Webhook")

6. Set up trigger:
   - Click Triggers (clock icon) in left sidebar
   - Click "+ Add Trigger"
   - Function: onFormSubmit
   - Event source: From form
   - Event type: On form submit
   - Click Save

7. Authorize the script when prompted

8. Test by running testWebhook() function first

9. Submit a test form to verify end-to-end!
""")


if __name__ == '__main__':
    main()
