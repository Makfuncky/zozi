# Azure Key Vault Integration for Secrets Management
# FREE tier: 10 secrets, 500 transactions/month
# Usage: Azure Key Vault is a paid service, but the free tier is sufficient for small deployments

"""
Azure Key Vault configuration for Zozi secrets management.

Usage:
1. Create Key Vault: az keyvault create --name zozi-kv --resource-group zozi-rg --location eastus
2. Set secrets: az keyvault secret set --vault-name zozi-kv --name SECRET_KEY --value "your-secret"
3. Grant app access: az keyvault set-policy --name zozi-kv --spn <app-id> --secret-permissions get list

Configuration in .env:
AZURE_KEY_VAULT_URL=https://zozi-kv.vault.azure.net/
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("zozi")


def get_key_vault_config() -> dict:
    """Return Key Vault configuration from environment."""
    return {
        "key_vault_url": os.environ.get("AZURE_KEY_VAULT_URL", ""),
        "client_id": os.environ.get("AZURE_CLIENT_ID", ""),
        "client_secret": os.environ.get("AZURE_CLIENT_SECRET", ""),
        "tenant_id": os.environ.get("AZURE_TENANT_ID", ""),
    }


def is_key_vault_enabled() -> bool:
    """Check if Key Vault is configured."""
    return bool(os.environ.get("AZURE_KEY_VAULT_URL", "").strip())


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a secret from Azure Key Vault with fallback to environment variables.
    
    Args:
        secret_name: Name of the secret to retrieve
        default: Default value if secret not found
        
    Returns:
        The secret value or default
    """
    if is_key_vault_enabled():
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            config = get_key_vault_config()
            credential = DefaultAzureCredential()
            client = SecretClient(
                vault_url=config["key_vault_url"],
                credential=credential
            )
            retrieved_secret = client.get_secret(secret_name)
            return retrieved_secret.value
        except Exception as e:
            logger.warning(f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}")
            return default
    
    env_mapping = {
        "SECRET_KEY": "SECRET_KEY",
        "FIELD_ENCRYPTION_KEY": "FIELD_ENCRYPTION_KEY",
        "STRIPE_SECRET_KEY": "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY": "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET": "STRIPE_WEBHOOK_SECRET",
    }
    
    env_var = env_mapping.get(secret_name, secret_name)
    return os.environ.get(env_var, default)


def get_key_vault_credentials() -> dict:
    """Get Key Vault credentials with fallback chain."""
    if is_key_vault_enabled():
        return get_key_vault_config()
    
    return {
        "key_vault_url": "",
        "client_id": "",
        "client_secret": "",
        "tenant_id": "",
    }


def is_production_ready() -> bool:
    """Check if the application is configured for production use."""
    if not is_key_vault_enabled():
        logger.warning(
            "Azure Key Vault not configured. Using environment variables for secrets. "
            "This is NOT recommended for production."
        )
        return False
    return True
