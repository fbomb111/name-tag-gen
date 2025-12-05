"""
Centralized path resolution for the badge generation system.

Works in both:
- Local development (src/ at project root)
- Azure deployment (src/ synced to function_app/)
"""
from pathlib import Path
import os


def get_project_root() -> Path:
    """
    Get project root - works in both local dev and Azure deployment.

    Detection logic:
    1. If PROJECT_ROOT env var set, use it (useful for testing/override)
    2. Navigate up from this file to find the root containing src/

    In local dev: /path/to/name-tag-gen/
    In Azure: /home/site/wwwroot/ (function_app contents)
    """
    # Allow override via environment
    if env_root := os.getenv('PROJECT_ROOT'):
        return Path(env_root)

    # Start from this file's location: src/utils/paths.py
    current = Path(__file__).resolve().parent  # src/utils/

    # Go up to src/, then one more to get project root
    src_dir = current.parent  # src/
    project_root = src_dir.parent  # function_app/ or name-tag-gen/

    # Verify we found a valid root (has src/ directory)
    if (project_root / "src").exists():
        return project_root

    # Fallback: search upward for a directory containing src/
    for parent in current.parents:
        if (parent / "src").exists():
            return parent

    raise RuntimeError(
        "Could not determine project root. "
        "Set PROJECT_ROOT environment variable or ensure src/ directory exists."
    )


# Module-level constant for convenience
PROJECT_ROOT = get_project_root()


def get_config_dir() -> Path:
    """Get the config directory (badge templates, HTML templates)."""
    return PROJECT_ROOT / "config"


def get_mocks_dir() -> Path:
    """Get the mocks directory (event and attendee JSON data)."""
    return PROJECT_ROOT / "mocks"


def get_assets_dir() -> Path:
    """Get the assets directory (event logos, sponsor logos, icons)."""
    return PROJECT_ROOT / "assets"


def get_data_dir() -> Path:
    """Get the data directory (Natural Earth shapefiles)."""
    return PROJECT_ROOT / "data"


def _is_azure_environment() -> bool:
    """Check if we're running in Azure/production environment.

    Primary check: ENVIRONMENT=prod (explicit, reliable)
    Fallback: Azure-specific environment variables
    """
    # Explicit environment flag (most reliable)
    if os.getenv('ENVIRONMENT') == 'prod':
        return True

    # Fallback: Azure Functions sets various environment variables
    azure_indicators = [
        'WEBSITE_INSTANCE_ID',          # Primary Azure indicator
        'AZURE_FUNCTIONS_ENVIRONMENT',  # Functions-specific
        'FUNCTIONS_WORKER_RUNTIME',     # Functions runtime
        'WEBSITE_SITE_NAME',            # Azure App Service/Functions
    ]
    return any(os.getenv(var) is not None for var in azure_indicators)


def get_output_dir() -> Path:
    """Get the output directory (generated badges, working files).

    In Azure: Uses /tmp which is writable
    Locally: Uses PROJECT_ROOT/output
    """
    if _is_azure_environment():
        # Azure Functions has writable /tmp directory
        output = Path("/tmp/badge_output")
    else:
        output = PROJECT_ROOT / "output"
    output.mkdir(exist_ok=True)
    return output


def get_working_dir(event_id: str = None, user_id: str = None) -> Path:
    """
    Get working directory for intermediate files.

    Args:
        event_id: Optional event ID for event-specific subdirectory
        user_id: Optional user ID for user-specific subdirectory

    Returns:
        Path to working directory
    """
    working = get_output_dir() / "working"
    if event_id:
        working = working / event_id
        if user_id:
            working = working / user_id
    working.mkdir(parents=True, exist_ok=True)
    return working


def get_badges_dir(event_id: str = None) -> Path:
    """
    Get badges output directory.

    Args:
        event_id: Optional event ID for event-specific subdirectory

    Returns:
        Path to badges directory
    """
    badges = get_output_dir() / "badges"
    if event_id:
        badges = badges / event_id
    badges.mkdir(parents=True, exist_ok=True)
    return badges


def get_location_graphics_dir() -> Path:
    """Get directory for cached location graphics."""
    location_dir = get_output_dir() / "location_graphics"
    location_dir.mkdir(parents=True, exist_ok=True)
    return location_dir
