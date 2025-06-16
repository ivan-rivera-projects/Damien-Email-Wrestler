"""
Middleware package for Damien MCP Server optimizations.

This package contains middleware components that enhance the MCP server's
functionality for better compatibility with different Claude interfaces.
"""

from .timeout_router import TimeoutAwareRouter, timeout_router

__all__ = ["TimeoutAwareRouter", "timeout_router"]