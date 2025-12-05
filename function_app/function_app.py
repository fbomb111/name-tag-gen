"""Azure Functions app for badge generation."""
import sys
from pathlib import Path
import azure.functions as func
import json
import logging
import traceback

# Setup sys.path BEFORE any other imports from our modules
_here = Path(__file__).parent
if (_here / "src").exists():
    sys.path.insert(0, str(_here))

# Now import our modules (lazy initialization means no directory creation at import time)
from lib.badge_processor import BadgeProcessor
from lib.email_client import EmailClient

app = func.FunctionApp()


@app.function_name(name="HealthCheck")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health check endpoint to verify the function is running."""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "message": "Badge generation service is running"}),
        status_code=200,
        mimetype="application/json"
    )


@app.function_name(name="ProcessBadge")
@app.route(route="process-badge", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def process_badge(req: func.HttpRequest) -> func.HttpResponse:
    """
    Process a badge generation request from form submission.

    Expected JSON body:
    {
        "event_id": "cohatch_afterhours",
        "name": "John Doe",
        "title": "Software Engineer",
        "company": "Tech Corp",
        "email": "john@example.com",
        "location": "Columbus, OH",
        "pronouns": "he/him",
        "interests": "hiking, photography, cooking",
        "tags": {
            "membership_level": "Professional",
            "industry": "Technology",
            ...
        }
    }

    Returns:
    - Success: PDF badge as binary with content-disposition header
    - Error: JSON with error details
    """
    logging.info("ProcessBadge function triggered")

    try:
        # Parse request body
        try:
            form_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )

        # Validate required fields
        required_fields = ["event_id", "name", "email"]
        missing = [f for f in required_fields if not form_data.get(f)]
        if missing:
            return func.HttpResponse(
                json.dumps({"error": f"Missing required fields: {', '.join(missing)}"}),
                status_code=400,
                mimetype="application/json"
            )

        logging.info(f"Processing badge for: {form_data.get('name')}")

        # Process the badge
        processor = BadgeProcessor()
        result = processor.generate_badge(
            form_data=form_data,
            force_regenerate=form_data.get("force_regenerate", False)
        )

        # Get results
        pdf_bytes = result["pdf_bytes"]
        attendee_name = result["attendee_name"]
        attendee_email = form_data.get("email")
        event_name = result["event_name"]

        logging.info(f"Badge generated successfully for: {attendee_name}")

        # Send badge via email to the form submitter
        try:
            email_client = EmailClient()
            email_result = email_client.send_badge_ready_email(
                badge_pdf=pdf_bytes,
                badge_preview=None,  # No preview for now
                attendee_name=attendee_name,
                event_name=event_name,
                recipient_email=attendee_email
            )
            logging.info(f"Badge email sent to: {attendee_email}")

            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": f"Badge generated and sent to {attendee_email}",
                    "attendee_name": attendee_name,
                    "email_status": email_result.get("status")
                }),
                status_code=200,
                mimetype="application/json"
            )
        except Exception as email_error:
            logging.error(f"Failed to send badge email: {str(email_error)}")
            # Badge was generated but email failed - return error
            return func.HttpResponse(
                json.dumps({
                    "error": "Badge generated but email delivery failed",
                    "details": str(email_error)
                }),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logging.error(f"Error processing badge: {str(e)}")
        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({
                "error": "Badge generation failed",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
