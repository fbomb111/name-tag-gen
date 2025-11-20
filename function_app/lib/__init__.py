"""
Function App Library
Shared code for Azure Functions badge generation
"""
from .badge_processor import BadgeProcessor
from .email_client import EmailClient
from .storage_client import StorageClient

__all__ = ['BadgeProcessor', 'EmailClient', 'StorageClient']
