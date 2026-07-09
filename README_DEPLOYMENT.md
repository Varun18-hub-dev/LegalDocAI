# 🚀 LegalDocAI — Deployment Guide

This document outlines the steps to run `LegalDocAI` locally in a Docker container and deploy it as a unified single-service container to **Railway** with persistent storage.

---

## 💻 Local Docker Execution

To package, run, and verify the container build locally before deploying:

1. **Build the Docker Image**:
   ```bash
   docker build -t legaldocai .
   ```

2. **Run the Container**:
   Create a local folder to simulate the Railway persistent volume (e.g. `./data` in your project folder) and pass your environment variables:
   ```bash
   docker run -p 8000:8000 -v "$(pwd)/data:/data" --env-file server/.env legaldocai
   ```

---

## 🚊 Railway Single-Service Deployment

Follow these steps to deploy on Railway with persistent storage:

### Step 1: Create a Railway Project
1. Log into your [Railway Console](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository containing `LegalDocAI`.

### Step 2: Configure Persistent Storage Volume
1. In your Railway service dashboard, click **Settings**.
2. Scroll to the **Volumes** section and click **Add Volume**.
3. Set the **Mount Path** to `/data`.
4. Click **Create Volume**. (This ensures SQLite databases, ChromaDB vectors, and uploaded PDF files persist across container redeployments).

### Step 3: Add Required Environment Variables
Go to the **Variables** tab of your service and add the following variables:
* `APP_ENV`: `production`
* `DATA_DIR`: `/data`
* `GEMINI_API_KEY`: *(Your Google AI Gemini API Key)*
* `JWT_SECRET_KEY`: *(A secure random secret hash)*
* `JWT_ALGORITHM`: `HS256`
* `ACCESS_TOKEN_EXPIRE_MINUTES`: `60`
* `ADMIN_EMAIL`: *(Your custom admin email address)*
* `ADMIN_PASSWORD`: *(Your secure admin password)*
* `ADMIN_NAME`: `LegalDocAI Admin`
* `FRONTEND_URL`: *(Your Railway Service URL, e.g., `https://legaldocai-production.up.railway.app`)*
* `CORS_ORIGINS`: *(Your Railway Service URL)*

Railway automatically binds the server to the `$PORT` environment variable.

---

## 🔒 First Admin Login
1. Public admin signup is disabled for security.
2. During the container's boot, the server checks if the user specified in `ADMIN_EMAIL` exists in the database.
3. If not, it automatically registers them with the password specified in `ADMIN_PASSWORD` and sets their role to `ADMIN`.
4. To access the admin panel, simply log in through the normal `/login` page with your `ADMIN_EMAIL` and `ADMIN_PASSWORD`.

---

## 🔗 Verification URLs

Once deployed, the following routes will be served from your unified Railway URL:

* **React Frontend Homepage**: `https://<your-app>.up.railway.app/`
* **Swagger API Documentation**: `https://<your-app>.up.railway.app/docs`
* **Backend Health Check**: `https://<your-app>.up.railway.app/api/health`
* **Login SPA View**: `https://<your-app>.up.railway.app/login`
* **Admin Workspace Dashboard**: `https://<your-app>.up.railway.app/admin/dashboard`
* **User Workspace Dashboard**: `https://<your-app>.up.railway.app/user/dashboard`
