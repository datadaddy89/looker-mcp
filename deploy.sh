#!/bin/bash
# Deployment script for Looker MCP Server to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Looker MCP Server Deployment ===${NC}"

# Check if required commands are available
command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}Error: gcloud CLI is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is required but not installed.${NC}" >&2; exit 1; }

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="looker-mcp-server"
REPOSITORY_NAME="looker-mcp"

# Prompt for project ID if not set
if [ -z "$PROJECT_ID" ]; then
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
fi

echo -e "${YELLOW}Using Project ID: $PROJECT_ID${NC}"
echo -e "${YELLOW}Using Region: $REGION${NC}"

# Set the project
gcloud config set project "$PROJECT_ID"

echo -e "${GREEN}Step 1: Enable required APIs${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    geminidataanalytics.googleapis.com \
    secretmanager.googleapis.com

echo -e "${GREEN}Step 2: Create Artifact Registry repository${NC}"
gcloud artifacts repositories create "$REPOSITORY_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Looker MCP Server Docker images" \
    || echo "Repository may already exist"

echo -e "${GREEN}Step 3: Create secrets in Secret Manager${NC}"
echo "Please enter your Looker API credentials:"
read -p "Looker Client ID: " LOOKER_CLIENT_ID
read -sp "Looker Client Secret: " LOOKER_CLIENT_SECRET
echo

# Create secrets
echo -n "$LOOKER_CLIENT_ID" | gcloud secrets create looker-client-id --data-file=- --replication-policy="automatic" || \
    echo -n "$LOOKER_CLIENT_ID" | gcloud secrets versions add looker-client-id --data-file=-

echo -n "$LOOKER_CLIENT_SECRET" | gcloud secrets create looker-client-secret --data-file=- --replication-policy="automatic" || \
    echo -n "$LOOKER_CLIENT_SECRET" | gcloud secrets versions add looker-client-secret --data-file=-

echo -e "${GREEN}Step 4: Grant Secret Manager access to Cloud Run${NC}"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding looker-client-id \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding looker-client-secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

echo -e "${GREEN}Step 5: Build and deploy using Cloud Build${NC}"
gcloud builds submit --config cloudbuild.yaml \
    --substitutions=_LOOKER_BASE_URL="https://labelboxdata.cloud.looker.com",_LOOKER_VERIFY_SSL="false"

echo -e "${GREEN}Step 6: Get service URL${NC}"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
echo ""
echo "Test your deployment with:"
echo -e "${YELLOW}curl $SERVICE_URL/health${NC}"
echo ""
echo "Query endpoint:"
echo -e "${YELLOW}$SERVICE_URL/query${NC}"
