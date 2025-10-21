"""
OAuth Token Manager for MCP Server Authentication.

This module provides a robust token management system for OAuth 2.0 client credentials flow.
It handles token acquisition, caching, automatic refresh, and thread-safe operations.

Features:
- Automatic token refresh before expiration
- Thread-safe token caching
- Configurable refresh buffer (default: refresh 5 minutes before expiration)
- Detailed error handling and logging
- Support for multiple token sources (different client IDs)

Usage:
    # Create a token manager
    token_manager = OAuthTokenManager(
        token_url="https://login.microsoftonline.com/.../oauth2/token",
        client_id="your-client-id",
        client_secret="your-client-secret",
        scope="api://your-app/.default"
    )
    
    # Get a fresh token (will use cache if valid, or refresh if needed)
    token = token_manager.get_token()
    
    # Use as a callable for MCP tools
    def get_auth_header():
        return {"Authorization": f"Bearer {token_manager.get_token()}"}
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TokenData:
    """Container for OAuth token data with expiration tracking."""
    
    access_token: str
    expires_at: float  # Unix timestamp
    token_type: str = "Bearer"
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """
        Check if token is expired or will expire soon.
        
        Args:
            buffer_seconds: Seconds before expiration to consider token expired (default: 5 minutes)
            
        Returns:
            True if token is expired or will expire within buffer_seconds
        """
        return time.time() >= (self.expires_at - buffer_seconds)
    
    def time_until_expiry(self) -> float:
        """Get seconds until token expiry."""
        return max(0, self.expires_at - time.time())
    
    def __str__(self) -> str:
        """String representation with masked token."""
        expiry_time = datetime.fromtimestamp(self.expires_at).strftime("%Y-%m-%d %H:%M:%S")
        token_preview = f"{self.access_token[:10]}...{self.access_token[-10:]}" if len(self.access_token) > 20 else "***"
        return f"TokenData(token={token_preview}, expires={expiry_time}, valid_for={self.time_until_expiry():.0f}s)"


class OAuthTokenManager:
    """
    Thread-safe OAuth token manager with automatic refresh.
    
    This class manages OAuth 2.0 client credentials tokens, handling acquisition,
    caching, and automatic refresh. It's designed for use with Azure AD/Entra ID
    but works with any OAuth 2.0 provider supporting client credentials flow.
    
    Attributes:
        token_url: OAuth token endpoint URL
        client_id: OAuth client ID
        client_secret: OAuth client secret
        scope: OAuth scope(s) to request
        refresh_buffer_seconds: Seconds before expiration to refresh token (default: 300 = 5 minutes)
    """
    
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str,
        refresh_buffer_seconds: int = 300,
    ):
        """
        Initialize OAuth token manager.
        
        Args:
            token_url: OAuth 2.0 token endpoint (e.g., https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token)
            client_id: Application (client) ID from Azure AD app registration
            client_secret: Client secret from Azure AD app registration
            scope: Scope for the token (e.g., "api://your-app-id/.default")
            refresh_buffer_seconds: Seconds before expiration to proactively refresh (default: 300 = 5 min)
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.refresh_buffer_seconds = refresh_buffer_seconds
        
        # Thread-safe token cache
        self._token: Optional[TokenData] = None
        self._lock = Lock()
        
        logger.info(
            f"Initialized OAuthTokenManager for client_id={client_id[:8]}... "
            f"with refresh buffer={refresh_buffer_seconds}s"
        )
    
    def _acquire_token(self) -> TokenData:
        """
        Acquire a new access token from the OAuth provider.
        
        This method performs the actual OAuth 2.0 client credentials flow request.
        
        Returns:
            TokenData object containing the new token and expiration
            
        Raises:
            ConnectionError: If token acquisition fails
            ValueError: If response doesn't contain required fields
        """
        logger.debug(f"Acquiring new OAuth token from {self.token_url}")
        
        try:
            response = httpx.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": self.scope,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,  # 30 second timeout for token acquisition
            )
            
            if response.status_code != 200:
                error_msg = f"OAuth token request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', 'unknown')}: {error_data.get('error_description', response.text)}"
                except Exception:
                    error_msg += f" - {response.text}"
                
                logger.error(error_msg)
                raise ConnectionError(error_msg)
            
            token_response = response.json()
            
            # Extract token data
            access_token = token_response.get("access_token")
            if not access_token:
                raise ValueError("Token response missing 'access_token' field")
            
            # Calculate expiration time - expires_in may be string or int
            expires_in_raw = token_response.get("expires_in", 3600)
            try:
                expires_in = int(expires_in_raw) if expires_in_raw else 3600
            except (ValueError, TypeError):
                logger.warning(f"Invalid expires_in value '{expires_in_raw}', defaulting to 3600 seconds")
                expires_in = 3600
            
            expires_at = time.time() + expires_in
            
            token_type = token_response.get("token_type", "Bearer")
            
            token_data = TokenData(
                access_token=access_token,
                expires_at=expires_at,
                token_type=token_type,
            )
            
            expiry_datetime = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                f"Successfully acquired OAuth token (expires at {expiry_datetime}, "
                f"valid for {expires_in}s)"
            )
            
            return token_data
            
        except httpx.RequestError as e:
            error_msg = f"Network error during token acquisition: {e}"
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        except (KeyError, ValueError) as e:
            error_msg = f"Invalid token response format: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        This is the main method to use when you need a token. It will:
        1. Return cached token if still valid
        2. Refresh token if expired or expiring soon
        3. Acquire new token if none exists
        
        Thread-safe and can be called concurrently.
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
            
        Returns:
            Valid access token string
            
        Raises:
            ConnectionError: If token acquisition fails
        """
        with self._lock:
            # Check if we need a new token
            needs_refresh = (
                force_refresh
                or self._token is None
                or self._token.is_expired(self.refresh_buffer_seconds)
            )
            
            if needs_refresh:
                if self._token:
                    logger.debug(
                        f"Token expired or expiring soon (time until expiry: {self._token.time_until_expiry():.0f}s), "
                        "acquiring new token"
                    )
                else:
                    logger.debug("No cached token, acquiring new token")
                
                self._token = self._acquire_token()
            else:
                logger.debug(
                    f"Using cached token (time until expiry: {self._token.time_until_expiry():.0f}s)"
                )
            
            return self._token.access_token
    
    def get_auth_header(self) -> dict[str, str]:
        """
        Get Authorization header with fresh token.
        
        Convenience method that returns a dict ready to use as HTTP headers.
        
        Returns:
            Dict with Authorization header: {"Authorization": "Bearer <token>"}
        """
        token = self.get_token()
        return {"Authorization": f"Bearer {token}"}
    
    def invalidate_token(self) -> None:
        """
        Invalidate the cached token, forcing refresh on next request.
        
        Useful if you know the token is invalid (e.g., received 401 response).
        """
        with self._lock:
            if self._token:
                logger.info("Invalidating cached token")
                self._token = None
    
    def get_token_info(self) -> Optional[dict]:
        """
        Get information about the current cached token.
        
        Returns:
            Dict with token info, or None if no token cached
        """
        with self._lock:
            if not self._token:
                return None
            
            return {
                "expires_at": datetime.fromtimestamp(self._token.expires_at).isoformat(),
                "time_until_expiry_seconds": self._token.time_until_expiry(),
                "is_expired": self._token.is_expired(self.refresh_buffer_seconds),
                "token_type": self._token.token_type,
            }
    
    def __call__(self) -> str:
        """
        Make the token manager callable, returning a fresh token.
        
        This allows using the token manager directly as a callable:
            token = token_manager()
        """
        return self.get_token()


# Global token manager cache for reuse across the application
_token_managers: dict[str, OAuthTokenManager] = {}
_token_managers_lock = Lock()


def get_token_manager(
    token_url: str,
    client_id: str,
    client_secret: str,
    scope: str,
    refresh_buffer_seconds: int = 300,
) -> OAuthTokenManager:
    """
    Get or create a token manager for the given credentials.
    
    This function maintains a global cache of token managers, keyed by client_id.
    This ensures we don't create multiple token managers for the same client,
    which could lead to unnecessary token acquisitions.
    
    Args:
        token_url: OAuth token endpoint URL
        client_id: OAuth client ID
        client_secret: OAuth client secret
        scope: OAuth scope
        refresh_buffer_seconds: Seconds before expiration to refresh
        
    Returns:
        OAuthTokenManager instance (cached if exists, new if not)
    """
    with _token_managers_lock:
        # Use client_id as cache key
        if client_id not in _token_managers:
            logger.info(f"Creating new token manager for client_id={client_id[:8]}...")
            _token_managers[client_id] = OAuthTokenManager(
                token_url=token_url,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
                refresh_buffer_seconds=refresh_buffer_seconds,
            )
        else:
            logger.debug(f"Reusing cached token manager for client_id={client_id[:8]}...")
        
        return _token_managers[client_id]
