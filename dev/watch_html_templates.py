"""
Watch HTML template files and auto-regenerate preview on changes.
Provides instant visual feedback for badge layout iteration.
"""
import time
import sys
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from preview_html_badge import generate_preview


ROOT = Path(__file__).parent


class TemplateChangeHandler(FileSystemEventHandler):
    """Handles file system events for template changes."""

    def __init__(self, user_id="user_007"):
        self.user_id = user_id
        self.last_modified = {}
        self.debounce_seconds = 0.5  # Wait 0.5s before regenerating

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only watch CSS and HTML files
        if file_path.suffix not in ['.css', '.html']:
            return

        # Debounce: ignore rapid successive changes
        now = time.time()
        if file_path in self.last_modified:
            if now - self.last_modified[file_path] < self.debounce_seconds:
                return

        self.last_modified[file_path] = now

        # Regenerate preview
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🔄 Detected change: {file_path.name}")
            generate_preview(self.user_id)
            print(f"[{timestamp}] ✓ Preview updated!\n")
        except Exception as e:
            print(f"[{timestamp}] ❌ Error: {e}\n")


def watch_with_watchdog(user_id="user_007"):
    """Watch templates using watchdog library (recommended)."""
    template_dir = ROOT / "config" / "html_templates" / "professional"

    print("=" * 60)
    print("🔄 Badge Preview Watch Mode (Watchdog)")
    print("=" * 60)
    print()
    print(f"📁 Watching: {template_dir}")
    print(f"   • {template_dir / 'styles.css'}")
    print(f"   • {template_dir / 'template.html'}")
    print()
    print(f"📋 Preview: output/preview/badge_preview.html")
    print(f"👤 Attendee: {user_id}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Generate initial preview
    try:
        output_path = generate_preview(user_id)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✓ Initial preview generated")
        print()
        print(f"🌐 Open in VS Code:")
        print(f"   1. Open Command Palette (Cmd+Shift+P)")
        print(f"   2. Type: 'Simple Browser: Show'")
        print(f"   3. Enter: file://{output_path.absolute()}")
        print()
        print(f"   OR right-click {output_path.relative_to(ROOT)} → Open in Live Preview")
        print()
        print("-" * 60)
        print()
    except Exception as e:
        print(f"❌ Error generating initial preview: {e}")
        return

    # Set up file watcher
    event_handler = TemplateChangeHandler(user_id)
    observer = Observer()
    observer.schedule(event_handler, str(template_dir), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("👋 Stopped watching")
        print("=" * 60)
        observer.stop()

    observer.join()


def watch_with_polling(user_id="user_007"):
    """Watch templates using simple file polling (fallback)."""
    template_dir = ROOT / "config" / "html_templates" / "professional"
    css_path = template_dir / "styles.css"
    html_path = template_dir / "template.html"

    print("=" * 60)
    print("🔄 Badge Preview Watch Mode (Polling)")
    print("=" * 60)
    print()
    print(f"📁 Watching:")
    print(f"   • {css_path}")
    print(f"   • {html_path}")
    print()
    print(f"📋 Preview: output/preview/badge_preview.html")
    print(f"👤 Attendee: {user_id}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Generate initial preview
    try:
        output_path = generate_preview(user_id)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✓ Initial preview generated")
        print()
        print(f"🌐 Open in VS Code:")
        print(f"   1. Open Command Palette (Cmd+Shift+P)")
        print(f"   2. Type: 'Simple Browser: Show'")
        print(f"   3. Enter: file://{output_path.absolute()}")
        print()
        print(f"   OR right-click {output_path.relative_to(ROOT)} → Open in Live Preview")
        print()
        print("-" * 60)
        print()
    except Exception as e:
        print(f"❌ Error generating initial preview: {e}")
        return

    # Track file modification times
    last_css_mtime = css_path.stat().st_mtime if css_path.exists() else 0
    last_html_mtime = html_path.stat().st_mtime if html_path.exists() else 0

    try:
        while True:
            time.sleep(0.5)  # Check every 0.5 seconds

            css_mtime = css_path.stat().st_mtime if css_path.exists() else 0
            html_mtime = html_path.stat().st_mtime if html_path.exists() else 0

            if css_mtime != last_css_mtime or html_mtime != last_html_mtime:
                changed_file = "styles.css" if css_mtime != last_css_mtime else "template.html"

                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 🔄 Detected change: {changed_file}")
                    generate_preview(user_id)
                    print(f"[{timestamp}] ✓ Preview updated!\n")
                except Exception as e:
                    print(f"[{timestamp}] ❌ Error: {e}\n")

                last_css_mtime = css_mtime
                last_html_mtime = html_mtime

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("👋 Stopped watching")
        print("=" * 60)


def main():
    """Main entry point."""
    user_id = sys.argv[1] if len(sys.argv) > 1 else "user_007"

    # Check if watchdog is available
    if WATCHDOG_AVAILABLE:
        watch_with_watchdog(user_id)
    else:
        print("⚠️  'watchdog' library not found. Using simple polling instead.")
        print("   For better performance, install: pip install watchdog")
        print()
        watch_with_polling(user_id)


if __name__ == "__main__":
    main()
