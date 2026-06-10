#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="fitsaathi"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Deploying ${SERVICE_NAME} to project ${PROJECT_ID} in ${REGION}..."

# 1. Enable APIs
echo "Enabling GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    generativelanguage.googleapis.com

# 2. Build and Push Image
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} .

# 3. Create Secrets (if they don't exist)
# Note: You should set the actual values manually in Secret Manager after first run
echo "Creating secret placeholders..."
gcloud secrets create MONGODB_URI --replication-policy="automatic" 2>/dev/null
gcloud secrets create GOOGLE_API_KEY --replication-policy="automatic" 2>/dev/null

# 4. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-secrets="MONGODB_URI=MONGODB_URI:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
    --set-env-vars="GOOGLE_PROJECT_ID=${PROJECT_ID},GOOGLE_LOCATION=${REGION},ENVIRONMENT=production"

echo "Deployment complete!"
gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)'
