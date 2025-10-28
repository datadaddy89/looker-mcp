#!/usr/bin/env python3
"""
Remote MCP Server for Looker Conversational Analytics

This server implements the MCP Streamable HTTP transport protocol,
allowing Claude web app and other remote clients to connect via HTTP.

Supports both the legacy REST API and the new MCP remote protocol.
"""

import os
import json
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Import the MCP server tool
from looker_conversational_analytics_mcp import (
    looker_conversational_analytics,
    ConversationalAnalyticsInput,
    ResponseFormat,
    ExploreReference
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Looker MCP Remote Server",
    description="Remote MCP server for Looker Conversational Analytics with HTTP Streamable transport",
    version="1.0.0"
)

# Add CORS middleware with proper origin validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://claude.ai", "https://*.claude.ai"],  # Add your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id", "MCP-Protocol-Version"]
)

# Session storage (in production, use Redis or similar)
sessions: Dict[str, Dict[str, Any]] = {}

# Supported MCP protocol version
MCP_PROTOCOL_VERSION = "2024-11-05"


def create_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def validate_origin(request: Request) -> bool:
    """Validate request origin to prevent DNS rebinding attacks."""
    origin = request.headers.get("origin", "")
    allowed_origins = [
        "https://claude.ai",
        "http://localhost",
        "http://127.0.0.1"
    ]

    # Allow requests from Claude and localhost
    for allowed in allowed_origins:
        if origin.startswith(allowed):
            return True

    logger.warning(f"Rejected request from unauthorized origin: {origin}")
    return False


def create_jsonrpc_response(id: Any, result: Any = None, error: Any = None) -> Dict:
    """Create a JSON-RPC 2.0 response."""
    response = {
        "jsonrpc": "2.0",
        "id": id
    }

    if error:
        response["error"] = error
    else:
        response["result"] = result

    return response


def create_jsonrpc_error(code: int, message: str, data: Any = None) -> Dict:
    """Create a JSON-RPC error object."""
    error = {
        "code": code,
        "message": message
    }
    if data:
        error["data"] = data
    return error


@app.post("/mcp")
async def mcp_endpoint_post(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    mcp_protocol_version: Optional[str] = Header(MCP_PROTOCOL_VERSION, alias="MCP-Protocol-Version")
):
    """
    MCP endpoint for client-to-server messages (POST).

    Handles JSON-RPC requests and responses according to MCP specification.
    """
    # Validate origin
    if not validate_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    # Parse JSON-RPC request
    try:
        json_rpc_request = await request.json()
    except Exception as e:
        return JSONResponse(
            content=create_jsonrpc_response(
                id=None,
                error=create_jsonrpc_error(-32700, "Parse error", str(e))
            ),
            headers={"MCP-Protocol-Version": MCP_PROTOCOL_VERSION}
        )

    request_id = json_rpc_request.get("id")
    method = json_rpc_request.get("method")
    params = json_rpc_request.get("params", {})

    logger.info(f"Received MCP request: method={method}, id={request_id}")

    # Handle initialization
    if method == "initialize":
        session_id = create_session_id()
        sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "protocol_version": mcp_protocol_version
        }

        return JSONResponse(
            content=create_jsonrpc_response(
                id=request_id,
                result={
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "looker-mcp-server",
                        "version": "1.0.0"
                    }
                }
            ),
            headers={
                "Mcp-Session-Id": session_id,
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
            }
        )

    # Require session ID for all other methods
    if not mcp_session_id or mcp_session_id not in sessions:
        return JSONResponse(
            content=create_jsonrpc_response(
                id=request_id,
                error=create_jsonrpc_error(-32001, "Invalid session")
            ),
            headers={"MCP-Protocol-Version": MCP_PROTOCOL_VERSION}
        )

    # Handle tools/list
    if method == "tools/list":
        return JSONResponse(
            content=create_jsonrpc_response(
                id=request_id,
                result={
                    "tools": [
                        {
                            "name": "looker_conversational_analytics",
                            "description": "Ask natural language questions about Looker data using Google's Conversational Analytics API",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "user_query_with_context": {
                                        "type": "string",
                                        "description": "Natural language question about the data"
                                    },
                                    "explore_references": {
                                        "type": "array",
                                        "description": "List of Looker explores to query (1-5)",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "model": {"type": "string"},
                                                "explore": {"type": "string"}
                                            },
                                            "required": ["model", "explore"]
                                        }
                                    },
                                    "system_instruction": {
                                        "type": "string",
                                        "description": "Additional context for the agent",
                                        "default": "Help analyze the data and provide clear, actionable insights."
                                    },
                                    "enable_python_analysis": {
                                        "type": "boolean",
                                        "description": "Enable advanced Python analysis",
                                        "default": False
                                    },
                                    "response_format": {
                                        "type": "string",
                                        "enum": ["markdown", "json"],
                                        "description": "Output format",
                                        "default": "markdown"
                                    }
                                },
                                "required": ["user_query_with_context", "explore_references"]
                            }
                        }
                    ]
                }
            ),
            headers={
                "Mcp-Session-Id": mcp_session_id,
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
            }
        )

    # Handle tools/call
    if method == "tools/call":
        tool_name = params.get("name")
        tool_arguments = params.get("arguments", {})

        if tool_name != "looker_conversational_analytics":
            return JSONResponse(
                content=create_jsonrpc_response(
                    id=request_id,
                    error=create_jsonrpc_error(-32601, f"Unknown tool: {tool_name}")
                ),
                headers={
                    "Mcp-Session-Id": mcp_session_id,
                    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
                }
            )

        try:
            # Convert arguments to MCP input format
            explore_refs = [
                ExploreReference(**ref) for ref in tool_arguments.get("explore_references", [])
            ]

            mcp_input = ConversationalAnalyticsInput(
                user_query_with_context=tool_arguments.get("user_query_with_context"),
                explore_references=explore_refs,
                system_instruction=tool_arguments.get("system_instruction", "Help analyze the data and provide clear, actionable insights."),
                enable_python_analysis=tool_arguments.get("enable_python_analysis", False),
                response_format=ResponseFormat(tool_arguments.get("response_format", "markdown"))
            )

            # Call the tool
            result = await looker_conversational_analytics(mcp_input)

            return JSONResponse(
                content=create_jsonrpc_response(
                    id=request_id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ],
                        "isError": False
                    }
                ),
                headers={
                    "Mcp-Session-Id": mcp_session_id,
                    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
                }
            )

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return JSONResponse(
                content=create_jsonrpc_response(
                    id=request_id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error executing query: {str(e)}"
                            }
                        ],
                        "isError": True
                    }
                ),
                headers={
                    "Mcp-Session-Id": mcp_session_id,
                    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
                }
            )

    # Handle ping (keepalive)
    if method == "ping":
        return JSONResponse(
            content=create_jsonrpc_response(id=request_id, result={}),
            headers={
                "Mcp-Session-Id": mcp_session_id,
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
            }
        )

    # Unknown method
    return JSONResponse(
        content=create_jsonrpc_response(
            id=request_id,
            error=create_jsonrpc_error(-32601, f"Method not found: {method}")
        ),
        headers={
            "Mcp-Session-Id": mcp_session_id,
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
        }
    )


@app.get("/mcp")
async def mcp_endpoint_get(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
):
    """
    MCP endpoint for server-to-client messages (GET with SSE).

    Opens an SSE stream for receiving unsolicited server messages.
    """
    # Validate origin
    if not validate_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    # Validate session
    if not mcp_session_id or mcp_session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")

    async def event_generator():
        """Generate SSE events for server-to-client messages."""
        try:
            # Send keepalive pings
            while True:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "jsonrpc": "2.0",
                        "method": "notifications/ping"
                    })
                }
                await asyncio.sleep(30)  # Ping every 30 seconds
        except asyncio.CancelledError:
            logger.info(f"SSE stream closed for session {mcp_session_id}")

    return EventSourceResponse(
        event_generator(),
        headers={
            "Mcp-Session-Id": mcp_session_id,
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
        }
    )


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "Looker MCP Remote Server",
        "status": "running",
        "protocol": "MCP Streamable HTTP",
        "version": MCP_PROTOCOL_VERSION,
        "endpoints": {
            "mcp": "/mcp (POST/GET)",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    try:
        required_vars = [
            'LOOKER_BASE_URL',
            'LOOKER_CLIENT_ID',
            'LOOKER_CLIENT_SECRET',
            'GOOGLE_CLOUD_PROJECT'
        ]

        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": f"Missing environment variables: {', '.join(missing)}"
                }
            )

        return {
            "status": "healthy",
            "service": "Looker MCP Remote Server",
            "protocol": MCP_PROTOCOL_VERSION,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Looker MCP Remote Server on port {port}")
    logger.info(f"MCP Protocol Version: {MCP_PROTOCOL_VERSION}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
