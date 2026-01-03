# HER Web Application - Deployment Guide

## 🚀 Overview

This is a Flask-based web application for Hydrogen Evolution Reaction (HER) electrochemical data analysis, designed to be deployed on Render.com.

## 📁 Project Structure

```
TheHER/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deployment configuration
├── HER script/                 # Core HER analysis modules
│   ├── her_model.py
│   ├── utils.py
│   └── main.py
├── templates/                  # HTML templates
│   └── index.html
├── static/                     # Static assets
│   ├── style.css
│   └── app.js
└── README_DEPLOYMENT.md        # This file
```

## 🔧 Features

- **Data Upload**: Upload LSV (Linear Sweep Voltammetry) data files
- **Automated Fitting**: Fit data using simplified or full HER models
- **Interactive Visualization**: Real-time parameter adjustment with live plot updates
- **Surface Coverage Analysis**: Calculate and visualize H-adsorbed coverage
- **Tafel Slope Analysis**: Compare experimental and theoretical Tafel slopes

## 📦 Dependencies

All dependencies are listed in `requirements.txt`:
- Flask 3.0.0 - Web framework
- NumPy 1.26.2 - Numerical computing
- SciPy 1.11.4 - Scientific computing
- Pandas 2.1.4 - Data manipulation
- lmfit 1.2.2 - Curve fitting
- Matplotlib 3.8.2 - Plotting backend
- Gunicorn 21.2.0 - Production WSGI server

## 🌐 Deploying to Render

### Method 1: Automatic Deployment (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add HER web application"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml` and configure the service

3. **Deploy**
   - Render will automatically:
     - Install dependencies from `requirements.txt`
     - Start the app using Gunicorn
     - Assign a public URL

### Method 2: Manual Deployment

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your repository

2. **Configure Service**
   - **Name**: `theher-webapp` (or your choice)
   - **Environment**: Python 3
   - **Region**: Choose your preferred region
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or your choice)

3. **Environment Variables**
   - `PYTHON_VERSION`: `3.11.0`
   - `PORT`: `10000` (automatically set by Render)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

## 🧪 Local Testing

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit `http://localhost:10000` in your browser.

## 📊 Using the Application

1. **Upload Data**
   - Select your LSV data file (.txt format)
   - Configure electrode parameters:
     - Electrode area (cm²)
     - Ohmic drop (Ω·cm²)
     - Reference correction (V)
     - Temperature (K)
     - Gas constant (J/(mol·K))
   - Click "Upload & Process Data"

2. **Configure Fitting**
   - Choose model type:
     - **Simplified**: 2-step Volmer-Heyrovsky mechanism
     - **Full**: 3-step with Tafel pathway
   - Set initial transfer coefficients (bbv, bbh)
   - Choose whether to vary parameters during fitting
   - Click "Fit Data"

3. **Analyze Results**
   - View fitted parameters and statistics
   - Explore interactive plots:
     - Current vs Potential
     - Surface Coverage
     - Tafel Slope Analysis
   - Adjust parameters with sliders and update plots in real-time

## 📝 Data Format

Input data files should be plain text (.txt) with two columns:
```
Current(mA)    Potential(V)
-0.5           -0.25
-1.0           -0.30
...
```

First row is skipped (headers).

## 🔍 API Endpoints

### `GET /`
Main application interface

### `POST /api/upload`
Upload and process data file
- **Input**: FormData with file and parameters
- **Output**: JSON with processed data

### `POST /api/fit`
Perform HER fitting
- **Input**: JSON with data and fitting parameters
- **Output**: JSON with fitted parameters and predictions

### `POST /api/calculate`
Calculate predictions with custom parameters
- **Input**: JSON with parameters
- **Output**: JSON with predictions

### `GET /health`
Health check endpoint
- **Output**: `{"status": "healthy"}`

## 🐛 Troubleshooting

### Build Failures
- Ensure all files are committed to Git
- Check `requirements.txt` for correct package versions
- Verify Python version compatibility

### Runtime Errors
- Check Render logs: Dashboard → Your Service → Logs
- Verify file paths are correct (use relative paths)
- Ensure data format matches expected structure

### Performance Issues
- Consider upgrading to a paid plan for better performance
- Optimize data file size
- Enable caching if needed

## 🔐 Security Considerations

- File upload size limited to 16MB
- Only `.txt` files accepted for data upload
- Temporary files cleaned up after processing
- No sensitive data stored on server

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Original HER Analysis Scripts](HER%20script/)

## 🤝 Contributing

To contribute improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

See [LICENSE](LICENSE) file in repository root.

## 👥 Contact

For issues or questions, please open an issue on the [GitHub repository](https://github.com/jm96ps/TheHER).

---

**Deployed URL**: After deployment, your app will be available at:
`https://theher-webapp.onrender.com` (or your custom name)

**Status**: Ready for deployment ✅
