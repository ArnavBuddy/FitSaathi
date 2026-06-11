# FitSaathi Deployment Guide (Vercel + Render + MongoDB Atlas)

## Architecture Overview
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│          ┌──────────────────┐         ┌──────────────────┐                     │
│          │   Frontend       │         │   Backend        │                     │
│          │   (Vercel)       │◄───────►│   (Render)       │                     │
│          │                  │         │                  │                     │
│          └──────────────────┘         └────────┬─────────┘                     │
│                                               │                               │
│                                               ▼                               │
│                                    ┌──────────────────┐                       │
│                                    │   MongoDB Atlas  │                       │
│                                    │   (Database)     │                       │
│                                    └──────────────────┘                       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites
- GitHub Account
- Vercel Account (Free Hobby Plan)
- Render Account (Free Plan)
- MongoDB Atlas Account (Free M0 Cluster)
- Google Gemini API Key (Free Tier available)

---

## Step 1: Set up MongoDB Atlas

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and sign up/log in
2. Create a new **Free M0 Cluster** (choose your preferred cloud provider/region)
3. Wait for your cluster to be created (2-3 minutes)
4. Click "Connect" → "Connect your application"
5. Select Driver = "Python", Version = "3.11 or later"
6. Copy your connection string, it should look like this:
   ```
   mongodb+srv://<username>:<password>@cluster.mongodb.net/fitsaathi
   ```
7. Replace `<username>` and `<password>` with your actual database credentials
8. **Important**: Make sure to whitelist your IP address (and `0.0.0.0/0` for Render/Vercel) in Network Access

---

## Step 2: Deploy Backend to Render

### Option A: One-Click Deploy (Recommended)
Wait, not yet, let's first commit our changes!

### Option B: Manual Deploy to Render

1. Go to [Render](https://render.com) and sign up/log in
2. Connect your GitHub account
3. Click "New" → "Web Service"
4. Select your FitSaathi repository
5. Configure your web service:
   - **Name**: fitsaathi-backend
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
6. In "Environment Variables" section, add:
   - `MONGODB_URI`: Your MongoDB Atlas connection string
   - `GOOGLE_API_KEY`: Your Gemini API Key
   - `SECRET_KEY`: (Render will auto-generate one for you, or use your own)
   - `ENVIRONMENT`: production
   - `CORS_ORIGINS`: `http://localhost:3000,http://localhost:8080,https://fitsaathi.vercel.app`
7. Click "Create Web Service"
8. Wait for your backend to deploy! Copy your backend URL (e.g. `https://fitsaathi-backend.onrender.com`)

---

## Step 3: Deploy Frontend to Vercel

1. Go to [Vercel](https://vercel.com) and sign up/log in
2. Connect your GitHub account
3. Click "New Project"
4. Select your FitSaathi repository
5. Configure your project:
   - **Project Name**: fitsaathi
   - **Framework Preset**: Other
   - **Build Command**: `mkdir -p build && cp -r frontend/* build/`
   - **Output Directory**: build
6. In "Environment Variables" section, add:
   - `VITE_API_BASE_URL`: Your Render backend URL (from Step 2)
7. Click "Deploy"
8. Wait for deployment to complete! Copy your frontend URL!

---

## Step 4: Post-Deployment Configuration

### Update Render CORS
After your Vercel frontend is deployed, go to:
1. Render → fitsaathi-backend → Environment
2. Add your Vercel URL to `CORS_ORIGINS`:
   ```
   http://localhost:3000,http://localhost:8080,https://your-vercel-url.vercel.app
   ```

### Update Vercel Environment Variable
1. Vercel Dashboard → Settings → Environment Variables
2. Update `VITE_API_BASE_URL` to match your Render backend URL
3. Redeploy for changes to take effect

---

## Step 5: Seed the Database (Optional)

If you want sample data:
1. Run locally first with your MONGODB_URI set
2. Or use `python data/seed_inventory.py` from your project root

---

## Production Readiness Checklist

- [ ] MongoDB Atlas IP whitelisting includes `0.0.0.0/0`
- [ ] MongoDB username/password are correctly set
- [ ] Gemini API key is valid and has quota
- [ ] CORS_ORIGINS includes your production Vercel URL
- [ ] Frontend is using correct backend API URL
- [ ] All required environment variables are set in Render/Vercel
- [ ] Render health check `/health` is responding 200 OK

---

## Files Changed/Added During This Setup

- `vercel.json` - Vercel deployment config
- `render.yaml` - Render infrastructure as code
- Updated `.env.example` - Updated env vars template
- Updated `backend/config.py` - Added production CORS origins
- Updated `frontend/index.html` - Added env var injection script
- Updated `frontend/static/app.js` - Added dynamic API base URL

---

## Local Development

For local development, you can still use:
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8080

# OR
python start_server.py  # if you have it
```
