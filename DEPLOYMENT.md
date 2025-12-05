# Azure Function Deployment Guide

## Overview

The badge generation system is deployed as an Azure Function App. This guide covers local development and production deployment.

## Quick Start

### Deploy to Azure
```bash
./scripts/deploy-function.sh
```

This syncs all required files to `function_app/` and deploys to Azure.

---

## Deployment Script

### Location
`scripts/deploy-function.sh`

### What It Does
1. **Syncs project files** into `function_app/` using rsync:
   - `src/` → Core application code (models, renderers, utils)
   - `scripts/` → AI prompts and image generation
   - `data/` → Geographic shapefiles for location graphics
   - `assets/` → Event logos and icons
   - `config/` → Badge templates and HTML
   - `mocks/` → Event and attendee configuration

2. **Deploys to Azure** Function App:
   - Resource Group: `rg-name-tag-gen`
   - Function App: `func-name-tag-gen-66802`
   - Uses remote build (Oryx) for dependency installation

3. **Verifies deployment**:
   - Lists deployed functions
   - Tests health endpoint

### Usage

#### Full Deployment
```bash
./scripts/deploy-function.sh
```

#### Preview Changes (Dry Run)
```bash
./scripts/deploy-function.sh --dry-run
```
Shows what would be synced without making changes.

#### Sync Files Only (Skip Azure Deploy)
```bash
./scripts/deploy-function.sh --no-deploy
# OR
SKIP_DEPLOY=1 ./scripts/deploy-function.sh
```
Useful for preparing deployment files locally.

### Configuration

Override defaults with environment variables:
```bash
RG=my-resource-group APP=my-function-app ./scripts/deploy-function.sh
```

---

## File Structure

### Project Root (Development)
```
name-tag-gen/
├── src/              # Core application code
├── scripts/          # Image generation, AI prompts
├── data/             # Geographic shapefiles
├── assets/           # Event logos, icons
├── config/           # Badge templates
├── mocks/            # Event/attendee data
└── function_app/     # Azure Function (deployment target)
```

### function_app/ (Deployment)
```
function_app/
├── function_app.py   # Function endpoints
├── host.json         # Azure Functions config
├── requirements.txt  # Dependencies
├── lib/              # Function-specific code
├── src/              # [SYNCED] Core app code
├── scripts/          # [SYNCED] AI/image generation
├── data/             # [SYNCED] Geographic data
├── assets/           # [SYNCED] Event logos
├── config/           # [SYNCED] Badge templates
└── mocks/            # [SYNCED] Event data
```

---

## Local Development

### Setup
1. Create virtual environment in `function_app/`:
   ```bash
   cd function_app
   python3.10 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure local settings:
   ```bash
   cp function_app/local.settings.json.example function_app/local.settings.json
   # Edit with your API keys
   ```

### Run Locally
Use VS Code launch config: **"Azure Functions: Start (No Debug)"**

Or manually:
```bash
cd function_app
source .venv/bin/activate
func start --port 7072
```

### Test Locally
Use VS Code launch config: **"Test Local Function (Random Attendee)"**

Or manually:
```bash
python scripts/test_local_function.py --email your@email.com
```

---

## Production Environment

### Azure Resources
- **Function App**: `func-name-tag-gen-66802`
- **Resource Group**: `rg-name-tag-gen`
- **Storage Account**: `stnametaggen66657`
- **Python Version**: 3.11
- **Runtime**: Azure Functions v4

### Environment Variables (Azure)
Set via Azure Portal or CLI:

```bash
az functionapp config appsettings set \
  -g rg-name-tag-gen \
  -n func-name-tag-gen-66802 \
  --settings \
    PROCESSING_MODE=demo \
    AZURE_OPENAI_ENDPOINT="https://..." \
    AZURE_OPENAI_API_KEY="..." \
    SENDGRID_API_KEY="..." \
    # ... etc
```

### Function Endpoints

#### Health Check
```
GET https://func-name-tag-gen-66802.azurewebsites.net/api/health
```

Response:
```json
{"status": "healthy", "mode": "demo"}
```

#### Process Badge
```
POST https://func-name-tag-gen-66802.azurewebsites.net/api/process-badge
```

Payload:
```json
{
  "event_id": "cohatch_afterhours",
  "name": "John Doe",
  "email": "john@example.com",
  "title": "Software Engineer",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "interests": "Hiking, Photography, Coffee",
  "profile_url": "https://example.com/john",
  "preferred_social_platform": "linkedin",
  "social_handle": "johndoe",
  "pronouns": "he/him",
  "tags": {
    "Committee": "Innovation Council",
    "Years as Member": "2-4",
    "Rep": "Jane Smith",
    "Industry": "Technology",
    "Membership Level": "Corporate"
  }
}
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Test locally with `./scripts/deploy-function.sh --dry-run`
- [ ] Verify all environment variables are set in Azure
- [ ] Check SendGrid templates are created
- [ ] Ensure Azure OpenAI deployment is active
- [ ] Test with `--no-deploy` to verify file sync
- [ ] Run full deployment: `./scripts/deploy-function.sh`
- [ ] Verify health endpoint returns 200
- [ ] Test badge generation with real attendee data

---

## Troubleshooting

### Import Errors After Deploy
**Symptom**: "ModuleNotFoundError: No module named 'src'"

**Solution**: Run sync script to ensure all directories are present:
```bash
./scripts/deploy-function.sh --no-deploy
```

### Logo/Asset Not Found
**Symptom**: "Failed to load image at assets/..."

**Solution**: Verify assets were synced and check .funcignore doesn't exclude them.

### Function Timeout
**Symptom**: AI image generation takes too long

**Solution**:
- Check Azure OpenAI quota/throttling
- Increase function timeout in host.json (currently 10 min)
- Consider batch processing mode

### Local Settings Not Synced
**Good!** `local.settings.json` is intentionally excluded from deployment (contains secrets).

Set environment variables in Azure Portal instead.

---

## CI/CD Integration

### GitHub Actions (Future)
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy Function
        run: ./scripts/deploy-function.sh
        env:
          RG: rg-name-tag-gen
          APP: func-name-tag-gen-66802
```

---

## Notes

- **MVP Approach**: Events, logos, and config are deployed with the function (not dynamic)
- **Future**: Move to Azure Blob Storage for assets and database for event config
- **File Sync**: Directories in function_app/ are tracked in git (see .gitignore rules)
- **Updates**: Re-run deploy script after changing events, logos, or templates
