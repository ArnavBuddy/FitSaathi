# FitSaathi Deployment Guide

## Prerequisites
1. **Docker Desktop** installed and running (for local deployment)
2. **Google Cloud SDK (gcloud)** installed (for Google Cloud Run deployment)
3. **Git** (to push/pull changes)

---

## Option 1: Local Docker Deployment

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your machine!

### Step 2: Create Upload Directories
```bash
mkdir -p uploads/tryons uploads/users uploads/garments
```

### Step 3: Build and Run with Docker Compose
```bash
docker compose up --build -d
```

### Step 4: Access the App
Open your browser and go to: **http://localhost:8080**

### Step 5: Stop the App
```bash
docker compose down
```

---

## Option 2: Google Cloud Run Deployment

### Step 1: Install Google Cloud SDK (gcloud)
Download and install from: https://cloud.google.com/sdk/docs/install

### Step 2: Authenticate to GCP
```bash
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID
```
*(Replace `YOUR_GCP_PROJECT_ID` with your actual GCP project ID!)*

### Step 3: Enable Required APIs
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com generativelanguage.googleapis.com
```

### Step 4: Create Secrets in GCP Secret Manager
Go to the [Secret Manager Console](https://console.cloud.google.com/security/secret-manager) and create these secrets:
1. `MONGODB_URI` - with your MongoDB Atlas connection string
2. `GOOGLE_API_KEY` - with your Gemini API key

### Step 5: Build and Deploy to Cloud Run
Run the deployment script:
```bash
bash deploy/cloud_run_deploy.sh
```
*(Or manually follow the steps in `deploy/cloud_run_deploy.sh`)*

### Step 6: Access Your Deployed App!
The script will output your app's public URL at the end!

---

## Other Deployment Options
- **Vercel**: Deploy frontend separately, backend on another service
- **AWS**: Use AWS ECS or Lambda
- **Heroku**: Docker-based deployment to Heroku
- **Railway/Render**: Easy Docker deployment platforms
