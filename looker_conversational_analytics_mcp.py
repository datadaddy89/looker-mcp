#!/usr/bin/env python3
"""
Looker Conversational Analytics MCP Server

This MCP server provides access to Looker's Conversational Analytics API, 
enabling AI assistants to ask natural language questions about data in Looker Explores.

The server uses Google's Conversational Analytics API to provide:
- Natural language to SQL/Python code generation
- Multi-explore querying (up to 5 explores simultaneously)
- Advanced analysis capabilities
- Automatic chart generation

Environment Variables Required:
    LOOKER_BASE_URL: URL of your Looker instance (e.g., https://company.looker.com)
    LOOKER_CLIENT_ID: Looker API client ID
    LOOKER_CLIENT_SECRET: Looker API client secret
    LOOKER_VERIFY_SSL: Whether to verify SSL (true/false)
    GOOGLE_CLOUD_PROJECT: Google Cloud project ID with Conversational Analytics API enabled

Author: Generated via Claude MCP Builder
License: MIT
"""

import os
import json
from typing import List, Dict, Optional, Any
from enum import Enum

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Google Cloud and Conversational Analytics imports
try:
    from google.cloud import geminidataanalytics
    from google.auth import default as google_auth_default
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    raise ImportError(
        "Required packages not installed. Please install:\n"
        "  pip install google-cloud-geminidataanalytics google-auth --break-system-packages"
    )

# Constants
CHARACTER_LIMIT = 25000  # Maximum response size in characters
DEFAULT_TIMEOUT = 300  # Default timeout for API calls in seconds
MAX_EXPLORES = 5  # Maximum number of explores per query

# Initialize MCP server
mcp = FastMCP("looker_conversational_analytics_mcp")


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class ExploreReference(BaseModel):
    """Reference to a Looker Explore."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    model: str = Field(
        ...,
        description="LookML model name (e.g., 'ecommerce', 'thelook')",
        min_length=1,
        max_length=200
    )
    explore: str = Field(
        ...,
        description="Explore name within the model (e.g., 'order_items', 'users')",
        min_length=1,
        max_length=200
    )

    @field_validator('model', 'explore')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure model and explore names are not empty after stripping."""
        if not v.strip():
            raise ValueError("Model and explore names cannot be empty")
        return v.strip()


class ConversationalAnalyticsInput(BaseModel):
    """Input model for Looker Conversational Analytics queries."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    user_query_with_context: str = Field(
        ...,
        description=(
            "Natural language question to ask about your Looker data. "
            "Examples: 'What are the top 10 products by revenue?', "
            "'Show me monthly sales trends for 2024', "
            "'Which customers have the highest lifetime value?'"
        ),
        min_length=1,
        max_length=5000
    )
    
    explore_references: List[ExploreReference] = Field(
        ...,
        description=(
            "List of 1-5 Looker Explores to query. The API will automatically "
            "select the most relevant explore for your question. "
            "Format: [{'model': 'model_name', 'explore': 'explore_name'}, ...]"
        ),
        min_length=1,
        max_length=MAX_EXPLORES
    )
    
    system_instruction: Optional[str] = Field(
        default="Help analyze the data and provide clear, actionable insights.",
        description=(
            "Additional context or instructions for the data agent. "
            "Use this to define business terms, specify response format preferences, "
            "or provide domain-specific context."
        ),
        max_length=5000
    )
    
    enable_python_analysis: bool = Field(
        default=False,
        description=(
            "Enable advanced Python code interpreter for complex calculations, "
            "statistical analysis, and advanced visualizations. "
            "Note: May increase response time."
        )
    )
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('user_query_with_context')
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Ensure query is not empty after stripping."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @field_validator('explore_references')
    @classmethod
    def validate_explore_count(cls, v: List[ExploreReference]) -> List[ExploreReference]:
        """Ensure explore references list is within limits."""
        if len(v) > MAX_EXPLORES:
            raise ValueError(f"Maximum {MAX_EXPLORES} explores allowed, got {len(v)}")
        return v


# Helper Functions

def get_environment_config() -> Dict[str, str]:
    """
    Retrieve and validate required environment variables.
    
    Returns:
        Dict[str, str]: Configuration dictionary with Looker and GCP settings
        
    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = {
        'LOOKER_BASE_URL': 'Looker instance URL (e.g., https://company.looker.com)',
        'LOOKER_CLIENT_ID': 'Looker API client ID',
        'LOOKER_CLIENT_SECRET': 'Looker API client secret',
        'GOOGLE_CLOUD_PROJECT': 'Google Cloud project ID'
    }
    
    config = {}
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"  - {var}: {description}")
        else:
            config[var] = value
    
    if missing_vars:
        error_msg = (
            "Missing required environment variables:\n" +
            "\n".join(missing_vars) +
            "\n\nPlease set these environment variables before running the server."
        )
        raise ValueError(error_msg)
    
    # Optional variables
    config['LOOKER_VERIFY_SSL'] = os.getenv('LOOKER_VERIFY_SSL', 'true').lower() == 'true'
    
    return config


def initialize_clients() -> tuple:
    """
    Initialize Google Cloud authentication and Conversational Analytics clients.
    
    Returns:
        tuple: (DataChatServiceClient, credentials, project_id)
        
    Raises:
        DefaultCredentialsError: If Google Cloud credentials are not properly configured
    """
    try:
        # Authenticate to Google Cloud
        credentials, project = google_auth_default()
        
        # Initialize Conversational Analytics client
        data_chat_client = geminidataanalytics.DataChatServiceClient(credentials=credentials)
        
        return data_chat_client, credentials, project
    except DefaultCredentialsError as e:
        error_msg = (
            "Google Cloud authentication failed. Please ensure you have:\n"
            "1. Set up Application Default Credentials:\n"
            "   - Run: gcloud auth application-default login\n"
            "   - Or set GOOGLE_APPLICATION_CREDENTIALS environment variable\n"
            "2. Enabled the Conversational Analytics API:\n"
            "   - gcloud services enable geminidataanalytics.googleapis.com\n"
            "3. Have the necessary IAM permissions\n\n"
            f"Error details: {str(e)}"
        )
        raise DefaultCredentialsError(error_msg)


def create_looker_explore_references(
    explore_refs: List[ExploreReference],
    looker_base_url: str
) -> List[geminidataanalytics.LookerExploreReference]:
    """
    Create Looker explore reference objects for the Conversational Analytics API.
    
    Args:
        explore_refs: List of ExploreReference objects
        looker_base_url: Base URL of the Looker instance
        
    Returns:
        List[geminidataanalytics.LookerExploreReference]: Explore references for the API
    """
    looker_refs = []
    
    for ref in explore_refs:
        looker_ref = geminidataanalytics.LookerExploreReference()
        looker_ref.looker_instance_uri = looker_base_url
        looker_ref.lookml_model = ref.model
        looker_ref.explore = ref.explore
        looker_refs.append(looker_ref)
    
    return looker_refs


def create_looker_credentials(
    client_id: str,
    client_secret: str
) -> geminidataanalytics.Credentials:
    """
    Create Looker credentials object for the Conversational Analytics API.
    
    Args:
        client_id: Looker API client ID
        client_secret: Looker API client secret
        
    Returns:
        geminidataanalytics.Credentials: Credentials object for the API
    """
    credentials = geminidataanalytics.Credentials()
    credentials.oauth.secret.client_id = client_id
    credentials.oauth.secret.client_secret = client_secret
    return credentials


def format_response_markdown(messages: List[Any]) -> str:
    """
    Format API response messages as Markdown.
    
    Args:
        messages: List of system messages from the API
        
    Returns:
        str: Formatted Markdown string
    """
    output_parts = []
    output_parts.append("# Conversational Analytics Response\n")
    
    for msg in messages:
        if not hasattr(msg, 'system_message'):
            continue
            
        sys_msg = msg.system_message
        
        # Handle text responses
        if hasattr(sys_msg, 'text') and sys_msg.text:
            text_obj = sys_msg.text
            if hasattr(text_obj, 'parts'):
                text_content = ''.join(text_obj.parts)
                # Determine if this is a thought or final response
                if hasattr(text_obj, 'text_type'):
                    if text_obj.text_type == geminidataanalytics.TextMessage.TextType.THOUGHT:
                        output_parts.append(f"\n## 💭 Analysis Steps\n\n{text_content}\n")
                    else:  # FINAL_RESPONSE
                        output_parts.append(f"\n## 📊 Answer\n\n{text_content}\n")
                else:
                    output_parts.append(f"\n{text_content}\n")
        
        # Handle data responses (SQL queries and results)
        if hasattr(sys_msg, 'data') and sys_msg.data:
            data_obj = sys_msg.data
            
            # SQL query
            if hasattr(data_obj, 'query') and data_obj.query:
                query = data_obj.query
                if hasattr(query, 'looker') and query.looker:
                    looker_query = query.looker
                    output_parts.append("\n## 🔍 Looker Query Details\n")
                    if hasattr(looker_query, 'lookml_model'):
                        output_parts.append(f"- **Model**: {looker_query.lookml_model}\n")
                    if hasattr(looker_query, 'explore'):
                        output_parts.append(f"- **Explore**: {looker_query.explore}\n")
                    if hasattr(looker_query, 'fields'):
                        output_parts.append(f"- **Fields**: {', '.join(looker_query.fields)}\n")
                    if hasattr(looker_query, 'filters'):
                        output_parts.append(f"- **Filters**: {dict(looker_query.filters)}\n")
            
            # Generated SQL
            if hasattr(data_obj, 'generated_sql') and data_obj.generated_sql:
                output_parts.append(f"\n## 📝 Generated SQL\n\n```sql\n{data_obj.generated_sql}\n```\n")
            
            # Results data
            if hasattr(data_obj, 'result') and data_obj.result:
                result = data_obj.result
                if hasattr(result, 'data') and result.data:
                    output_parts.append("\n## 📋 Query Results\n\n")
                    # Convert results to a simple table format
                    if hasattr(result, 'schema') and result.schema.fields:
                        # Create table header
                        headers = [field.name for field in result.schema.fields]
                        output_parts.append("| " + " | ".join(headers) + " |\n")
                        output_parts.append("|" + "|".join(["---"] * len(headers)) + "|\n")
                        
                        # Add data rows (limit to first 50 rows for readability)
                        for i, row in enumerate(result.data[:50]):
                            row_values = [str(row.get(h, '')) for h in headers]
                            output_parts.append("| " + " | ".join(row_values) + " |\n")
                        
                        if len(result.data) > 50:
                            output_parts.append(f"\n*Showing first 50 of {len(result.data)} rows*\n")
        
        # Handle chart specifications
        if hasattr(sys_msg, 'chart') and sys_msg.chart:
            chart_obj = sys_msg.chart
            if hasattr(chart_obj, 'result') and chart_obj.result:
                output_parts.append("\n## 📈 Visualization\n\n")
                output_parts.append("*Chart specification available (use JSON format for full details)*\n")
    
    result = ''.join(output_parts)
    
    # Check character limit
    if len(result) > CHARACTER_LIMIT:
        result = result[:CHARACTER_LIMIT] + (
            f"\n\n---\n⚠️ **Response truncated**: Output exceeded {CHARACTER_LIMIT} character limit. "
            "Consider refining your query or requesting specific data subsets."
        )
    
    return result


def format_response_json(messages: List[Any]) -> str:
    """
    Format API response messages as JSON.
    
    Args:
        messages: List of system messages from the API
        
    Returns:
        str: Formatted JSON string
    """
    response_data = {
        "text_responses": [],
        "analysis_steps": [],
        "queries": [],
        "results": [],
        "charts": []
    }
    
    for msg in messages:
        if not hasattr(msg, 'system_message'):
            continue
            
        sys_msg = msg.system_message
        
        # Handle text responses
        if hasattr(sys_msg, 'text') and sys_msg.text:
            text_obj = sys_msg.text
            if hasattr(text_obj, 'parts'):
                text_content = ''.join(text_obj.parts)
                text_type = "thought" if (hasattr(text_obj, 'text_type') and 
                                         text_obj.text_type == geminidataanalytics.TextMessage.TextType.THOUGHT) else "final_response"
                
                if text_type == "thought":
                    response_data["analysis_steps"].append(text_content)
                else:
                    response_data["text_responses"].append(text_content)
        
        # Handle data responses
        if hasattr(sys_msg, 'data') and sys_msg.data:
            data_obj = sys_msg.data
            
            query_info = {}
            if hasattr(data_obj, 'query') and data_obj.query:
                query = data_obj.query
                if hasattr(query, 'looker') and query.looker:
                    looker_query = query.looker
                    query_info = {
                        "model": getattr(looker_query, 'lookml_model', None),
                        "explore": getattr(looker_query, 'explore', None),
                        "fields": list(getattr(looker_query, 'fields', [])),
                        "filters": dict(getattr(looker_query, 'filters', {}))
                    }
            
            if hasattr(data_obj, 'generated_sql') and data_obj.generated_sql:
                query_info["sql"] = data_obj.generated_sql
            
            if query_info:
                response_data["queries"].append(query_info)
            
            if hasattr(data_obj, 'result') and data_obj.result:
                result = data_obj.result
                if hasattr(result, 'data') and result.data:
                    result_data = {
                        "schema": [],
                        "data": []
                    }
                    
                    if hasattr(result, 'schema') and result.schema.fields:
                        result_data["schema"] = [
                            {"name": field.name, "type": field.type}
                            for field in result.schema.fields
                        ]
                    
                    result_data["data"] = [dict(row) for row in result.data]
                    response_data["results"].append(result_data)
        
        # Handle charts
        if hasattr(sys_msg, 'chart') and sys_msg.chart:
            chart_obj = sys_msg.chart
            if hasattr(chart_obj, 'result') and chart_obj.result:
                # Chart specs can be large, include a simplified version
                response_data["charts"].append({
                    "type": "vega_spec",
                    "note": "Full chart specification available in API response"
                })
    
    result = json.dumps(response_data, indent=2)
    
    # Check character limit
    if len(result) > CHARACTER_LIMIT:
        response_data["truncated"] = True
        response_data["truncation_message"] = (
            f"Response exceeded {CHARACTER_LIMIT} character limit. "
            "Results have been truncated. Consider refining your query."
        )
        # Truncate data arrays
        if len(response_data["results"]) > 0:
            for result in response_data["results"]:
                if len(result.get("data", [])) > 50:
                    result["data"] = result["data"][:50]
                    result["data_truncated"] = True
        result = json.dumps(response_data, indent=2)
    
    return result


@mcp.tool(
    name="looker_conversational_analytics",
    annotations={
        "title": "Looker Conversational Analytics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def looker_conversational_analytics(params: ConversationalAnalyticsInput) -> str:
    """Ask natural language questions about your Looker data using Google's Conversational Analytics API.
    
    This tool enables you to query Looker Explores using natural language, leveraging Google's
    advanced AI models to automatically generate SQL, analyze data, and provide insights.
    The API can query up to 5 different Looker Explores and will automatically select the most
    relevant one for your question.
    
    Features:
    - Natural language to SQL query generation
    - Automatic explore selection from provided options
    - Multi-turn conversation support
    - Advanced Python analysis for complex calculations
    - Automatic chart and visualization generation
    - Grounded in Looker's semantic layer for accuracy
    
    Args:
        params (ConversationalAnalyticsInput): Input parameters containing:
            - user_query_with_context (str): Natural language question about the data
            - explore_references (List[Dict]): 1-5 Looker explores to query
            - system_instruction (Optional[str]): Additional context for the agent
            - enable_python_analysis (bool): Enable advanced Python code interpreter
            - response_format (str): Output format ('markdown' or 'json')
    
    Returns:
        str: Formatted response containing analysis, queries, results, and insights.
             Format depends on response_format parameter:
             - 'markdown': Human-readable format with headers and tables
             - 'json': Structured JSON with separate sections for queries, results, charts
    
    Raises:
        ValueError: If environment variables are not configured or inputs are invalid
        DefaultCredentialsError: If Google Cloud credentials are not properly set up
        Exception: For API errors, timeouts, or other runtime issues
    
    Example Usage:
        ```
        # Single explore query
        {
          "user_query_with_context": "What are the top 10 products by revenue this year?",
          "explore_references": [
            {"model": "ecommerce", "explore": "order_items"}
          ]
        }
        
        # Multi-explore query (API selects most relevant)
        {
          "user_query_with_context": "Compare user signups vs order volume by month",
          "explore_references": [
            {"model": "ecommerce", "explore": "users"},
            {"model": "ecommerce", "explore": "orders"}
          ],
          "system_instruction": "Focus on year-over-year growth trends"
        }
        ```
    
    Important Notes:
    - Requires Google Cloud credentials with Conversational Analytics API enabled
    - Requires Looker API credentials (client ID and secret)
    - First API call may take longer as the agent analyzes the explore structure
    - Large result sets may be truncated to respect character limits
    - Python analysis may increase response time but enables advanced calculations
    """
    try:
        # Get configuration
        config = get_environment_config()
        
        # Initialize clients
        data_chat_client, credentials, project_id = initialize_clients()
        
        # Use project from config if available, otherwise from credentials
        billing_project = config.get('GOOGLE_CLOUD_PROJECT', project_id)
        
        # Create Looker explore references
        looker_explore_refs = create_looker_explore_references(
            params.explore_references,
            config['LOOKER_BASE_URL']
        )
        
        # Create Looker credentials
        looker_creds = create_looker_credentials(
            config['LOOKER_CLIENT_ID'],
            config['LOOKER_CLIENT_SECRET']
        )
        
        # Set up datasource references
        datasource_references = geminidataanalytics.DatasourceReferences()
        datasource_references.looker.explore_references = looker_explore_refs
        datasource_references.credentials = looker_creds
        
        # Set up inline context for stateless chat
        inline_context = geminidataanalytics.Context()
        inline_context.system_instruction = params.system_instruction
        inline_context.datasource_references = datasource_references
        
        # Enable Python analysis if requested
        if params.enable_python_analysis:
            inline_context.options.analysis.python.enabled = True
        
        # Create the user message
        user_message = geminidataanalytics.Message()
        user_message.user_message.text = params.user_query_with_context
        
        # Create the chat request
        request = geminidataanalytics.ChatRequest(
            parent=f"projects/{billing_project}/locations/global",
            messages=[user_message],
            inline_context=inline_context
        )
        
        # Make the request (with timeout)
        stream = data_chat_client.chat(request=request, timeout=DEFAULT_TIMEOUT)
        
        # Collect all response messages
        response_messages = []
        for response in stream:
            response_messages.append(response)
        
        # Format the response based on requested format
        if params.response_format == ResponseFormat.JSON:
            formatted_response = format_response_json(response_messages)
        else:  # MARKDOWN
            formatted_response = format_response_markdown(response_messages)
        
        return formatted_response
        
    except ValueError as e:
        # Configuration or validation errors
        return (
            f"❌ **Configuration Error**\n\n{str(e)}\n\n"
            "Please check your environment variables and input parameters."
        )
    except DefaultCredentialsError as e:
        # Google Cloud authentication errors
        return (
            f"❌ **Authentication Error**\n\n{str(e)}\n\n"
            "Please ensure Google Cloud credentials are properly configured."
        )
    except Exception as e:
        # Other runtime errors
        error_type = type(e).__name__
        return (
            f"❌ **Error ({error_type})**\n\n{str(e)}\n\n"
            "If this error persists, please check:\n"
            "1. Your Looker instance is accessible\n"
            "2. The explore references are correct\n"
            "3. Your Google Cloud project has the Conversational Analytics API enabled\n"
            "4. You have sufficient API quota\n\n"
            "For timeout errors, try simplifying your query or enabling Python analysis."
        )


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
