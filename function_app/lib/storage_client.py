"""
Storage Client - Azure Blob Storage integration for batch mode badge storage
Uses Managed Identity in Azure, falls back to connection string for local development
"""
import os
from typing import Optional
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.identity import DefaultAzureCredential
import logging


class StorageClient:
    """Handles blob storage operations for badge PDFs"""

    def __init__(self):
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'badges')

        # Try managed identity first (Azure), fall back to connection string (local)
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')

        if storage_account_name:
            # Use managed identity with storage account name (Azure production)
            account_url = f"https://{storage_account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )
            logging.info(f"Using managed identity for storage: {storage_account_name}")
        elif connection_string:
            # Fall back to connection string (local development)
            self.blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
            logging.info("Using connection string for storage (local dev)")
        else:
            raise ValueError(
                "Either AZURE_STORAGE_ACCOUNT_NAME (for managed identity) or "
                "AZURE_STORAGE_CONNECTION_STRING (for local dev) must be configured"
            )

        # Ensure container exists
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                logging.info(f"Creating container: {self.container_name}")
                container_client.create_container()
        except Exception as e:
            logging.error(f"Failed to ensure container exists: {str(e)}")
            raise

    def upload_badge(
        self,
        badge_pdf: bytes,
        event_id: str,
        user_id: str,
        overwrite: bool = True
    ) -> str:
        """
        Upload badge PDF to blob storage

        Args:
            badge_pdf: PDF file as bytes
            event_id: Event identifier
            user_id: User identifier
            overwrite: Whether to overwrite existing file

        Returns:
            URL of uploaded blob
        """
        # Create blob path: {event_id}/{user_id}.pdf
        blob_name = f"{event_id}/{user_id}.pdf"

        logging.info(f"Uploading badge to blob storage: {blob_name}")

        try:
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Upload with PDF content type
            blob_client.upload_blob(
                badge_pdf,
                overwrite=overwrite,
                content_settings=ContentSettings(content_type='application/pdf')
            )

            # Return blob URL
            blob_url = blob_client.url
            logging.info(f"Badge uploaded successfully: {blob_url}")

            return blob_url

        except Exception as e:
            logging.error(f"Failed to upload badge: {str(e)}")
            raise

    def list_badges_for_event(self, event_id: str) -> list:
        """
        List all badges for a given event

        Args:
            event_id: Event identifier

        Returns:
            List of blob names
        """
        logging.info(f"Listing badges for event: {event_id}")

        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            # List blobs with event_id prefix
            blob_list = []
            for blob in container_client.list_blobs(name_starts_with=f"{event_id}/"):
                blob_list.append({
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.creation_time,
                    'url': f"{container_client.url}/{blob.name}"
                })

            logging.info(f"Found {len(blob_list)} badges for event {event_id}")
            return blob_list

        except Exception as e:
            logging.error(f"Failed to list badges: {str(e)}")
            raise

    def download_badge(self, blob_name: str) -> bytes:
        """
        Download badge PDF from blob storage

        Args:
            blob_name: Name of the blob

        Returns:
            PDF file as bytes
        """
        logging.info(f"Downloading badge: {blob_name}")

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Download blob
            download_stream = blob_client.download_blob()
            badge_pdf = download_stream.readall()

            logging.info(f"Badge downloaded successfully: {len(badge_pdf)} bytes")
            return badge_pdf

        except Exception as e:
            logging.error(f"Failed to download badge: {str(e)}")
            raise

    def delete_badge(self, blob_name: str) -> bool:
        """
        Delete badge PDF from blob storage

        Args:
            blob_name: Name of the blob

        Returns:
            True if successful
        """
        logging.info(f"Deleting badge: {blob_name}")

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            blob_client.delete_blob()
            logging.info(f"Badge deleted successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to delete badge: {str(e)}")
            raise
