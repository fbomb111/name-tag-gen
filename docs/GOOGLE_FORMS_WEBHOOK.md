# Google Forms to Azure Function Webhook

This document describes how to set up a Google Forms webhook to automatically trigger badge generation when someone submits the form.

## Google Apps Script Code

### Setup Instructions

1. Open your Google Form
2. Click the three dots (⋮) → **Script editor**
3. Delete any existing code
4. Paste the script below
5. Update the `AZURE_FUNCTION_URL` with your function URL
6. Save the project (name it "Badge Generation Webhook")
7. Set up trigger (see Trigger Setup section)

### Script Code

```javascript
/**
 * Badge Generation Webhook for Google Forms
 * Sends form responses to Azure Function for badge processing
 */

// Configuration
const AZURE_FUNCTION_URL = "https://func-name-tag-gen-66802.azurewebsites.net/api/process-badge";
const EVENT_ID = "cohatch_afterhours";  // Update this for each event

/**
 * Trigger function - runs when form is submitted
 */
function onFormSubmit(e) {
  try {
    // Log the submission
    Logger.log("Form submitted at: " + new Date());

    // Get form response
    const formResponse = e.response;
    const itemResponses = formResponse.getItemResponses();

    // Build payload from form responses
    const payload = buildPayload(itemResponses);

    // Send to Azure Function
    const response = sendToAzureFunction(payload);

    // Log success
    Logger.log("Badge generation triggered successfully");
    Logger.log("Response: " + response.getContentText());

  } catch (error) {
    // Log error
    Logger.log("ERROR: " + error.toString());

    // Optionally send error notification
    // sendErrorNotification(error, e);
  }
}

/**
 * Build JSON payload from form responses
 */
function buildPayload(itemResponses) {
  const payload = {
    event_id: EVENT_ID,
    tags: {}
  };

  // Map form questions to payload fields
  itemResponses.forEach(function(itemResponse) {
    const question = itemResponse.getItem().getTitle();
    const answer = itemResponse.getResponse();

    // Map questions to fields
    switch(question) {
      case "Full Name":
      case "Name":
        payload.name = answer;
        break;

      case "Email":
      case "Email Address":
        payload.email = answer;
        break;

      case "Job Title":
      case "Title":
        payload.title = answer;
        break;

      case "Company":
      case "Company Name":
      case "Organization":
        payload.company = answer;
        break;

      case "Location":
      case "City, State":
        payload.location = answer;
        break;

      case "Interests":
      case "Hobbies and Interests":
        payload.interests = answer;
        break;

      case "LinkedIn Profile":
      case "Profile URL":
        payload.profile_url = answer;
        break;

      case "Preferred Social Platform":
        payload.preferred_social_platform = answer;
        break;

      case "Social Media Handle":
        payload.social_handle = answer;
        break;

      case "Pronouns":
        payload.pronouns = answer;
        break;

      // Tag fields (customize for your event)
      case "Committee":
        payload.tags["Committee"] = answer;
        break;

      case "Years as Member":
        payload.tags["Years as Member"] = answer;
        break;

      case "Rep":
      case "Representative":
        payload.tags["Rep"] = answer;
        break;

      case "Industry":
        payload.tags["Industry"] = answer;
        break;

      case "Membership Level":
        payload.tags["Membership Level"] = answer;
        break;

      default:
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
 * Test function - use to test the webhook without submitting the form
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
    profile_url: "https://example.com/profile",
    preferred_social_platform: "linkedin",
    social_handle: "testuser",
    pronouns: "they/them",
    tags: {
      "Committee": "Innovation & Transformation Council",
      "Years as Member": "5-9 years",
      "Rep": "Test Rep",
      "Industry": "Technology",
      "Membership Level": "Corporate Plus"
    }
  };

  Logger.log("Testing webhook...");
  const response = sendToAzureFunction(testPayload);
  Logger.log("Test successful!");
  Logger.log("Response: " + response.getContentText());
}
```

## Trigger Setup

### Automatic Trigger (Recommended)

1. In Apps Script editor, click **Triggers** (clock icon)
2. Click **+ Add Trigger**
3. Configure:
   - Function: `onFormSubmit`
   - Deployment: `Head`
   - Event source: `From form`
   - Event type: `On form submit`
4. Click **Save**
5. Authorize the script (you'll be prompted to grant permissions)

### Manual Testing

Before setting up the trigger, test the webhook:

1. In Apps Script editor, select `testWebhook` function
2. Click **Run**
3. Check **Execution log** for results
4. Verify badge is generated in Azure

## Form Question Mapping

Update the `buildPayload()` function to match your exact form questions. Current mappings:

| Form Question | Payload Field | Required |
|--------------|---------------|----------|
| Full Name | `name` | Yes |
| Email | `email` | Yes |
| Job Title | `title` | Yes |
| Company | `company` | Yes |
| Location | `location` | Yes |
| Interests | `interests` | Yes |
| Profile URL | `profile_url` | No |
| Preferred Social Platform | `preferred_social_platform` | No |
| Social Media Handle | `social_handle` | No |
| Pronouns | `pronouns` | No |
| Committee | `tags.Committee` | Event-specific |
| Years as Member | `tags.Years as Member` | Event-specific |
| Rep | `tags.Rep` | Event-specific |
| Industry | `tags.Industry` | Event-specific |
| Membership Level | `tags.Membership Level` | Event-specific |

## Troubleshooting

### Check Execution Logs

1. In Apps Script editor, click **Executions** (list icon)
2. View recent runs and their status
3. Click on a run to see detailed logs

### Common Issues

**Error: "Script has no authorization"**
- Solution: Run `testWebhook()` manually first to authorize the script

**Error: "Azure Function returned status 400"**
- Solution: Check payload formatting - missing required fields?

**Error: "UrlFetchApp is not defined"**
- Solution: Make sure you're using Google Apps Script, not regular JavaScript

**Submissions not triggering webhook**
- Solution: Check trigger is set up correctly in **Triggers** tab
- Make sure trigger event type is "On form submit"

### View Logs

```javascript
function viewRecentLogs() {
  const logs = Logger.getLog();
  Logger.log(logs);
}
```

## Security Considerations

### Function Key (Optional)

For added security, you can use Azure Function's built-in authentication:

1. In Azure Portal, go to your Function App
2. Navigate to **Function → ProcessBadge → Function Keys**
3. Copy the `default` key
4. Update the webhook URL:

```javascript
const AZURE_FUNCTION_URL = "https://func-name-tag-gen-66802.azurewebsites.net/api/process-badge?code=YOUR_FUNCTION_KEY";
```

### Environment-Specific URLs

For testing vs production:

```javascript
const ENVIRONMENT = "production";  // or "dev"

const URLS = {
  dev: "http://localhost:7072/api/process-badge",
  production: "https://func-name-tag-gen-66802.azurewebsites.net/api/process-badge"
};

const AZURE_FUNCTION_URL = URLS[ENVIRONMENT];
```

## Multiple Events

If you need to handle multiple events with one script:

```javascript
// Determine event ID based on form name or custom logic
function getEventId(formResponse) {
  const formTitle = FormApp.getActiveForm().getTitle();

  if (formTitle.includes("AfterHours")) {
    return "cohatch_afterhours";
  } else if (formTitle.includes("BBQ")) {
    return "short_name_event";
  }

  return "default_event";
}

// Update onFormSubmit:
function onFormSubmit(e) {
  const formResponse = e.response;
  const eventId = getEventId(formResponse);
  // ... rest of code
}
```

## Next Steps

1. Customize question mappings for your form
2. Test with `testWebhook()` function
3. Set up trigger for automatic processing
4. Submit a test form to verify end-to-end
5. Monitor Azure Function App logs for any issues
