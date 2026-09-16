# HER Fitting Analysis

**An interactive web application for fitting and analyzing Hydrogen Evolution Reaction (HER) electrochemical data.**

[![DOI](https://zenodo.org/badge/1124731941.svg)](https://doi.org/10.5281/zenodo.18099697)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

## 🌐 Live Demo
**Try the web app here:** [https://theher.onrender.com/](https://theher.onrender.com/)

---

## 📖 Overview

**TheHER** is an open-source web application designed to process and analyze Hydrogen Evolution Reaction (HER) data to extract fundamental kinetic information. 

By fitting your polarization curves (Current vs. Potential) to well-established kinetic reaction models, you can seamlessly evaluate the quality of the fit and extract chemical kinetic constants. To provide a comprehensive view of the reaction pathway, the application plots the polarization curve concurrently with **surface hydrogen coverage ($\theta_{H}$)** and **rolling Tafel slopes**.

This tool is built to assist both expert electrochemists in deep-dive analyses and students learning electrochemistry concepts.

### Key Features
- **Four-Panel Analysis Dashboard**: Instantly visualize your Experimental Data, Fit Results, Surface Coverage, and Tafel Slopes in one place.
- **Multiple Kinetic Models**: Choose between a Simplified 2-step (Volmer-Heyrovsky) model or a Full 3-step (Volmer-Heyrovsky-Tafel) mechanism.
- **Robust Data Processing**: Built-in support for Ohmic Drop compensation and Reference Potential corrections.
- **Point-and-Click**: No coding required! Upload your `.txt` or `.csv` files and run the fit directly from your browser.

---

## 🚀 Getting Started (Local Development)

If you wish to run the web application on your local machine instead of the live demo, follow these simple steps:

### 1. Requirements
Ensure you have Python 3.8+ installed. It is highly recommended to use a virtual environment (`venv` or `conda`).

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/jm96ps/TheHER.git
cd TheHER
pip install -r requirements.txt
pip install -e .
```

### 3. Option A: Run the Web Application Locally
Launch the Django web server:
```bash
python manage.py runserver
```
Open your browser and navigate to: `http://localhost:8000`

### 4. Option B: Use as a Python Library
You can also use TheHER directly in Python scripts or Jupyter notebooks:
```python
from theher import HydrogenFitting

fitter = HydrogenFitting(
    file_path="sample_data/Pt_example.txt",
    area_electrode=0.196,
    ohmic_drop=6.05,
    ref_potential=0.098,
    pH=14.0,
    current_col=2,
    potential_col=1,
)

# Fit kinetic rates
result = fitter.fit_data(model_type="simplified")
print("Fitted rates:", fitter.get_params_dict())

# Compute surface coverage & rolling Tafel slope
theta_h, theta_empty = fitter.compute_theta()
tafel_slope = fitter.compute_tafel_slope(window_size=10)
```
See [examples/quickstart_fitting.py](examples/quickstart_fitting.py) for a complete working demonstration.

---

## 🧪 How to Use

1. **Upload Data**: Use the file upload button on the left panel to select your Linear Sweep Voltammetry (LSV) data file.
2. **Configure Parameters**: Adjust your Experimental Parameters such as Ohmic Drop, Electrode Area, Reference Potential, and pH.
3. **Select Model**: Choose between the "Simplified" or "Full" kinetic model.
4. **Run Fit**: Click the **"Run Kinetic Fitting & Analysis"** button. The application will fit the data and automatically render the analysis plots.

*Note: You can click "Load Sample Data (Pt)" to instantly load a test dataset and explore the interface.*

---

## 📚 Theory & Models

The Hydrogen Evolution Reaction in alkaline/neutral media proceeds via the following steps:
```math
\ce{2H2O + 2e- <-->H2 + OH-}
```

The application models this using combinations of the following primary steps:

1. **Volmer step** (Electrochemical hydrogen adsorption):
   ```math
   \ce{H2O + e- + M <-->[\overrightarrow{k}_1][\overrightarrow{k}_{-1}] MH + OH-}
   ```
2. **Heyrovsky step** (Electrochemical desorption):
   ```math
   \ce{H2O + MH + e-<-->[\overrightarrow{k}_2][\overrightarrow{k}_{-2}] H2 + OH-}
   ```
3. **Tafel step** (Chemical desorption, *used in Full Model*):
   ```math
   \ce{2MH<-->[{k}_3][{k}_{-3}] H2 +2M}
   ```

### Fitting Defaults and Model Properties
- **Log-space fitting**: Rate constants are optimized as natural logarithms internally to ensure positivity and scale properly.
- **Physical reporting**: Displayed `k` values are the physical rates obtained by exponentiation.
- **Symmetry factors**: Volmer ($\beta_V$) and Heyrovsky ($\beta_H$) symmetry factors are fixed at 0.5 by default but can be optionally fitted.
- **Local refinement**: The default local method is bounded `least_squares`.
- **Global search**: A global differential evolution search is optional and recommended for difficult fits, though it is slower.
- **Current weights**: Proper weighting requires experimental relative uncertainty and/or a noise floor.
- **Derived rates**: In the full model, `k2r` and `k3r` are derived parameters determined by microscopic reversibility and should only be used when justified by the underlying mechanism.

---

## 📖 References & Citation

If you use this tool in your research, please consider citing it:

```bibtex
@software{TheHER,
  author = {James Silva},
  title = {TheHER: Interactive web application for fitting and analyzing Hydrogen Evolution Reaction (HER) electrochemical data},
  year = {2026},
  url = {https://github.com/jm96ps/TheHER}
}
```

### Scientific Literature
- Lasia, Andrzej. “Mechanism and Kinetics of the Hydrogen Evolution Reaction.” *International Journal of Hydrogen Energy* 44, no. 36 (2019): 19484–518. [10.1016/j.ijhydene.2019.05.183](https://doi.org/10.1016/j.ijhydene.2019.05.183)
- van der Heijden et al. “Tafel Slope Plot as a Tool to Analyze Electrocatalytic Reactions.” *ACS Energy Letters* (2024). [10.1021/acsenergylett.4c00266](https://doi.org/10.1021/acsenergylett.4c00266)

---

## 🤖 AI Usage Disclosure

**Tool Use:** This project was developed with the assistance of Generative AI tools, including Google Gemini, OpenAI ChatGPT, and GitHub Copilot.
**Location of Use:** These tools were utilized in the generation of the software code, the drafting of documentation (including this README), and test scaffolding.
**Nature and Scope of Assistance:** AI assistance was used for initial code generation, refactoring, debugging, and drafting documentation to improve overall clarity.
**Human Verification:** The authors affirm that they take full responsibility for the accuracy, originality, and ethical/legal standards of all submitted materials. All AI-generated content (both code and text) has been thoroughly reviewed, modified, and validated by human team members who made all primary architectural and design decisions.

---

## 🤝 Contributing & Community
- **Contributing**: Please review our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests or opening issues.
- **Code of Conduct**: All participants agree to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).
- **Citation Metadata**: See [CITATION.cff](CITATION.cff) for machine-readable citation formats.

---

## 📄 License & Support
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

For issues, questions, or suggestions, please [Open an Issue](https://github.com/jm96ps/TheHER/issues) or contact `jamesmario@usp.br`.

<p align="center">
  <em>Brazil pays poorly PhD candidates. Support this project!</em><br>
  <a href="https://buymeacoffee.com/jm96ps">
    <img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee">
  </a>
</p>
