# Testing and Running TheHER App

## Quick Start Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Django Development Server

```bash
python manage.py runserver
```

The app will be available at: **http://localhost:8000**

### 3. Test the Features

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific theta and Tafel test
python -m pytest tests/test_hydrogen.py::test_theta_and_tafel -v

# Run with coverage
python -m pytest tests/ --cov=webapp --cov-report=html
```

### 4. Demo Scripts

```bash
# Show Tafel and Theta calculations
python demo_tafel_theta.py

# Create example plots
python create_demo_plots.py
```

## Using the Web Interface

### Step 1: Upload Data
- Go to http://localhost:8000
- Upload your electrochemical data file (LSV/CV format)
- Supported formats: `.txt`, `.csv`
- Example file: `Pt_example.txt` or `test_fixture.csv`

### Step 2: Configure Parameters
- **Model type**: Select "full" to enable theta coverage analysis
- **Initial bbv/bbh**: Transfer coefficients (default: 0.5)
- **Electrode area**: In cm² (used for current density)
- **Ohmic drop**: In Ω·cm²
- **Column indices**: Specify which columns contain current and potential

### Step 3: Run Fit
- Click "Run Fit & Plot"
- Wait for fitting to complete (may take 10-30 seconds)

### Step 4: View Results

#### Main Outputs:
1. **Fit Plot** - Current vs Potential with fitted curve
2. **Theta Coverage Plot** - Shows surface coverage (0-1)
3. **Tafel Slope Plot** - Shows local Tafel slope (mV/dec)

#### Additional Data:
- Fit statistics (χ², AIC, BIC)
- Fitted parameters (k1, k1r, k2, k2r, k3, k3r, bbv, bbh)
- Download results as JSON

## API Endpoints

| Endpoint | Method | Description | Returns |
|----------|--------|-------------|---------|
| `/fit` | POST | Run fitting algorithm | JSON with parameters and stats |
| `/plot` | POST | Generate main fit plot | PNG image |
| `/plot_theta` | POST | Generate theta coverage plot | PNG image |
| `/plot_tafel` | POST | Generate Tafel slope plot | PNG image |
| `/fit_summary` | GET/POST | Full summary page | HTML page |

### Example API Usage

```python
import requests

# Upload and fit
with open('Pt_example.txt', 'rb') as f:
    files = {'datafile': f}
    data = {
        'model_type': 'full',
        'area_electrode': '1.0',
        'ohmic_drop': '0.0',
        'current_col': '1',
        'potential_col': '2',
        'delimiter': 'auto',
        'bbv': '0.5',
        'bbh': '0.5'
    }
    
    # Get fit results
    response = requests.post('http://localhost:8000/fit', data=data, files=files)
    results = response.json()
    
    # Get theta plot
    theta_response = requests.post('http://localhost:8000/plot_theta', data=data, files=files)
    with open('theta_plot.png', 'wb') as f:
        f.write(theta_response.content)
    
    # Get Tafel plot
    tafel_response = requests.post('http://localhost:8000/plot_tafel', data=data, files=files)
    with open('tafel_plot.png', 'wb') as f:
        f.write(tafel_response.content)
```

## Understanding the Results

### Theta (θ) Coverage Plot

**What it shows:**
- Fraction of electrode surface covered by adsorbed hydrogen (H_ads)
- Range: 0 (no coverage) to 1 (full coverage)

**Physical Interpretation:**
- **High θ** (→1): Surface saturated with H_ads, reaction may shift mechanism
- **Low θ** (→0): Surface mostly empty, adsorption is rate-limiting
- **Medium θ**: Competitive adsorption/desorption

**Typical Behavior:**
- θ increases at more negative (cathodic) potentials
- θ depends on material and electrolyte conditions

### Tafel Slope Plot

**What it shows:**
- Local slope of the overpotential vs log(current) relationship
- Units: mV/decade (millivolts per decade of current)

**Physical Interpretation:**

| Tafel Slope | Mechanism | Rate-Limiting Step |
|-------------|-----------|-------------------|
| ~30 mV/dec | Volmer-Tafel | Chemical desorption (Tafel step) |
| ~40 mV/dec | Volmer-Heyrovsky | Electrochemical desorption (Heyrovsky) |
| ~120 mV/dec | Volmer limiting | Proton discharge (Volmer step) |

**Typical Values:**
- Pt in acid: ~30 mV/dec (excellent HER catalyst)
- MoS₂: ~40-60 mV/dec
- Ni: ~120 mV/dec
- Carbon: >200 mV/dec (poor HER catalyst)

## Mathematical Details

### Theta Calculation (Full Model)

```
Theta is calculated by solving:
A₁θ² + B₁θ + C₁ = 0

where:
A₁ = -2k₃ + 2k₃ᵣ
B₁ = complex expression with exponential terms
C₁ = k₁/exp(bbv·f1·V) + exp((1-bbh)·f1·V)·k₂ᵣ + 2k₃ᵣ

θ = (-B₁ - √(B₁² - 4A₁C₁)) / (2A₁)
```

### Tafel Slope Calculation

```
Tafel equation: η = a + b·log₁₀(i)
where b is the Tafel slope

Numerical calculation:
b = dV / d(log₁₀(I))
```

## Troubleshooting

### Issue: Theta plot shows error
**Solution**: Make sure you selected "full" model type. Theta is only available for full model fits.

### Issue: Tafel slope values seem unrealistic
**Solution**: 
- Check data quality (smooth LSV sweep)
- Verify ohmic correction is applied
- Ensure sufficient data points
- Check for artifacts at low/high currents

### Issue: Fitting fails
**Solution**:
- Check data file format (correct delimiter)
- Verify column indices are correct (1-based)
- Ensure current units are in Amperes (A)
- Try different initial parameters for bbv/bbh

### Issue: Plots not displaying
**Solution**:
- Check browser console for errors
- Ensure all form fields are filled
- Try refreshing the page
- Check server logs for errors

## Files Modified/Created

### Enhanced Files:
1. **webapp/templates/index.html** - Improved UI with larger plots and descriptions
2. **requirements.txt** - Fixed merge conflict, consolidated dependencies

### New Files:
1. **TAFEL_THETA_IMPLEMENTATION.md** - Complete documentation
2. **demo_tafel_theta.py** - Demonstration script
3. **create_demo_plots.py** - Example plot generator
4. **test_app_features.py** - Feature verification script
5. **RUN_AND_TEST.md** - This file

## Next Steps

### To run the app:
```bash
python manage.py runserver
```

### To test functionality:
```bash
python -m pytest tests/test_hydrogen.py -v
```

### To see demo:
```bash
python demo_tafel_theta.py
```

## Summary

✅ **Tafel slope functionality** - Fully implemented and tested  
✅ **Theta coverage functionality** - Fully implemented and tested  
✅ **Web interface** - Enhanced with better plot visibility  
✅ **API endpoints** - All working (`/plot_theta`, `/plot_tafel`)  
✅ **Documentation** - Complete guide created  
✅ **Tests** - Existing test suite covers both features  

**The app is ready to use!** Both Tafel slope and theta hydrogen coverage functions are fully functional and accessible through the web interface.
