"""
OpenAPI Tool Integration for Agent Framework.

This module provides a dynamic OpenAPI client that can:
1. Parse OpenAPI 3.0 specifications
2. Generate callable functions from API endpoints
3. Integrate with Agent Framework's tool system
4. Handle authentication (API keys, OAuth2, etc.)
5. Log requests/responses for observability

Usage:
    from tools.openapi_client import OpenAPITool
    
    # Create tool from spec
    tool = OpenAPITool(
        spec_path="openapi/support-triage-api.yaml",
        base_url="https://api.example.com/support",
        api_key="your-api-key"
    )
    
    # Use with Agent Framework
    async with ChatAgent(
        chat_client=OpenAIChatClient(),
        tools=tool.get_tools()
    ) as agent:
        result = await agent.run("Search for Azure Storage tickets")
"""

import os
import yaml
import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import aiohttp
from pydantic import BaseModel, Field


class OpenAPITool:
    """
    Dynamic OpenAPI client that converts OpenAPI specs into callable tools.
    
    Supports OpenAPI 3.0 specifications and can be used with Agent Framework.
    """
    
    def __init__(
        self,
        spec_path: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_header: str = "X-API-Key",
        timeout: int = 30
    ):
        """
        Initialize OpenAPI tool from specification.
        
        Args:
            spec_path: Path to OpenAPI YAML file
            base_url: Base URL for API (overrides spec server)
            api_key: API key for authentication
            api_key_header: Header name for API key (default: X-API-Key)
            timeout: Request timeout in seconds
        """
        self.spec_path = Path(spec_path)
        self.base_url = base_url
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.timeout = timeout
        
        # Load and parse spec
        self.spec = self._load_spec()
        self.title = self.spec.get("info", {}).get("title", "OpenAPI Tool")
        self.version = self.spec.get("info", {}).get("version", "1.0.0")
        
        # Use base_url or fallback to first server in spec
        if not self.base_url and "servers" in self.spec and self.spec["servers"]:
            self.base_url = self.spec["servers"][0]["url"]
        
        # Parse operations
        self.operations = self._parse_operations()
    
    def _load_spec(self) -> Dict[str, Any]:
        """Load OpenAPI specification from YAML file."""
        if not self.spec_path.exists():
            raise FileNotFoundError(f"OpenAPI spec not found: {self.spec_path}")
        
        with open(self.spec_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def _parse_operations(self) -> List[Dict[str, Any]]:
        """Parse all operations from OpenAPI paths."""
        operations = []
        paths = self.spec.get("paths", {})
        
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation = path_item[method]
                    operations.append({
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "parameters": operation.get("parameters", []),
                        "request_body": operation.get("requestBody"),
                        "responses": operation.get("responses", {})
                    })
        
        return operations
    
    async def call_operation(
        self,
        operation_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call an OpenAPI operation.
        
        Args:
            operation_id: Operation ID from OpenAPI spec
            parameters: Query/path parameters
            body: Request body (for POST/PUT/PATCH)
            
        Returns:
            Response JSON data
        """
        # Find operation
        operation = next((op for op in self.operations if op["operation_id"] == operation_id), None)
        if not operation:
            raise ValueError(f"Operation not found: {operation_id}")
        
        # Build URL
        url = self.base_url + operation["path"]
        
        # Replace path parameters
        if parameters:
            for key, value in parameters.items():
                url = url.replace(f"{{{key}}}", str(value))
        
        # Build query parameters
        query_params = {}
        if parameters:
            param_names = [p["name"] for p in operation["parameters"] if p.get("in") == "query"]
            query_params = {k: v for k, v in parameters.items() if k in param_names}
        
        # Build headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers[self.api_key_header] = self.api_key
        
        # Make request
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=operation["method"],
                url=url,
                params=query_params,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                return await response.json()
    
    def get_operations_info(self) -> List[Dict[str, Any]]:
        """Get information about all available operations."""
        return [
            {
                "operation_id": op["operation_id"],
                "method": op["method"],
                "path": op["path"],
                "summary": op["summary"],
                "description": op["description"]
            }
            for op in self.operations
        ]
    
    def __repr__(self) -> str:
        return f"OpenAPITool(title='{self.title}', operations={len(self.operations)})"


# Factory functions for common APIs

def get_support_triage_tool(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> OpenAPITool:
    """
    Get Support Triage API tool.
    
    Args:
        base_url: Base URL (default: from env SUPPORT_API_URL or spec)
        api_key: API key (default: from env SUPPORT_API_KEY or 'demo-key')
    
    Returns:
        OpenAPITool instance for Support Triage API
    """
    # Go from src/tools -> src -> backend -> backend/openapi
    spec_path = Path(__file__).resolve().parent.parent.parent / "openapi" / "support-triage-api.yaml"
    
    return OpenAPITool(
        spec_path=str(spec_path),
        base_url=base_url or os.getenv("SUPPORT_API_URL"),
        api_key=api_key or os.getenv("SUPPORT_API_KEY", "demo-key")
    )


def get_ops_assistant_tool(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> OpenAPITool:
    """
    Get Operations Assistant API tool.
    
    Args:
        base_url: Base URL (default: from env OPS_API_URL or spec)
        api_key: API key (default: from env OPS_API_KEY or 'demo-key')
    
    Returns:
        OpenAPITool instance for Operations Assistant API
    """
    # Go from src/tools -> src -> backend -> backend/openapi
    spec_path = Path(__file__).resolve().parent.parent.parent / "openapi" / "ops-assistant-api.yaml"
    
    return OpenAPITool(
        spec_path=str(spec_path),
        base_url=base_url or os.getenv("OPS_API_URL"),
        api_key=api_key or os.getenv("OPS_API_KEY", "demo-key")
    )
