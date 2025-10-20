"""
Entra ID (Azure AD) authentication and authorization for FastAPI.
Provides JWT validation, user claims extraction, and role-based access control.
"""

import logging
import json
from typing import Optional, Dict, Any
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class AuthContext:
    """
    Represents the authenticated user context extracted from JWT claims.
    """
    
    def __init__(self, token: str, claims: Dict[str, Any]):
        """
        Initialize auth context.
        
        Args:
            token: The JWT token
            claims: Decoded claims from the token
        """
        self.token = token
        self.claims = claims
        self.user_id = claims.get("oid")  # Object ID
        self.user_principal = claims.get("upn")  # User Principal Name
        self.email = claims.get("email")
        self.name = claims.get("name")
        self.roles = claims.get("roles", [])
        self.app_roles = claims.get("appRoles", [])
        self.tenant_id = claims.get("tid")
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles or role in self.app_roles
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.has_role("Admin")
    
    def __repr__(self) -> str:
        return f"AuthContext(user_id={self.user_id}, email={self.email}, roles={self.roles})"


class AuthenticationError(Exception):
    """Base authentication error."""
    pass


class TokenValidator:
    """
    Validates JWT tokens from Entra ID.
    In development, performs basic validation.
    In production, should validate against Azure AD public keys.
    """
    
    def __init__(self, tenant_id: str, client_id: str, is_development: bool = False):
        """
        Initialize token validator.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application client ID
            is_development: If True, perform minimal validation (dev mode)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.is_development = is_development
    
    def validate_token(self, token: str) -> AuthContext:
        """
        Validate JWT token and extract claims.
        
        Args:
            token: JWT token string
            
        Returns:
            AuthContext with decoded claims
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # In production, use PyJWT with Azure AD public keys
            # For now, simple validation in dev mode
            if self.is_development:
                logger.warning("Using development token validation - not suitable for production")
                # In dev mode, just parse the JWT without verification
                # This is for testing only - NEVER use in production
                claims = self._parse_jwt_claims_dev(token)
            else:
                # Production: validate against Azure AD public keys
                claims = self._validate_jwt_signature(token)
            
            # Basic claim validation
            if claims.get("aud") != self.client_id:
                raise AuthenticationError("Token audience does not match client ID")
            
            if claims.get("tid") != self.tenant_id:
                logger.warning(f"Token tenant ID {claims.get('tid')} does not match expected {self.tenant_id}")
            
            return AuthContext(token, claims)
        
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    def _parse_jwt_claims_dev(self, token: str) -> Dict[str, Any]:
        """
        Parse JWT claims without signature verification.
        FOR DEVELOPMENT ONLY - DO NOT USE IN PRODUCTION.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded claims dictionary
        """
        try:
            import base64
            # JWT format: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                raise AuthenticationError("Invalid token format")
            
            # Decode payload (add padding if necessary)
            payload = parts[1]
            # Add padding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
            logger.debug(f"Parsed JWT claims (dev mode): {list(claims.keys())}")
            return claims
        
        except Exception as e:
            raise AuthenticationError(f"Failed to parse JWT: {str(e)}")
    
    def _validate_jwt_signature(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT signature against Azure AD public keys.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded claims dictionary
            
        Raises:
            AuthenticationError: If signature is invalid
        """
        # This would use PyJWT library to validate against Azure AD's public keys
        # For now, placeholder that would be implemented in production
        raise NotImplementedError(
            "Production JWT validation requires Azure AD public key validation. "
            "Please implement this using PyJWT and Azure AD metadata endpoints."
        )


@lru_cache(maxsize=1)
def get_token_validator(tenant_id: str, client_id: str, is_development: bool = False) -> TokenValidator:
    """
    Get or create a cached token validator instance.
    """
    return TokenValidator(tenant_id, client_id, is_development)


async def get_current_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(security),
    tenant_id: str = None,
    client_id: str = None,
    is_development: bool = False,
) -> AuthContext:
    """
    FastAPI dependency for extracting and validating the current user from the JWT token.
    
    Args:
        credentials: HTTP bearer token from request
        tenant_id: Azure AD tenant ID
        client_id: Application client ID
        is_development: If True, use development validation
        
    Returns:
        AuthContext with validated user information
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        logger.warning("Missing authorization credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        validator = get_token_validator(tenant_id, client_id, is_development)
        auth_context = validator.validate_token(credentials.credentials)
        logger.debug(f"User authenticated: {auth_context}")
        return auth_context
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    """
    FastAPI dependency to require admin role.
    Use this on endpoints that need admin access.
    
    Args:
        auth: Authenticated user context
        
    Returns:
        AuthContext if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not auth.is_admin():
        logger.warning(f"Admin access denied for user {auth.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return auth


async def require_role(role: str):
    """
    Factory function to create a role-based access control dependency.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(auth: AuthContext = Depends(require_role("Moderator"))):
            ...
    
    Args:
        role: Required role name
        
    Returns:
        FastAPI dependency that enforces the role
    """
    async def _require_role(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        if not auth.has_role(role):
            logger.warning(f"Access denied for user {auth.user_id}: missing role {role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {role} required"
            )
        return auth
    
    return _require_role
