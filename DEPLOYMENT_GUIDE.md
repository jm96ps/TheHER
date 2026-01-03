# HER Web App - Render Deployment Guide

## ✅ Files Created

All necessary files for Render deployment have been created:

- `app.py` - Flask web application
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `templates/index.html` - Web interface
- `static/style.css` - Styling
- `static/app.js` - Frontend JavaScript

## 🚀 Deploy to Render

### Step 1: Commit and Push to GitHub

```bash
cd ~/TheHER-local
git add .
git commit -m "Add Flask web application for Render deployment"
git push origin main
```

### Step 2: Deploy on Render

**Option A: Automatic (Recommended)**
1. Go to https://dashboard.render.com/
2. Click "New +" → "Blueprint"
3. Connect your GitHub account
4. Select the `TheHER` repository
5. Render will detect `render.yaml` and auto-configure
6. Click "Apply" to deploy

**Option B: Manual**
1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect repository: `jm96ps/TheHER`
4. Configure:
   - Name: `theher-webapp`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: Free

### Step 3: Access Your App

After deployment (2-3 minutes), your app will be live at:
`https://theher-webapp.onrender.com` (or your chosen name)

## 📊 Using the App

1. **Upload Data**: Select your LSV .txt file and configure parameters
2. **Fit Data**: Choose model type and fit your electrochemical data
3. **Analyze**: View interactive plots and adjust parameters in real-time

## 🧪 Test Locally (Optional)

```bash
cd ~/TheHER-local
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:10000

## ✨ Features

- Upload LSV data files
- Automated HER fitting (simplified model)
- Interactive parameter adjustment
- Real-time plot updates
- Surface coverage analysis
- Tafel slope calculations

---

**Status**: Ready for deployment! ��
