# PowerShell deployment script for Looker MCP Server to Google Cloud Run
# For Windows users

$ErrorActionPreference = "Stop"

Write-Host "=== Looker MCP Server Deployment ===" -ForegroundColor Green

# Check if required commands are available
$gcloudExists = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudExists) {
    Write-Host "Error: gcloud CLI is required but not installed." -ForegroundColor Red
    exit 1
}

# Configuration
$PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$SERVICE_NAME = "looker-mcp-server"
$REPOSITORY_NAME = "looker-mcp"

# Prompt for project ID if not set
if (-not $PROJECT_ID) {
    $PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"
}

Write-Host "Using Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Using Region: $REGION" -ForegroundColor Yellow

# Set the project
gcloud config set project $PROJECT_ID

Write-Host "Step 1: Enable required APIs" -ForegroundColor Green
gcloud services enable `
    cloudbuild.googleapis.com `
    run.googleapis.com `
    artifactregistry.googleapis.com `
    geminidataanalytics.googleapis.com `
    secretmanager.googleapis.com

Write-Host "Step 2: Create Artifact Registry repository" -ForegroundColor Green
try {
    gcloud artifacts repositories create $REPOSITORY_NAME `
        --repository-format=docker `
        --location=$REGION `
        --description="Looker MCP Server Docker images"
} catch {
    Write-Host "Repository may already exist" -ForegroundColor Yellow
}

Write-Host "Step 3: Create secrets in Secret Manager" -ForegroundColor Green
Write-Host "Please enter your Looker API credentials:"
$LOOKER_CLIENT_ID = Read-Host "Looker Client ID"
$LOOKER_CLIENT_SECRET = Read-Host "Looker Client Secret" -AsSecureString
$LOOKER_CLIENT_SECRET_Plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($LOOKER_CLIENT_SECRET))

# Create secrets
try {
    echo $LOOKER_CLIENT_ID | gcloud secrets create looker-client-id --data-file=- --replication-policy="automatic"
} catch {
    echo $LOOKER_CLIENT_ID | gcloud secrets versions add looker-client-id --data-file=-
}

try {
    echo $LOOKER_CLIENT_SECRET_Plain | gcloud secrets create looker-client-secret --data-file=- --replication-policy="automatic"
} catch {
    echo $LOOKER_CLIENT_SECRET_Plain | gcloud secrets versions add looker-client-secret --data-file=-
}

Write-Host "Step 4: Grant Secret Manager access to Cloud Run" -ForegroundColor Green
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"

gcloud secrets add-iam-policy-binding looker-client-id `
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding looker-client-secret `
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"

Write-Host "Step 5: Build and deploy using Cloud Build" -ForegroundColor Green
gcloud builds submit --config cloudbuild.yaml `
    --substitutions=_LOOKER_BASE_URL="https://labelboxdata.cloud.looker.com",_LOOKER_VERIFY_SSL="false"

Write-Host "Step 6: Get service URL" -ForegroundColor Green
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Test your deployment with:"
Write-Host "curl $SERVICE_URL/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "Query endpoint:"
Write-Host "$SERVICE_URL/query" -ForegroundColor Yellow
