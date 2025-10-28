#!/usr/bin/env python3
"""
HTTP wrapper for Looker Conversational Analytics MCP Server for Google Cloud Run deployment.

This server provides an HTTP/SSE interface to the MCP server for Cloud Run compatibility.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

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
    title="Looker MCP Cloud Server",
    description="HTTP wrapper for Looker Conversational Analytics MCP Server",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for conversational analytics queries."""
    user_query_with_context: str
    explore_references: list[dict]
    system_instruction: str = "Help analyze the data and provide clear, actionable insights."
    enable_python_analysis: bool = False
    response_format: str = "markdown"


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "Looker MCP Cloud Server",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "docs": "/docs"
        },
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    try:
        # Verify environment variables are set
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
            "service": "Looker MCP Cloud Server",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/query")
async def query_looker(request: QueryRequest):
    """
    Query Looker using conversational analytics.

    Args:
        request: Query request with user question and explore references

    Returns:
        Formatted response from Looker Conversational Analytics API
    """
    try:
        logger.info(f"Received query: {request.user_query_with_context[:100]}...")

        # Convert request to MCP input format
        explore_refs = [
            ExploreReference(**ref) for ref in request.explore_references
        ]

        mcp_input = ConversationalAnalyticsInput(
            user_query_with_context=request.user_query_with_context,
            explore_references=explore_refs,
            system_instruction=request.system_instruction,
            enable_python_analysis=request.enable_python_analysis,
            response_format=ResponseFormat(request.response_format)
        )

        # Call the MCP tool
        result = await looker_conversational_analytics(mcp_input)

        logger.info("Query completed successfully")

        # Return response based on format
        if request.response_format == "json":
            try:
                return JSONResponse(content=json.loads(result))
            except json.JSONDecodeError:
                return {"result": result}
        else:
            return {"result": result, "format": "markdown"}

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/query/stream")
async def query_looker_stream(request: QueryRequest):
    """
    Query Looker with streaming response (Server-Sent Events).

    Args:
        request: Query request with user question and explore references

    Returns:
        Streaming response with incremental results
    """
    async def event_stream():
        try:
            yield f"data: {json.dumps({'status': 'started'})}\n\n"

            # Convert request to MCP input format
            explore_refs = [
                ExploreReference(**ref) for ref in request.explore_references
            ]

            mcp_input = ConversationalAnalyticsInput(
                user_query_with_context=request.user_query_with_context,
                explore_references=explore_refs,
                system_instruction=request.system_instruction,
                enable_python_analysis=request.enable_python_analysis,
                response_format=ResponseFormat(request.response_format)
            )

            # Call the MCP tool
            result = await looker_conversational_analytics(mcp_input)

            yield f"data: {json.dumps({'status': 'completed', 'result': result})}\n\n"

        except Exception as e:
            logger.error(f"Stream query failed: {e}")
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )


@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "looker_conversational_analytics",
                "description": "Ask natural language questions about Looker data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_query_with_context": {
                            "type": "string",
                            "description": "Natural language question"
                        },
                        "explore_references": {
                            "type": "array",
                            "description": "List of Looker explores to query",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "model": {"type": "string"},
                                    "explore": {"type": "string"}
                                }
                            }
                        },
                        "system_instruction": {
                            "type": "string",
                            "description": "Additional context for the agent"
                        },
                        "enable_python_analysis": {
                            "type": "boolean",
                            "description": "Enable advanced Python analysis"
                        },
                        "response_format": {
                            "type": "string",
                            "enum": ["markdown", "json"],
                            "description": "Output format"
                        }
                    },
                    "required": ["user_query_with_context", "explore_references"]
                }
            }
        ]
    }


@app.get("/openapi.json")
async def get_openapi_schema(request: Request):
    """Return OpenAPI schema for ChatGPT Custom GPT integration."""
    base_url = str(request.base_url).rstrip('/')

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Looker Conversational Analytics API",
            "description": "Query Looker data using natural language via Google's Conversational Analytics API",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": base_url,
                "description": "Looker MCP Cloud Server"
            }
        ],
        "paths": {
            "/query": {
                "post": {
                    "operationId": "queryLooker",
                    "summary": "Query Looker data with natural language",
                    "description": "Ask natural language questions about Looker data. The API will automatically generate SQL, execute queries, and provide insights.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["user_query_with_context", "explore_references"],
                                    "properties": {
                                        "user_query_with_context": {
                                            "type": "string",
                                            "description": "Natural language question about the data",
                                            "example": "What are the top 10 products by revenue this quarter?"
                                        },
                                        "explore_references": {
                                            "type": "array",
                                            "description": "List of Looker explores to query (1-5)",
                                            "items": {
                                                "type": "object",
                                                "required": ["model", "explore"],
                                                "properties": {
                                                    "model": {
                                                        "type": "string",
                                                        "description": "LookML model name",
                                                        "example": "ecommerce"
                                                    },
                                                    "explore": {
                                                        "type": "string",
                                                        "description": "Explore name within the model",
                                                        "example": "order_items"
                                                    }
                                                }
                                            },
                                            "minItems": 1,
                                            "maxItems": 5
                                        },
                                        "system_instruction": {
                                            "type": "string",
                                            "description": "Additional context or instructions for the AI agent",
                                            "default": "Help analyze the data and provide clear, actionable insights."
                                        },
                                        "enable_python_analysis": {
                                            "type": "boolean",
                                            "description": "Enable advanced Python code interpreter for complex calculations",
                                            "default": False
                                        },
                                        "response_format": {
                                            "type": "string",
                                            "enum": ["markdown", "json"],
                                            "description": "Output format preference",
                                            "default": "markdown"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful query response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "result": {
                                                "type": "string",
                                                "description": "Formatted query results"
                                            },
                                            "format": {
                                                "type": "string",
                                                "description": "Response format used"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request parameters"
                        },
                        "500": {
                            "description": "Server error"
                        }
                    }
                }
            },
            "/tools": {
                "get": {
                    "operationId": "listTools",
                    "summary": "List available tools",
                    "description": "Get information about available Looker query tools",
                    "responses": {
                        "200": {
                            "description": "List of available tools"
                        }
                    }
                }
            }
        }
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Looker MCP Cloud Server on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
