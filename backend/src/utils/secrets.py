"""
Azure Key Vault integration for secret management.
Supports both local development (Azure CLI credentials) and production (Managed Identity).
"""

import logging
from typing import Optional
from functools import lru_cache

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Manages secrets from Azure Key Vault.
    Uses DefaultAzureCredential for authentication (Managed Identity in production, CLI credentials in dev).
    """
    
    def __init__(self, keyvault_url: str, use_cli_credential: bool = False):
        """
        Initialize the Secret Manager.
        
        Args:
            keyvault_url: The URL of the Key Vault (e.g., https://my-keyvault.vault.azure.net/)
            use_cli_credential: If True, use AzureCliCredential (for local dev). 
                              If False, use DefaultAzureCredential (Managed Identity in production).
        """
        self.keyvault_url = keyvault_url
        
        if not keyvault_url:
            logger.warning("Key Vault URL not provided. Secret retrieval will be disabled.")
            self.client = None
            return
        
        # Choose credential type based on environment
        if use_cli_credential:
            credential = AzureCliCredential()
            logger.info("Using Azure CLI credentials for Key Vault authentication")
        else:
            credential = DefaultAzureCredential()
            logger.info("Using DefaultAzureCredential for Key Vault authentication")
        
        self.client = SecretClient(vault_url=keyvault_url, credential=credential)
        logger.info(f"SecretManager initialized for {keyvault_url}")
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from Key Vault.
        
        Args:
            secret_name: The name of the secret
            default: Default value if secret is not found
            
        Returns:
            The secret value or default if not found
        """
        if not self.client:
            logger.debug(f"Key Vault client not initialized, returning default for {secret_name}")
            return default
        
        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"Successfully retrieved secret: {secret_name}")
            return secret.value
        except ResourceNotFoundError:
            logger.warning(f"Secret not found in Key Vault: {secret_name}")
            return default
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
            return default
    
    def list_secrets(self) -> list[str]:
        """
        List all secrets in the Key Vault.
        
        Returns:
            List of secret names
        """
        if not self.client:
            logger.warning("Key Vault client not initialized, cannot list secrets")
            return []
        
        try:
            secrets = [secret.name for secret in self.client.list_properties_of_secrets()]
            logger.info(f"Listed {len(secrets)} secrets from Key Vault")
            return secrets
        except Exception as e:
            logger.error(f"Error listing secrets: {str(e)}")
            return []


# Global secret manager instance
_secret_manager: Optional[SecretManager] = None


def initialize_secrets(keyvault_url: str, use_cli_credential: bool = False) -> SecretManager:
    """
    Initialize the global secret manager.
    
    Args:
        keyvault_url: The URL of the Key Vault
        use_cli_credential: If True, use Azure CLI credentials (for local dev)
        
    Returns:
        The initialized SecretManager instance
    """
    global _secret_manager
    _secret_manager = SecretManager(keyvault_url, use_cli_credential)
    return _secret_manager


def get_secrets() -> Optional[SecretManager]:
    """
    Get the global secret manager instance.
    Returns None if not initialized.
    """
    return _secret_manager


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to retrieve a secret using the global secret manager.
    
    Args:
        secret_name: The name of the secret
        default: Default value if secret is not found
        
    Returns:
        The secret value or default if not found
    """
    if _secret_manager:
        return _secret_manager.get_secret(secret_name, default)
    return default
