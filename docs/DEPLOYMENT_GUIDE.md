# Deployment Guide: GitHub & Streamlit Community Cloud
## Metro Feeder Zone Screening Tool | Bengaluru (SHIFT 2026 Hackathon)

This guide walks you through pushing the project to your GitHub repository and hosting it live on the web so the judges can access it from anywhere.

---

## Step 1: Push Code to Your GitHub Repository

### 1. Create a New Repository on GitHub
1. Go to [github.com/new](https://github.com/new).
2. Enter a repository name (e.g., `metro-feeder-screening-bengaluru`).
3. Set visibility to **Public** (required for free Streamlit Cloud hosting).
4. **Do NOT** initialize with a README, `.gitignore`, or license (we already have all of these prepared).
5. Click **Create repository**.
6. Copy your repository URL (e.g., `https://github.com/<your-username>/metro-feeder-screening-bengaluru.git`).

### 2. Add the Remote and Push from Terminal
Run the following commands in your project terminal:

```bash
# 1. Set the main branch name (standard for GitHub)
git branch -M main

# 2. Add your GitHub repository as the remote origin
# (Replace with your actual GitHub URL copied in step 1)
git remote add origin https://github.com/<your-username>/metro-feeder-screening-bengaluru.git

# 3. Push all commits and branches to GitHub
git push -u origin main
```

*(If you ever need to update or push new changes later, simply run `git push origin main`)*.

---

## Step 2: Deploy Free Live Web App on Streamlit Cloud

Once your code is pushed to GitHub, you can host the interactive dashboard live for free on **Streamlit Community Cloud**:

1. Go to [**share.streamlit.io**](https://share.streamlit.io) and sign in with your GitHub account.
2. Click the **"New app"** (or **"Create app"**) button.
3. Fill in the deployment form:
   - **Repository:** Select `<your-username>/metro-feeder-screening-bengaluru`
   - **Branch:** `main`
   - **Main file path:** `app/main.py`
   - **App URL:** (Optional custom URL slug, e.g., `bengaluru-metro-feeder.streamlit.app`)
4. Click **Deploy!**

### Why It Deploys Automatically Without Errors:
- ✅ **System Dependencies (`packages.txt`):** Includes `libgdal-dev` and `gdal-bin` so geospatial libraries compile on Linux.
- ✅ **Python Dependencies (`requirements.txt`):** Includes exact scientific packages (`geopandas`, `h3`, `folium`, `plotly`, `osmnx`).
- ✅ **Theme Configuration (`.streamlit/config.toml`):** Configures primary colors, fonts, and headless server settings.
- ✅ **Self-Contained Data (`data/output/`):** All H3 cells, catchment GeoPackages, station rankings, and sensitivity matrices are committed directly in Git.

---

## Step 3: Presenting the Live URL to the Jury

Once deployed on Streamlit Cloud, you will receive a public link:
`https://<your-app-name>.streamlit.app`

- Put this link in your **hackathon submission portal** and **presentation slide deck**.
- Judges can open the link directly on their own phones, tablets, or laptops during the live demo!
