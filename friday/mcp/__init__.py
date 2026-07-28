"""MCP (Model Context Protocol) layer for FRIDAY."""

from friday.mcp.client import MCPClient
from friday.mcp.protocol import MCPError, MCPNotification, MCPRequest, MCPResponse
from friday.mcp.server import MCPServer
from friday.mcp.transport import (
    InProcessTransport,
    MCPTransport,
    SSETransport,
    StdioTransport,
    StreamableHTTPTransport,
)

__all__ = [
    "MCPClient",
    "MCPError",
    "MCPNotification",
    "MCPRequest",
    "MCPResponse",
    "MCPServer",
    "MCPTransport",
    "InProcessTransport",
    "SSETransport",
    "StdioTransport",
    "StreamableHTTPTransport",
]
