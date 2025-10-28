# Looker MCP Cloud Server - Google Cloud Run Deployment Guide

This guide provides step-by-step instructions for deploying the Looker MCP Server to Google Cloud Run.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)

## Overview

The Looker MCP Cloud Server is deployed as an HTTP service on Google Cloud Run, providing a scalable and serverless API for querying Looker data using natural language.

### Key Features

- **Serverless**: Scales automatically from 0 to many instances
- **HTTP API**: RESTful endpoints for easy integration
- **Streaming Support**: Server-Sent Events (SSE) for real-time responses
- **Secure**: Uses Google Secret Manager for credentials
- **Cost-Effective**: Pay only for what you use
- **Fast Deployment**: Deploy in minutes using automated scripts

## Architecture

```
Client (Web/Mobile/AI)
        ↓ (HTTPS)
Google Cloud Run (HTTP Server)
        ↓ (FastAPI Wrapper)
MCP Tool (looker_conversational_analytics)
        ↓
Google Conversational Analytics API
        ↓
Looker Instance
```

## Prerequisites

### 1. Google Cloud Setup

- Google Cloud account with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and configured
- Project with appropriate permissions:
  - Cloud Run Admin
  - Artifact Registry Admin
  - Secret Manager Admin
  - Service Usage Admin

### 2. Looker Setup

- Looker instance URL (e.g., `https://company.looker.com`)
- API credentials (Client ID and Client Secret)
- User permissions:
  - Get LookML Model Explore
  - Run Inline Query

### 3. APIs to Enable

The deployment script will enable these automatically, but you can verify:

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    geminidataanalytics.googleapis.com \
    secretmanager.googleapis.com
```

## Quick Start

### Option 1: Automated Deployment (Recommended)

#### For Linux/Mac:

```bash
# Make the script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

#### For Windows:

```powershell
# Run in PowerShell
.\deploy.ps1
```

The script will:
1. Enable required APIs
2. Create Artifact Registry repository
3. Store Looker credentials in Secret Manager
4. Build Docker image
5. Deploy to Cloud Run
6. Output the service URL

### Option 2: Manual Deployment

#### Step 1: Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
```

#### Step 2: Enable APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    geminidataanalytics.googleapis.com \
    secretmanager.googleapis.com
```

#### Step 3: Create Artifact Registry

```bash
gcloud artifacts repositories create looker-mcp \
    --repository-format=docker \
    --location=$REGION \
    --description="Looker MCP Server"
```

#### Step 4: Store Secrets

```bash
# Store Looker Client ID
echo -n "your-looker-client-id" | \
    gcloud secrets create looker-client-id \
    --data-file=- \
    --replication-policy="automatic"

# Store Looker Client Secret
echo -n "your-looker-client-secret" | \
    gcloud secrets create looker-client-secret \
    --data-file=- \
    --replication-policy="automatic"
```

#### Step 5: Grant Secret Access

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding looker-client-id \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding looker-client-secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### Step 6: Deploy with Cloud Build

```bash
gcloud builds submit --config cloudbuild.yaml \
    --substitutions=_LOOKER_BASE_URL="https://your-instance.looker.com",_LOOKER_VERIFY_SSL="true"
```

## Deployment Options

### Build Configuration

Edit [cloudbuild.yaml](cloudbuild.yaml) to customize:

- **Memory**: Default 2Gi, adjust based on query complexity
- **CPU**: Default 2, increase for faster processing
- **Timeout**: Default 300s (5 minutes)
- **Instances**: Min 0, Max 10, adjust for traffic

### Environment Variables

Configure in [cloudbuild.yaml](cloudbuild.yaml):

- `LOOKER_BASE_URL`: Your Looker instance URL
- `LOOKER_VERIFY_SSL`: SSL verification (true/false)
- `GOOGLE_CLOUD_PROJECT`: Auto-populated

### Secrets

Stored in Google Secret Manager:
- `looker-client-id`: Looker API Client ID
- `looker-client-secret`: Looker API Client Secret

## Configuration

### Update Looker URL

```bash
gcloud run services update looker-mcp-server \
    --region=us-central1 \
    --update-env-vars LOOKER_BASE_URL="https://new-instance.looker.com"
```

### Update Credentials

```bash
# Update client ID
echo -n "new-client-id" | gcloud secrets versions add looker-client-id --data-file=-

# Update client secret
echo -n "new-client-secret" | gcloud secrets versions add looker-client-secret --data-file=-
```

### Scaling Configuration

```bash
gcloud run services update looker-mcp-server \
    --region=us-central1 \
    --min-instances=1 \
    --max-instances=20 \
    --memory=4Gi \
    --cpu=4
```

## Testing

### Health Check

```bash
curl https://your-service-url.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Looker MCP Cloud Server",
  "version": "1.0.0"
}
```

### Query Endpoint

```bash
curl -X POST https://your-service-url.run.app/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query_with_context": "What are the top 10 products by revenue?",
    "explore_references": [
      {"model": "ecommerce", "explore": "order_items"}
    ],
    "response_format": "markdown"
  }'
```

### Streaming Query

```bash
curl -X POST https://your-service-url.run.app/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_query_with_context": "Show monthly sales trends",
    "explore_references": [
      {"model": "ecommerce", "explore": "orders"}
    ]
  }'
```

### List Available Tools

```bash
curl https://your-service-url.run.app/tools
```

## Monitoring

### View Logs

```bash
gcloud run services logs read looker-mcp-server \
    --region=us-central1 \
    --limit=50
```

### Real-time Logs

```bash
gcloud run services logs tail looker-mcp-server \
    --region=us-central1
```

### Metrics Dashboard

Visit [Cloud Run Console](https://console.cloud.google.com/run) to view:
- Request count
- Request latency
- Container instance count
- CPU and memory utilization

### Set Up Alerts

```bash
# Example: Alert on high error rate
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="High Error Rate - Looker MCP" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=0.05
```

## Troubleshooting

### Deployment Fails

**Issue**: Cloud Build fails
```bash
# Check build logs
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

**Common causes**:
- APIs not enabled
- Insufficient permissions
- Invalid Docker configuration

### Service Unhealthy

**Issue**: Health check returns 503
```bash
# Check service logs
gcloud run services logs read looker-mcp-server --limit=100
```

**Common causes**:
- Missing environment variables
- Invalid Looker credentials
- Secret Manager access issues

### Query Errors

**Issue**: Queries return errors

1. **Authentication Error**:
   - Verify Google Cloud credentials
   - Check Conversational Analytics API is enabled
   - Verify IAM permissions

2. **Looker Connection Error**:
   - Verify Looker credentials in Secret Manager
   - Check Looker base URL is correct
   - Verify Looker API permissions

3. **Timeout Error**:
   - Increase timeout: `--timeout=600s`
   - Simplify query
   - Enable Python analysis for complex queries

### Check Secret Access

```bash
# Test secret access from Cloud Run
gcloud run services describe looker-mcp-server \
    --region=us-central1 \
    --format="value(spec.template.spec.containers[0].env)"
```

## Cost Estimation

### Pricing Factors

1. **Cloud Run**:
   - CPU time: $0.00002400 per vCPU-second
   - Memory: $0.00000250 per GiB-second
   - Requests: $0.40 per million requests
   - Free tier: 2 million requests/month

2. **Conversational Analytics API**:
   - Pricing varies by usage
   - Check [Google Cloud Pricing](https://cloud.google.com/pricing)

3. **Secret Manager**:
   - $0.06 per active secret version per month
   - $0.03 per 10,000 access operations

### Example Cost Calculation

**Scenario**: 10,000 queries/month, 30s average response time, 2 GB memory

- Cloud Run CPU: 10,000 × 30s × 2 vCPU × $0.000024 = $14.40
- Cloud Run Memory: 10,000 × 30s × 2 GB × $0.0000025 = $1.50
- Requests: 10,000 / 1,000,000 × $0.40 = $0.004
- Secret Manager: 2 secrets × $0.06 = $0.12
- **Total**: ~$16/month

### Cost Optimization

1. **Reduce min instances to 0** (default)
2. **Use appropriate memory/CPU** (start with 2Gi/2 CPU)
3. **Set request timeouts** to prevent long-running queries
4. **Monitor and optimize** query complexity

## Production Best Practices

### Security

1. **Enable Authentication**:
   ```bash
   gcloud run services update looker-mcp-server \
       --region=us-central1 \
       --no-allow-unauthenticated
   ```

2. **Use Custom Service Account**:
   ```bash
   gcloud run services update looker-mcp-server \
       --region=us-central1 \
       --service-account=your-sa@project.iam.gserviceaccount.com
   ```

3. **Enable SSL Verification**:
   Update cloudbuild.yaml: `_LOOKER_VERIFY_SSL: "true"`

### Performance

1. **Use min instances** for latency-sensitive applications
2. **Enable HTTP/2** for multiplexing
3. **Implement caching** for repeated queries
4. **Use streaming** for large responses

### Reliability

1. **Set up monitoring** and alerting
2. **Configure max instances** to control costs
3. **Implement retry logic** in clients
4. **Test disaster recovery** procedures

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: google-github-actions/setup-gcloud@v0
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - run: gcloud builds submit --config cloudbuild.yaml
```

### Cloud Build Trigger

```bash
gcloud builds triggers create github \
    --repo-name=looker-mcp \
    --repo-owner=cyrusj89 \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api)
- [Looker API Reference](https://cloud.google.com/looker/docs/api)
- [Secret Manager Guide](https://cloud.google.com/secret-manager/docs)

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review Cloud Run logs
3. Check Google Cloud Status Dashboard
4. Open an issue in the GitHub repository
