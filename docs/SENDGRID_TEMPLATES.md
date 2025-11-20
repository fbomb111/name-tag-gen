# SendGrid Email Templates

This document describes the Send Grid dynamic templates needed for the badge generation system.

## Template 1: Badge Ready Email

**Purpose:** Sent to event organizer when a badge is generated (demo mode)

**Template ID Variable:** `SENDGRID_TEMPLATE_ID_BADGE_READY`

### Dynamic Template Data

```json
{
  "attendee_name": "John Doe",
  "event_id": "cohatch_afterhours",
  "preview_available": true
}
```

### Email Design

**Subject:** Badge Ready: {{attendee_name}}

**HTML Body:**
```html
<!DOCTYPE html>
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
</html>
```

## Template 2: Error Notification Email

**Purpose:** Sent to support team when badge generation fails

**Template ID Variable:** `SENDGRID_TEMPLATE_ID_ERROR`

### Dynamic Template Data

```json
{
  "error_message": "API request failed with status 500",
  "form_data": "{ ... full form data ... }",
  "attendee_name": "John Doe",
  "event_id": "cohatch_afterhours"
}
```

### Email Design

**Subject:** Badge Generation Error - {{attendee_name}}

**HTML Body:**
```html
<!DOCTYPE html>
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
</html>
```

## Setup Instructions

### 1. Create Templates in SendGrid

1. Log in to SendGrid Dashboard
2. Navigate to **Email API → Dynamic Templates**
3. Click **Create a Dynamic Template**
4. Name it: "Badge Ready - Production"
5. Click **Add Version**
6. Select **Blank Template**
7. Switch to **Code Editor**
8. Paste the HTML from above
9. Save and note the Template ID

### 2. Add Template IDs to Environment

**Local (function_app/local.settings.json):**
```json
{
  "SENDGRID_TEMPLATE_ID_BADGE_READY": "d-abc123...",
  "SENDGRID_TEMPLATE_ID_ERROR": "d-def456..."
}
```

**Azure (via CLI):**
```bash
az functionapp config appsettings set \
  --name func-name-tag-gen-66802 \
  --resource-group rg-name-tag-gen \
  --settings \
    SENDGRID_TEMPLATE_ID_BADGE_READY=d-abc123... \
    SENDGRID_TEMPLATE_ID_ERROR=d-def456...
```

### 3. Test Templates

Use SendGrid's **Test Data** feature to preview:

```json
{
  "attendee_name": "Test User",
  "event_id": "test_event",
  "preview_available": true
}
```

## Notes

- Templates use Handlebars syntax (`{{variable}}`, `{{#if}}...{{/if}}`)
- Attachments are added programmatically by the email_client.py
- Templates should be versioned (keep old versions for rollback)
- Test thoroughly before using in production
