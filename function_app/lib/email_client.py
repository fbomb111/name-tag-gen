"""
Email Client - SendGrid integration for badge delivery and error notifications
"""
import os
import base64
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId
)
import logging


class EmailClient:
    """Handles email sending via SendGrid"""

    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'Badge Generation System')
        self.organizer_email = os.getenv('EVENT_ORGANIZER_EMAIL')
        self.template_badge_ready = os.getenv('SENDGRID_TEMPLATE_ID_BADGE_READY')
        self.template_error = os.getenv('SENDGRID_TEMPLATE_ID_ERROR')

        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY not configured")

        self.client = SendGridAPIClient(self.api_key)

    def send_badge_ready_email(
        self,
        badge_pdf: bytes,
        badge_preview: Optional[bytes],
        attendee_name: str,
        event_id: str
    ) -> dict:
        """
        Send "Badge is Ready" email to event organizer

        Args:
            badge_pdf: PDF badge file as bytes
            badge_preview: Preview image as bytes (optional)
            attendee_name: Name of the attendee
            event_id: Event identifier

        Returns:
            Response from SendGrid API
        """
        logging.info(f"Sending badge ready email for {attendee_name}")

        # Create message
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=self.organizer_email
        )

        # Use dynamic template if configured
        if self.template_badge_ready:
            message.template_id = self.template_badge_ready
            message.dynamic_template_data = {
                'attendee_name': attendee_name,
                'event_id': event_id,
                'preview_available': badge_preview is not None
            }
        else:
            # Fallback to plain text
            message.subject = f"Badge Ready: {attendee_name}"
            message.content = f"""
            Badge generated for {attendee_name} (Event: {event_id})

            Please see attached PDF for the badge.
            """

        # Attach PDF
        pdf_attachment = Attachment()
        pdf_attachment.file_content = FileContent(base64.b64encode(badge_pdf).decode())
        pdf_attachment.file_name = FileName(f"{attendee_name.replace(' ', '_')}_badge.pdf")
        pdf_attachment.file_type = FileType('application/pdf')
        pdf_attachment.disposition = Disposition('attachment')
        message.attachment = [pdf_attachment]

        # Attach preview image if provided
        if badge_preview:
            preview_attachment = Attachment()
            preview_attachment.file_content = FileContent(
                base64.b64encode(badge_preview).decode()
            )
            preview_attachment.file_name = FileName('badge_preview.png')
            preview_attachment.file_type = FileType('image/png')
            preview_attachment.disposition = Disposition('inline')
            preview_attachment.content_id = ContentId('badge_preview')
            message.attachment.append(preview_attachment)

        # Send email
        try:
            response = self.client.send(message)
            logging.info(f"Email sent successfully: {response.status_code}")
            return {
                'status': 'sent',
                'status_code': response.status_code,
                'recipient': self.organizer_email
            }
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise

    def send_error_notification(
        self,
        error: str,
        form_data: dict,
        support_email: str
    ) -> dict:
        """
        Send error notification to support team

        Args:
            error: Error message
            form_data: Original form data that caused the error
            support_email: Email address for support team

        Returns:
            Response from SendGrid API
        """
        logging.info(f"Sending error notification to {support_email}")

        # Create message
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=support_email
        )

        # Use error template if configured
        if self.template_error:
            message.template_id = self.template_error
            message.dynamic_template_data = {
                'error_message': error,
                'form_data': str(form_data),
                'attendee_name': form_data.get('name', 'Unknown'),
                'event_id': form_data.get('event_id', 'Unknown')
            }
        else:
            # Fallback to plain text
            message.subject = "Badge Generation Error"
            message.content = f"""
            ERROR: Badge generation failed

            Error: {error}

            Form Data:
            {self._format_form_data(form_data)}

            Please investigate and retry manually if needed.
            """

        # Send email
        try:
            response = self.client.send(message)
            logging.info(f"Error notification sent: {response.status_code}")
            return {
                'status': 'sent',
                'status_code': response.status_code,
                'recipient': support_email
            }
        except Exception as e:
            logging.error(f"Failed to send error notification: {str(e)}")
            # Don't raise - we don't want to fail the function if error email fails
            return {'status': 'failed', 'error': str(e)}

    def _format_form_data(self, form_data: dict) -> str:
        """Format form data for display in email"""
        lines = []
        for key, value in form_data.items():
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)
