"""
Configuration and environment variable handling for the Agent Framework backend.
Loads configuration from environment variables with sensible defaults for local development.
"""

import os
from functools import lru_cache
from typing import Optional
from pathlib import Path

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Agent Framework Demo"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, staging, production
    LOCAL_DEV_MODE: bool = os.getenv("LOCAL_DEV_MODE", "true").lower() == "true"
    
    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api"
    RELOAD: bool = LOCAL_DEV_MODE
    
    # CORS Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ALLOWED_ORIGINS: list[str] = [FRONTEND_URL]
    
    # Azure Configuration
    AZURE_SUBSCRIPTION_ID: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_REGION: str = os.getenv("AZURE_REGION", "eastus")
    
    # Cosmos DB Configuration
    COSMOS_ENDPOINT: str = os.getenv("COSMOS_ENDPOINT", "https://localhost:8081")
    COSMOS_DATABASE_NAME: str = os.getenv("COSMOS_DATABASE_NAME", "agents-db")
    COSMOS_KEY: Optional[str] = os.getenv("COSMOS_KEY", None)  # For emulator/local testing
    COSMOS_CONNECTION_STRING: Optional[str] = os.getenv("COSMOS_CONNECTION_STRING", None)
    
    # Key Vault Configuration
    KEYVAULT_URL: str = os.getenv("KEYVAULT_URL", "")
    KEYVAULT_SECRET_COSMOS_KEY: str = "cosmosdb-primary-key"
    KEYVAULT_SECRET_OPENAI_KEY: str = "openai-api-key"
    KEYVAULT_SECRET_MSSQL_KEY: str = "mssql-connection-string"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_KEY: Optional[str] = os.getenv("AZURE_OPENAI_KEY", None)
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")
    
    # Model Configuration
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
    
    # Model to Azure Deployment Name Mapping
    # Map model identifiers to actual Azure OpenAI deployment names
    MODEL_DEPLOYMENT_MAPPING: dict = {
        "gpt-4o": os.getenv("DEPLOYMENT_NAME_GPT4O", "gpt-4o"),
        "gpt-4.1": os.getenv("DEPLOYMENT_NAME_GPT41", "gpt-4.1"),
    }
    
    # MCP Server Configuration
    MCP_SERVERS: dict = {
        "microsoft_learn": {
            "endpoint": os.getenv("MCP_MICROSOFT_LEARN_ENDPOINT", "https://learn.microsoft.com/api/mcp"),
            "auth_type": "none",
        },
        "azure_mcp": {
            "endpoint": os.getenv("MCP_AZURE_ENDPOINT", "http://localhost:3000"),
            "auth_type": "managed_identity",
            "timeout": 30,
        },
        "adventure_mcp": {
            "endpoint": os.getenv("MCP_ADVENTURE_ENDPOINT", "https://mssqlmcp.azure-api.net"),
            "auth_type": "oauth2",
            "timeout": 30,
        },
    }
    
    # Application Insights Configuration
    APPINSIGHTS_INSTRUMENTATION_KEY: Optional[str] = os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY", None)
    APPINSIGHTS_CONNECTION_STRING: Optional[str] = os.getenv("APPINSIGHTS_CONNECTION_STRING", None)
    
    # Authentication Configuration
    ENTRA_ID_AUTHORITY: str = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}" if AZURE_TENANT_ID else ""
    ENTRA_ID_CLIENT_ID: str = os.getenv("ENTRA_ID_CLIENT_ID", "")
    ENTRA_ID_CLIENT_SECRET: Optional[str] = os.getenv("ENTRA_ID_CLIENT_SECRET", None)
    
    # API Scopes
    API_SCOPE: str = os.getenv("API_SCOPE", "https://localhost/api/.default")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if not LOCAL_DEV_MODE else "DEBUG")
    
    # Token Configuration (for cost control)
    TOKEN_BUDGET_PER_USER_PER_DAY: int = int(os.getenv("TOKEN_BUDGET_PER_USER_PER_DAY", "100000"))
    MAX_RESPONSE_TOKENS: int = int(os.getenv("MAX_RESPONSE_TOKENS", "2048"))
    
    # Feature Flags
    ENABLE_TELEMETRY_SAMPLING: bool = os.getenv("ENABLE_TELEMETRY_SAMPLING", "true").lower() == "true"
    ENABLE_A2A_PROTOCOL: bool = os.getenv("ENABLE_A2A_PROTOCOL", "true").lower() == "true"
    ENABLE_TOOL_CACHING: bool = os.getenv("ENABLE_TOOL_CACHING", "true").lower() == "true"
    
    class Config:
        case_sensitive = True
        env_file = ".env.local"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to avoid reloading settings on every request.
    """
    return Settings()


# Export settings instance for easy access
settings = get_settings()
