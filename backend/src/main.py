"""
Main FastAPI application for the Agent Framework backend.
Initializes the app with middleware, dependencies, and routes.
Version: 1.0.1
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.utils.secrets import initialize_secrets
from src.persistence.cosmos_client import initialize_cosmos
from src.a2a.server import router as a2a_router, well_known_router
from src.a2a.api import router as agent_cards_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress MCP async generator cleanup error (harmless on connection close)
asyncio_logger = logging.getLogger("asyncio")
asyncio_logger.setLevel(logging.CRITICAL)  # Only show critical errors, filter out the generator cleanup warnings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    Handles initialization of external services (Key Vault, Cosmos DB).
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Local Dev Mode: {settings.LOCAL_DEV_MODE}")
    
    try:
        # Initialize Key Vault if configured
        if settings.KEYVAULT_URL:
            initialize_secrets(
                settings.KEYVAULT_URL,
                use_cli_credential=settings.LOCAL_DEV_MODE
            )
            logger.info("Key Vault initialized")
        else:
            logger.warning("KEYVAULT_URL not configured - secret retrieval disabled")
        
        # Initialize Cosmos DB
        cosmos_client = initialize_cosmos(
            endpoint=settings.COSMOS_ENDPOINT,
            database_name=settings.COSMOS_DATABASE_NAME,
            key=settings.COSMOS_KEY,
            connection_string=settings.COSMOS_CONNECTION_STRING,
        )
        
        # Perform health check
        if cosmos_client.health_check():
            logger.info("Cosmos DB connected and healthy")
        else:
            logger.warning("Cosmos DB health check failed")
        
        # Seed default agents
        try:
            from src.persistence.seed_agents import seed_agents
            from src.persistence.agents import get_agent_repository
            from src.agents.tool_registry import register_default_tools
            
            # Register all built-in tools first
            print("[MAIN.PY] About to register built-in tools...")
            logger.info("Registering built-in tools...")
            register_default_tools()
            print("[MAIN.PY] Built-in tools registered successfully")
            logger.info("Built-in tools registered")
            
            # Load custom tools from Cosmos DB (MUST complete before seeding agents)
            try:
                from src.api.custom_tools import load_custom_tools_from_db
                print("[MAIN.PY] About to load custom tools from Cosmos DB...")
                logger.info("Loading custom tools from Cosmos DB...")
                
                # Custom tools must be loaded BEFORE seeding agents
                # so that agents can reference them
                # lifespan is async, so we can await here
                await load_custom_tools_from_db()
                
                print("[MAIN.PY] Custom tools loaded successfully")
                logger.info("Custom tools loaded from Cosmos DB")
            except Exception as e:
                logger.warning(f"Failed to load custom tools from Cosmos DB: {e}")
                # Continue - custom tools are optional
            
            print(f"[MAIN.PY] About to seed agents...")
            seed_result = seed_agents()
            logger.info(
                f"Agent seeding: {seed_result['created']} created, "
                f"{seed_result['skipped']} skipped, {seed_result['total']} total"
            )
            
            # Clean up any duplicate agents
            print("[MAIN.PY] Cleaning up duplicate agents...")
            repo = get_agent_repository()
            repo.cleanup_duplicate_agents()
            print("[MAIN.PY] Duplicate agents cleanup complete")
            # This helps with Cosmos DB eventual consistency issues
            logger.info("Verifying agents are accessible from backend's client...")
            repo = get_agent_repository()
            all_agents = repo.list()
            logger.info(f"Backend can see {len(all_agents)} agents: {[a.id for a in all_agents]}")
            
        except Exception as e:
            logger.error(f"Failed to seed agents: {e}")
            # Continue - seeding is not critical for app functionality
    
    except Exception as e:
        logger.warning(f"Error during startup: {str(e)}")
        logger.warning("Continuing in degraded mode - some features may use mock data")
        # In production, you might want to fail startup here
        # For development, we'll continue with mock data fallback
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Agent Framework Backend - Multi-Agent Chat with MCP Integration",
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"],
)


# Include A2A Protocol Routers
app.include_router(well_known_router)  # Agent card at /.well-known/agent.json
app.include_router(a2a_router)  # A2A endpoints at /a2a
app.include_router(agent_cards_router)  # Agent card management API at /api/agent-cards
logger.info("A2A Protocol routers registered")

# Include Chat API Router
from src.api.chat import router as chat_router
app.include_router(chat_router)  # Chat API at /api/agents/{agent_id}/...
logger.info("Chat API router registered")

# Include Agent Management API Router
from src.api.agents import router as agents_router
app.include_router(agents_router)  # Agent Management API at /api/agents
logger.info("Agent Management API router registered")

# Include Custom Tools API Router
from src.api.custom_tools import router as custom_tools_router
app.include_router(custom_tools_router)  # Custom Tools API at /api/custom-tools
logger.info("Custom Tools API router registered")

# Include Models API Router
from src.api.models import router as models_router
app.include_router(models_router)  # Models API at /api/models
logger.info("Models API router registered")

# Include Workflows API Router
from src.api.workflows import router as workflows_router
app.include_router(workflows_router)  # Workflows API at /api/workflows
logger.info("Workflows API router registered")


# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancing.
    Returns status of the application and its dependencies.
    """
    from src.persistence.cosmos_client import get_cosmos
    from src.utils.secrets import get_secrets
    
    cosmos = get_cosmos()
    secrets = get_secrets()
    
    cosmos_healthy = cosmos.health_check() if cosmos else False
    
    status_code = 200 if cosmos_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if cosmos_healthy else "degraded",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "dependencies": {
                "cosmos_db": "connected" if cosmos_healthy else "disconnected",
                "key_vault": "configured" if secrets else "not configured",
            }
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "api_prefix": settings.API_PREFIX,
        "documentation": "/docs",
    }


# Error Handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid value: {str(exc)}"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
