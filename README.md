# HER Fitting Analysis

**Script and Interactive Jupyter notebook for fitting and analyzing Hydrogen Evolution Reaction (HER) electrochemical data with real-time parameter adjustment and dynamic visualization.**

[![DOI](https://zenodo.org/badge/1124731941.svg)](https://doi.org/10.5281/zenodo.18099697)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

## Overview

This project provides an interactive tool for:
- **Fitting** experimental HER data using kinetic models (simplified 2-step or full 3-step mechanism)
- **Real-time parameter adjustment** with interactive sliders showing scientific notation
- **Dynamic visualization** including:
  - Current vs. potential curves (experimental vs. theoretical)
  - Surface coverage (θ) analysis
  - Tafel slope analysis
  - Current parameter values display

## Features

✨ **Interactive Sliders**
- Log-scale sliders for rate constants (k1, k1r, k2, k2r, k3, k3r)
- Linear sliders for symmetry factors (bbv, bbh)
- Real-time scientific notation display (e.g., 1.23e-10)

📊 **Four-Panel Analysis Dashboard**
- Current vs. Potential plot with experimental data overlay
- Surface coverage (H-adsorbed and empty sites)
- Tafel slope trends
- Parameter display box

🔬 **Multiple Model Options**
- **Simplified Model**: 2-step HER mechanism (Vomer-Heyrovsky)
- **Full Model**: 3-step HER mechanism with dependent parameter calculation (Volmer-Heyrovsky-Tafel)

⚙️ **Data Processing**
- Automatic ohmic drop correction
- Reference potential correction
- Current density normalization
- Support for LSV (linear sweep voltammetry) data

## Installation

### Prerequisites
- Python 3.8+
- Jupyter Lab or Jupyter Notebook

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/LSV_Fitting_HER.git
   cd LSV_Fitting_HER
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

1. **Launch Jupyter**
   ```bash
   jupyter notebook
   ```

2. **Open the notebook**
   - Open `HER_Interactive_Analysis.ipynb`

3. **Configure your data**
   - Edit the file path in the "Load and Process Experimental Data" cell:
     ```python
     file_path = r'path/to/your/data.txt'
     area_electrode = 0.5  # cm²
     ohmic_drop = 6.43    # ohm
     ref_correction = 0.924  # V
     ```

4. **Run all cells**
   - Execute cells in order to fit data and launch interactive interface

5. **Adjust parameters**
   - Use the interactive sliders to explore parameter sensitivity
   - Watch plots update in real-time

## Data Format

Expected input format for LSV data files:

```
current (mA)  potential (V)
value1        value1
value2        value2
...           ...
```

Example:
```
-0.001234  -0.500
-0.002156  -0.450
-0.003421  -0.400
```

**Note**: First row should be headers or will be skipped with `skiprows=1`

## File Structure

```
LSV_Fitting_HER/
├── HER_Interactive_Analysis.ipynb   # Main interactive notebook
├── her_model.py                      # Core HER model functions
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── Fit_LSV_Mo2C_*.txt               # Example fitting results
├── Theta_LSV_Mo2C_*.txt             # Surface coverage data
└── V_LSV_Mo2C_*.txt                 # Potential data
```

## Key Parameters

### Rate Constants
| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| $k_1$ (k1) | Forward rate const. (Volmer step) | $10^{-12}\ to\ 0.01\ mol\ cm^{-2}\ s^{-1}$ |
| $k_{-1}$(k1r) | Reverse rate const. (Volver step) | $10^{-12}\ to\ 0.01\ mol\ cm^{-2}\ s^{-1}$ |
| $k_2$(k2) | Forward rate const. (Heyrovsky step ) | $10^{-12}\ to\ 0.01\ mol\ cm^{-2}\ s^{-1}$ |
| $k_{-2}$(k2r) | Reverse rate const. (Heyrovsky step) | Computed from $k_{1},\ k_{-1},\ k_{2}$ |

### Symmetry Factors
| Parameter | Description | Range |
|-----------|-------------|-------|
| $\beta_v$ (bbv) | Symmetry factor (Volmer) | 0.0 - 1.0 |
| $\beta_h$ (bbh) | Symmetry factor (Heyrovsky) | 0.0 - 1.0 |

### Physical Constants
| Constant | Value | Unit |
|----------|-------|------|
| F (Faraday) | 96485.3 | C/mol |
| R | 8.314 | J/(mol·K) |
| T | 298.15 | K |
| $f1=\frac{F}{RT}$ | ~38.92 | 1/V (at 298K) |

## Notebook Workflow

1. **Setup** - Configure plotting and imports
2. **Core Functions** - Load HER model equations
3. **Data Loading** - Import and process experimental data
4. **Model Selection** - Choose simplified or full model
5. **Fitting** - Perform non-linear regression using lmfit
6. **Interactive UI** - Create parameter sliders
7. **Visualization** - Real-time plot generation
## HER Models
```math
\ce{2H2O + 2e- <-->H2 + OH-}
```
### Simplified Model (2-step)
Volmer step
```math
\ce{H2O + e- + M <-->[\overrightarrow{k}_1][\overrightarrow{k}_{-1}] MH + OH-}
```
Heyrovsky step
```math
\ce{H2O + MH + e-<-->[\overrightarrow{k}_2][\overrightarrow{k}_{-2}] H2 + OH-}           (step 2, Heyrovsky)
```
Tafel step (Full Model)
```math
\ce{2MH<-->[{k}_3][{k}_{-3}] H2 +2M}           (step 2, Heyrovsky)
```
## Customization

### Change Model Type
Edit in "Fit Data with Simplified or Full Model" cell:
```python
model_choice = 'simplified'  # or 'full'
```

### Adjust Slider Ranges
Modify the fitting parameter constraints in the model setup:
```python
k1=dict(value=initial_value, max=1e-2, min=1e-20)
```

### Modify Data Processing
Edit electrode parameters:
```python
area_electrode = 0.5  # Your electrode area (cm²)
ohmic_drop = 6.43     # Your ohmic drop (ohm)
ref_correction = 0.924 # Your reference potential (V) (mercury oxide reference electrode in 1 NaOH (pH=14))
```

## Dependencies

See `requirements.txt` for all packages. Main dependencies:

- **numpy** - Numerical computations
- **pandas** - Data manipulation
- **scipy** - Statistical analysis
- **lmfit** - Non-linear curve fitting
- **plotly** - Interactive visualizations
- **ipywidgets** - Jupyter interactive widgets
- **matplotlib** - Plotting backend

## Examples

### Example 1: Basic Usage
```python
# Load your data
file_path = 'data/Mo2C_LSV.txt'
# Run cells in order
# Sliders appear automatically after fitting
```

### Example 2: Export Results
```python
# After fitting, access results
fitted_params = result_model.params
fitted_curve = result_model.best_fit

# Save to CSV
import csv
with open('fitted_params.csv', 'w') as f:
    for key, value in fitted_params.items():
        f.write(f"{key},{value.value}\n")
```

## Troubleshooting

### Sliders show "0.00"
- Ensure FloatLogSlider is imported
- Check if parameters are truly small values
- Solution: Already configured to show scientific notation

### Fitting doesn't converge
- Try different initial parameters (run cell again for new `rnd()` values)
- Check data quality and format
- Increase iteration limit in fitting parameters

### Plots don't update
- Ensure sliders are connected to `on_value_change` callback
- Check browser console for errors
- Restart kernel if needed

## Performance Tips

- For large datasets (>1000 points), consider downsampling
- Use simplified model for faster fitting
- Increase slider step size if UI feels sluggish

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Push to the branch
5. Open a Pull Request

## References

- Lasia, Andrzej. “Mechanism and Kinetics of the Hydrogen Evolution Reaction.” International Journal of Hydrogen Energy 44, no. 36 (2019): 19484–518. [10.1016/j.ijhydene.2019.05.183](10.1016/j.ijhydene.2019.05.183)

- Onno van der Heijden, Sunghak Park, Rafaël E. Vos, Jordy J. J. Eggebeen, and Marc T. M. Koper. “Tafel Slope Plot as a Tool to Analyze Electrocatalytic Reactions.” ACS Energy Letters, American Chemical Society, April 1, 2024, 1871–79. [10.1021/acsenergylett.4c00266](10.1021/acsenergylett.4c00266)



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{TheHER,
  author = {James Silva},
  title = {*Script and Interactive Jupyter notebook for fitting and analyzing Hydrogen Evolution Reaction (HER) electrochemical data with real-time parameter adjustment and dynamic visualization.},
  year = {2026},
  url = {https://github.com/jm96ps/TheHER}
}
```

## Support
Brazil pays poorly phD candidates.\
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/jm96ps)


For issues, questions, or suggestions:
- Open an [Issue](https://github.com/jm96ps/TheHER/issues)
- Contact: jamesmario@usp.br

---

**Last Updated**: January 2026
**Status**: Active Development ✓
