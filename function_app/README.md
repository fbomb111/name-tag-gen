# Azure Function App - Badge Generation

This directory contains the Azure Function App for automated badge generation from form submissions.

## Architecture

```
Google Forms → Azure Function (HTTP trigger) → Badge PDF
                                              ↓
                                    Demo Mode: Email to organizer
                                    Batch Mode: Save to Blob Storage
```

## Local Development Setup

### Prerequisites

1. **Azure Functions Core Tools** (v4):
   ```bash
   brew install azure-functions-core-tools@4
   ```

2. **Python 3.11**:
   ```bash
   python --version  # Should be 3.11.x
   ```

3. **Dependencies**:
   ```bash
   pip install -r ../requirements.txt
   ```

### Configuration

1. Copy configuration template:
   ```bash
   cp local.settings.json.example local.settings.json
   ```

2. Fill in your credentials in `local.settings.json`:
   - Azure OpenAI endpoint and API key
   - SendGrid API key
   - Azure Storage connection string
   - Event organizer email

### Running Locally

#### Option 1: Using Azure Functions Core Tools

```bash
cd function_app
func start --port 7072 --python-debugger-port 9092
```

The function will be available at: `http://localhost:7072/api/process-badge`

**Note:** Using custom ports (7072/9092) to avoid conflicts with other function apps.

#### Option 2: Using VS Code

1. Open the workspace in VS Code
2. Press `F5` or select "Azure Functions: Attach" from the debug menu
3. The function will start automatically

### Testing the Function

Send a POST request to the local endpoint:

```bash
curl -X POST http://localhost:7071/api/process-badge \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "cohatch_afterhours",
    "name": "Test User",
    "email": "test@example.com",
    "title": "Software Engineer",
    "company": "Test Corp",
    "location": "Columbus, OH",
    "interests": "coding, hiking, photography",
    "profile_url": "https://example.com/profile",
    "preferred_social_platform": "linkedin",
    "social_handle": "testuser",
    "pronouns": "they/them",
    "tags": {
      "Committee": "Innovation",
      "Years as Member": "1-2 years",
      "Rep": "Test Rep",
      "Industry": "Technology",
      "Membership Level": "Plus"
    }
  }'
```

## Processing Modes

### Demo Mode (`PROCESSING_MODE=demo`)

- Badge generated and **emailed immediately** to event organizer
- Shows the "wow factor" of real-time badge generation
- Email includes badge PDF attachment and preview
- Use for: Live demos, small VIP events

### Batch Mode (`PROCESSING_MODE=batch`)

- Badge generated and **saved to Azure Blob Storage**
- All badges accumulate in storage
- Admin downloads all badges when ready to print
- Use for: Production events with 20+ attendees

Toggle mode in `local.settings.json`:
```json
"PROCESSING_MODE": "batch"  // or "demo"
```

## Project Structure

```
function_app/
├── function_app.py          # Main HTTP trigger function
├── host.json                # Function runtime config
├── requirements.txt         # Python dependencies for deployment
├── local.settings.json      # Local environment variables (gitignored)
│
└── lib/                     # Shared library code
    ├── badge_processor.py   # Badge generation logic
    ├── email_client.py      # SendGrid email integration
    └── storage_client.py    # Azure Blob Storage client
```

## API Endpoints

### POST /api/process-badge

Generate and process a badge from form data.

**Request Body:**
```json
{
  "event_id": "string",
  "name": "string",
  "email": "string",
  "title": "string",
  "company": "string",
  "location": "string",
  "interests": "string or array",
  "profile_url": "string (optional)",
  "preferred_social_platform": "string (optional)",
  "social_handle": "string (optional)",
  "pronouns": "string (optional)",
  "tags": {
    "tag_name": "tag_value"
  }
}
```

**Response (Success):**
```json
{
  "status": "success",
  "mode": "demo" | "batch",
  "message": "Badge generated...",
  "email_sent": true | null,
  "blob_url": "url" | null
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error_type": "validation" | "internal",
  "message": "Error description"
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "mode": "batch" | "demo"
}
```

## Error Handling

- **Validation errors** (400): Invalid form data, missing required fields
- **Internal errors** (500): AI generation failures, storage errors, etc.

All errors trigger an email notification to `SUPPORT_EMAIL` with:
- Full error details
- Form data for manual retry
- Timestamp and user information

## Deployment

See main repository README for deployment instructions via GitHub Actions.

## Environment Variables

See `.env.example` in the root directory for all required environment variables.

## Troubleshooting

### Function won't start

1. Check Python version: `python --version` (should be 3.11.x)
2. Install dependencies: `pip install -r requirements.txt`
3. Verify Azure Functions Core Tools: `func --version`

### Badge generation fails

1. Check Azure OpenAI credentials in `local.settings.json`
2. Verify event exists in `../mocks/events.json`
3. Check logs for detailed error messages

### Email not sending

1. Verify SendGrid API key in `local.settings.json`
2. Check SendGrid template IDs are correct
3. Ensure `EVENT_ORGANIZER_EMAIL` is set

### Blob storage errors

1. Verify `AZURE_STORAGE_CONNECTION_STRING` is correct
2. Check that storage account exists and is accessible
3. Ensure container name is valid (lowercase, no special chars)

## Next Steps (Phase 2)

- [ ] Set up Azure infrastructure (resource group, function app, storage account)
- [ ] Configure GitHub Actions for CI/CD
- [ ] Create SendGrid email templates
- [ ] Set up Google Apps Script webhook
- [ ] Test end-to-end pipeline
