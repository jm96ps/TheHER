# HER Fitting Analysis
**Web app for fitting and analyzing Hydrogen Evolution Reaction (HER) electrochemical data with real-time parameter adjustment and dynamic visualization.**

[![DOI](https://zenodo.org/badge/1124731941.svg)](https://doi.org/10.5281/zenodo.18099697)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

## 🌐 Live Demo

**Try the web app here:** [https://theher.onrender.com/](https://theher.onrender.com/)

## Summary

TheHER is an open-source web app that treats hydrogen evolution reaction (HER) data to extract kinetic information. With a few clicks, it is possible to deliver a bundle of information from the HER measurement, providing a general view of the reaction path. It is accomplished by fitting the polarization curves using the formalism of the well-worn reaction mechanism of HER to get the chemical kinetics constants. To evaluate the quality of fitting, besides the statistical metrics, the polarization fitted curve is printed concurrently with the hydrogen coverage($\theta_{H}$) vs. potential plot, and the Tafel slope vs. potential plot. This simultaneous analysis allows finding the parameters that not only minimize the difference between the data and the model but also find a set of parameters whose values have a physical foundation in terms of $\theta_{H}$ and the Tafel slopes. It aims not only to help expert researchers seeking a deeper analysis of the HER systems, but also to be beneficial in an academic context in electrochemistry or related courses.

## Overview

This project provides an interactive tool for:
- **Fitting** experimental HER data using kinetic models simplified 2-step (Volmer-Heyrovsky) or full 3-step mechanism(Vomer-Heyrovsky-Tafel)
- **Real-time parameter adjustment** with interactive sliders showing scientific notation
- **Dynamic visualization** including:
  - Current vs. potential curves (experimental vs. theoretical)
  - Surface coverage (θ) analysis
  - Tafel slope analysis
  - Current parameter values display

## Features

📊 **Four-Panel Analysis Dashboard**
- Current vs. Potential plot with experimental data overlay
- Surface coverage (H-adsorbed and empty sites)
- Tafel slope trends


🔬 **Multiple Model Options**
- **Simplified Model**: 2-step HER mechanism (Vomer-Heyrovsky)
- **Full Model**: 3-step HER mechanism with dependent parameter calculation (Volmer-Heyrovsky-Tafel)

⚙️ **Data Processing**
- Automatic ohmic drop correction
- Reference potential correction
- Current density normalization
- Support for LSV (linear sweep voltammetry) data

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
