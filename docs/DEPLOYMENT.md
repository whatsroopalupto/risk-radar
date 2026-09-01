# Public Web Deployment Guide — Geopolitical Risk Radar

This document provides step-by-step instructions for deploying the **Geopolitical Risk Radar** to the web so anyone can access it via a standard browser URL without installing Python or Docker.

---

## Option 1: Streamlit Community Cloud (Recommended — Free & 1-Click)

**Streamlit Cloud** is the easiest way to deploy the dashboard online for free.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   Ensure your latest code is pushed to your GitHub repository:
   ```bash
   git add .
   git commit -m "Dashboard redesign & deployment update"
   git push origin main
   ```

2. **Sign in to Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click **Continue with GitHub** to log in.

3. **Deploy the App**:
   - Click the **New app** button.
   - Select your repository: `whatsroopalupto/risk-radar`.
   - Select Branch: `main`.
   - Set Main file path: `dashboard/app.py`.
   - Click **Deploy!**

4. **Access your live app**:
   Streamlit will build your app and give you a public URL (e.g. `https://risk-radar.streamlit.app`).
   *Anyone with this link can open the dashboard in their phone or desktop web browser!*

---

## Option 2: Render.com (Full-Stack Free Cloud Hosting)

If you want both the FastAPI backend and Streamlit dashboard hosted independently on the cloud:

1. Sign up at [Render.com](https://render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository `whatsroopalupto/risk-radar`.
4. Render will automatically detect `render.yaml` and deploy both the FastAPI Backend and Streamlit Dashboard!

---

## Option 3: Optional Local Docker (Developer Container)

If you prefer to run the application inside a local isolated container:

```bash
# Build and start container
docker-compose up --build
```
- Dashboard: `http://localhost:8501`
- Backend API: `http://localhost:8000`
