#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Azure Function Deployment Script - Name Tag Generation
# ============================================================================
# Syncs project files into function_app/ and deploys to Azure
#
# Usage:
#   ./scripts/deploy-function.sh           # Full deployment
#   ./scripts/deploy-function.sh --dry-run # Preview changes only
#   ./scripts/deploy-function.sh --no-deploy # Sync files, skip Azure deploy
#   SKIP_DEPLOY=1 ./scripts/deploy-function.sh # Same as --no-deploy
# ============================================================================

# ---- CONFIG ----------------------------------------------------------------
RG="${RG:-rg-name-tag-gen}"
APP="${APP:-func-name-tag-gen-66802}"

# Auto-detect project root
ROOT="${ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
FUNC_DIR="$ROOT/function_app"

# Parse arguments
DRY_RUN=0
NO_DEPLOY=0
for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=1 ;;
    --no-deploy) NO_DEPLOY=1 ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

# Honor SKIP_DEPLOY env var
[ "${SKIP_DEPLOY:-0}" = "1" ] && NO_DEPLOY=1

# ---- PRECHECKS -------------------------------------------------------------
echo "==> Checking prerequisites..."
command -v az >/dev/null || { echo "ERROR: 'az' CLI not found"; exit 1; }
command -v func >/dev/null || { echo "ERROR: Azure Functions Core Tools 'func' not found"; exit 1; }
command -v rsync >/dev/null || { echo "ERROR: 'rsync' not found"; exit 1; }

[ -d "$ROOT" ] || { echo "ERROR: Project root not found: $ROOT"; exit 1; }
[ -d "$FUNC_DIR" ] || { echo "ERROR: function_app directory not found: $FUNC_DIR"; exit 1; }
[ -f "$FUNC_DIR/function_app.py" ] || { echo "ERROR: function_app.py not found"; exit 1; }
[ -f "$FUNC_DIR/host.json" ] || { echo "ERROR: host.json not found"; exit 1; }

echo "ROOT: $ROOT"
echo "FUNC_DIR: $FUNC_DIR"
echo "RG: $RG"
echo "APP: $APP"
[ $DRY_RUN -eq 1 ] && echo "MODE: DRY RUN (no changes will be made)"
[ $NO_DEPLOY -eq 1 ] && echo "MODE: NO DEPLOY (sync only, skip Azure)"
echo ""

# ---- DEFINE SYNC FUNCTION --------------------------------------------------
sync_dir() {
  local src="$1"
  local dest="$2"
  local label="$3"

  if [ ! -d "$src" ]; then
    echo "⚠️  SKIP: $label (source not found: $src)"
    return
  fi

  echo "==> Syncing $label..."
  echo "    FROM: $src"
  echo "    TO:   $dest"

  # Build rsync exclude list
  local excludes=(
    --exclude='__pycache__'
    --exclude='*.pyc'
    --exclude='*.pyo'
    --exclude='*.log'
    --exclude='.DS_Store'
    --exclude='.venv'
    --exclude='venv'
    --exclude='.git'
    --exclude='*.bak'
    --exclude='credentials.json'  # Google OAuth credentials (scripts/)
    --exclude='token.json'         # Google OAuth token (scripts/)
  )

  if [ $DRY_RUN -eq 1 ]; then
    rsync -av --dry-run --delete "${excludes[@]}" "$src/" "$dest/"
  else
    mkdir -p "$dest"
    rsync -a --delete "${excludes[@]}" "$src/" "$dest/"
    echo "    ✓ Synced $(du -sh "$dest" | cut -f1) to $dest"
  fi
  echo ""
}

# ---- SYNC REQUIRED DIRECTORIES ---------------------------------------------
echo "==> STEP 1: Syncing project files to function_app/"
echo ""

# Core application code
sync_dir "$ROOT/src" "$FUNC_DIR/src" "src/ (models, renderers, utils)"

# Image generation and AI prompts
sync_dir "$ROOT/scripts" "$FUNC_DIR/scripts" "scripts/ (AI prompts, image generation)"

# Geographic data for location graphics
sync_dir "$ROOT/data" "$FUNC_DIR/data" "data/ (natural earth shapefiles)"

# Event assets (logos, icons)
sync_dir "$ROOT/assets" "$FUNC_DIR/assets" "assets/ (event logos, icons)"

# Badge templates and HTML config
sync_dir "$ROOT/config" "$FUNC_DIR/config" "config/ (badge templates)"

# Event and attendee configuration
sync_dir "$ROOT/mocks" "$FUNC_DIR/mocks" "mocks/ (events, attendees)"

if [ $DRY_RUN -eq 1 ]; then
  echo "==> DRY RUN COMPLETE (no changes were made)"
  exit 0
fi

# ---- IMPORT VALIDATION -----------------------------------------------------
echo "==> STEP 2: Validating imports..."
echo ""

# Run the import validation script from within the function_app directory
pushd "$FUNC_DIR" >/dev/null
if python3 test-imports.py; then
  echo ""
else
  echo ""
  echo "ERROR: Import validation failed. Fix the above errors before deploying."
  exit 1
fi
popd >/dev/null

if [ $NO_DEPLOY -eq 1 ]; then
  echo "==> Files synced. Skipping Azure deployment (--no-deploy)"
  exit 0
fi

# ---- AZURE DEPLOYMENT ------------------------------------------------------
echo "==> STEP 3: Deploying to Azure"
echo ""

# Check if logged into Azure
if ! az account show >/dev/null 2>&1; then
  echo "ERROR: Not logged into Azure. Run 'az login' first."
  exit 1
fi

# Verify resource exists
echo "==> Verifying Azure Function App exists..."
if ! az functionapp show -g "$RG" -n "$APP" >/dev/null 2>&1; then
  echo "ERROR: Function app '$APP' not found in resource group '$RG'"
  exit 1
fi

# Enable remote build (Oryx)
echo "==> Enabling remote build on function app..."
az functionapp config appsettings set -g "$RG" -n "$APP" \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true ENABLE_ORYX_BUILD=true \
  >/dev/null

# Deploy with remote build
echo "==> Publishing to Azure with remote build..."
pushd "$FUNC_DIR" >/dev/null
func azure functionapp publish "$APP" --build remote
popd >/dev/null

# ---- VERIFICATION ----------------------------------------------------------
echo ""
echo "==> STEP 4: Verification"
echo ""

echo "==> Listing deployed functions..."
az functionapp function list -g "$RG" -n "$APP" -o table

echo ""
echo "==> Testing health endpoint..."
HEALTH_URL="https://${APP}.azurewebsites.net/api/health"
echo "    URL: $HEALTH_URL"

# Give the function a moment to warm up
sleep 3

if curl -sSf -m 10 "$HEALTH_URL" 2>/dev/null; then
  echo "    ✓ Health check passed"
else
  echo "    ⚠️  Health check failed (function may still be starting up)"
fi

echo ""
echo "==> Deployment complete!"
echo ""
echo "Function URLs:"
echo "  Health: https://${APP}.azurewebsites.net/api/health"
echo "  Badge:  https://${APP}.azurewebsites.net/api/process-badge"
echo ""
