"""Agents package."""

# Lazy import to avoid import errors if agent-framework is not installed
def __getattr__(name):
    if name == "DemoBaseAgent":
        from .base import DemoBaseAgent
        return DemoBaseAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DemoBaseAgent",
]
