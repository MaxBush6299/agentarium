"""
Models API

Provides endpoints for retrieving available AI models and their deployment names.
Allows frontend to dynamically populate model selectors with available deployments.

Endpoints:
- GET /api/models - List all available Azure OpenAI model deployments
- GET /api/models/info - Get detailed info about model capabilities and endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelDeployment(BaseModel):
    """Information about an available model deployment"""
    deployment_name: str = Field(..., description="Azure OpenAI deployment name")
    model_id: str = Field(..., description="Model identifier (e.g., gpt-4, gpt-4o)")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities (e.g., 'vision', 'function_calling')")
    context_window: Optional[int] = Field(default=None, description="Context window size in tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "deployment_name": "gpt-4-deployment",
                "model_id": "gpt-4",
                "description": "GPT-4 with 8K context window",
                "capabilities": ["function_calling", "json_mode"],
                "context_window": 8192
            }
        }


class ModelListResponse(BaseModel):
    """Response with list of available model deployments"""
    models: List[ModelDeployment]
    total: int
    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    api_version: str = Field(..., description="Azure OpenAI API version")


class ModelInfo(BaseModel):
    """Detailed information about models and endpoints"""
    available_models: List[ModelDeployment]
    azure_openai_endpoint: str
    api_version: str
    default_model: str
    api_key_configured: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "available_models": [
                    {
                        "deployment_name": "gpt-4-deployment",
                        "model_id": "gpt-4",
                        "description": "GPT-4 model",
                        "capabilities": ["function_calling"],
                        "context_window": 8192
                    }
                ],
                "azure_openai_endpoint": "https://example.openai.azure.com/",
                "api_version": "2025-03-01-preview",
                "default_model": "gpt-4",
                "api_key_configured": True
            }
        }


# Hardcoded list of known Azure OpenAI model deployments
# These are typical deployment names - can be customized per environment via .env
KNOWN_DEPLOYMENTS: List[Dict[str, Any]] = [
    {
        "deployment_name": "gpt-4",
        "model_id": "gpt-4",
        "description": "GPT-4 model",
        "capabilities": ["function_calling", "json_mode", "vision"],
        "context_window": 8192
    },
    {
        "deployment_name": "gpt-4-turbo",
        "model_id": "gpt-4-turbo",
        "description": "GPT-4 Turbo model with 128K context",
        "capabilities": ["function_calling", "json_mode", "vision"],
        "context_window": 128000
    },
    {
        "deployment_name": "gpt-4o",
        "model_id": "gpt-4o",
        "description": "GPT-4o model - latest and most capable",
        "capabilities": ["function_calling", "json_mode", "vision"],
        "context_window": 128000
    },
    {
        "deployment_name": "gpt-35-turbo",
        "model_id": "gpt-3.5-turbo",
        "description": "GPT-3.5 Turbo model",
        "capabilities": ["function_calling"],
        "context_window": 4096
    },
]


@router.get(
    "",
    response_model=ModelListResponse,
    summary="List available model deployments",
    description="Get list of all available Azure OpenAI model deployments that can be used by agents"
)
async def list_models() -> ModelListResponse:
    """
    List all available Azure OpenAI model deployments.
    
    Returns a list of deployments that are configured and available for use.
    This includes deployment names that can be passed to agent configuration.
    
    Returns:
        ModelListResponse with list of available deployments
    """
    try:
        # Convert known deployments to ModelDeployment objects
        models = [ModelDeployment(**dep) for dep in KNOWN_DEPLOYMENTS]
        
        logger.debug(f"Returning {len(models)} available model deployments")
        
        return ModelListResponse(
            models=models,
            total=len(models),
            endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
    except Exception as e:
        logger.error(f"Failed to list model deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available models"
        )


@router.get(
    "/info",
    response_model=ModelInfo,
    summary="Get detailed model and endpoint information",
    description="Get comprehensive information about available models and Azure OpenAI configuration"
)
async def get_model_info() -> ModelInfo:
    """
    Get detailed information about available models and Azure OpenAI endpoints.
    
    Includes:
    - List of available model deployments
    - Azure OpenAI endpoint URL
    - API version being used
    - Default model configuration
    - Whether API key is configured
    
    Returns:
        ModelInfo with comprehensive configuration details
    """
    try:
        models = [ModelDeployment(**dep) for dep in KNOWN_DEPLOYMENTS]
        
        # Check if API key is configured
        has_api_key = bool(settings.AZURE_OPENAI_KEY or settings.KEYVAULT_URL)
        
        logger.debug("Returning model configuration info")
        
        return ModelInfo(
            available_models=models,
            azure_openai_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            default_model=settings.DEFAULT_MODEL,
            api_key_configured=has_api_key
        )
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model information"
        )


def get_deployment_names() -> List[str]:
    """
    Get list of deployment names only.
    
    Useful for quick lookups without full model details.
    
    Returns:
        List of deployment name strings
    """
    return [dep["deployment_name"] for dep in KNOWN_DEPLOYMENTS]


def get_model_by_deployment(deployment_name: str) -> Optional[ModelDeployment]:
    """
    Get model information by deployment name.
    
    Args:
        deployment_name: The Azure OpenAI deployment name
        
    Returns:
        ModelDeployment if found, None otherwise
    """
    for dep in KNOWN_DEPLOYMENTS:
        if dep["deployment_name"] == deployment_name:
            return ModelDeployment(**dep)
    return None
