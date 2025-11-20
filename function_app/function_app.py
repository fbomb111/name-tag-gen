"""
Azure Function App for Badge Generation
Handles form submissions and generates personalized event badges
"""
import azure.functions as func
import logging
import json
import os
from typing import Dict, Any

# Import our custom processors
from lib.badge_processor import BadgeProcessor
from lib.email_client import EmailClient
from lib.storage_client import StorageClient

app = func.FunctionApp()

# Configuration
PROCESSING_MODE = os.getenv('PROCESSING_MODE', 'batch')  # 'demo' or 'batch'
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'support@example.com')

@app.function_name(name="ProcessBadge")
@app.route(route="process-badge", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def process_badge(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function that processes badge generation requests from Google Forms

    Expected JSON payload:
    {
        "event_id": "cohatch_afterhours",
        "name": "John Doe",
        "email": "john@example.com",
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Columbus, OH",
        "interests": "hiking, photography, coding",
        "profile_url": "https://example.com/profile",
        "preferred_social_platform": "linkedin",
        "social_handle": "johndoe",
        "pronouns": "he/him"
    }
    """
    logging.info('Badge generation request received')

    try:
        # Parse request body
        req_body = req.get_json()
        logging.info(f"Processing badge for: {req_body.get('name')}")

        # Initialize processors
        badge_processor = BadgeProcessor()
        email_client = EmailClient()
        storage_client = StorageClient()

        # Generate the badge
        badge_result = badge_processor.generate_badge(req_body)

        # Process based on mode
        if PROCESSING_MODE == 'demo':
            # Demo mode: Send email immediately
            email_result = email_client.send_badge_ready_email(
                badge_pdf=badge_result['pdf_bytes'],
                badge_preview=badge_result['preview_image'],
                attendee_name=req_body.get('name'),
                event_id=req_body.get('event_id')
            )

            return func.HttpResponse(
                json.dumps({
                    'status': 'success',
                    'mode': 'demo',
                    'message': 'Badge generated and emailed successfully',
                    'email_sent': True
                }),
                status_code=200,
                mimetype='application/json'
            )

        elif PROCESSING_MODE == 'batch':
            # Batch mode: Save to blob storage
            blob_url = storage_client.upload_badge(
                badge_pdf=badge_result['pdf_bytes'],
                event_id=req_body.get('event_id'),
                user_id=badge_result['user_id']
            )

            return func.HttpResponse(
                json.dumps({
                    'status': 'success',
                    'mode': 'batch',
                    'message': 'Badge generated and saved to storage',
                    'blob_url': blob_url
                }),
                status_code=200,
                mimetype='application/json'
            )

    except ValueError as e:
        # Validation errors
        logging.error(f"Validation error: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                'status': 'error',
                'error_type': 'validation',
                'message': str(e)
            }),
            status_code=400,
            mimetype='application/json'
        )

    except Exception as e:
        # Unexpected errors - notify support
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)

        try:
            email_client = EmailClient()
            email_client.send_error_notification(
                error=str(e),
                form_data=req_body,
                support_email=SUPPORT_EMAIL
            )
        except:
            logging.error("Failed to send error notification email")

        return func.HttpResponse(
            json.dumps({
                'status': 'error',
                'error_type': 'internal',
                'message': 'An error occurred processing your badge. Support has been notified.'
            }),
            status_code=500,
            mimetype='application/json'
        )


@app.function_name(name="HealthCheck")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({
            'status': 'healthy',
            'mode': PROCESSING_MODE
        }),
        status_code=200,
        mimetype='application/json'
    )
