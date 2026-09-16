"""Quickstart example: Kinetic fitting of HER polarization data with TheHER.

Demonstrates loading experimental LSV data, running a kinetic fit,
extracting rate constants, and computing surface coverage and Tafel slopes.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from theher import HydrogenFitting

# Locate sample dataset (Platinum in alkaline electrolyte)
data_file = os.path.join(ROOT, "sample_data", "Pt_example.txt")

if not os.path.exists(data_file):
    raise FileNotFoundError(f"Sample data file not found at: {data_file}")

# 1. Initialize fitter with electrochemical parameters
fitter = HydrogenFitting(
    file_path=data_file,
    area_electrode=0.196,     # Electrode surface area (cm²)
    ohmic_drop=6.05,          # Ohmic resistance (Ohms) for iR compensation
    ref_potential=0.098,      # Reference electrode potential (V)
    pH=14.0,                  # Electrolyte pH
    current_col=2,            # Column index of current in file
    potential_col=1,          # Column index of potential in file
    delimiter="auto",
)

# 2. Run kinetic fit (Simplified Volmer-Heyrovsky model)
print("Running kinetic fit on Pt sample data...")
result = fitter.fit_data(
    model_type="simplified",
    fitting_method="least_squares",
    use_global_search=False,
    n_starts=2,
)

# 3. Print extracted kinetic parameters
print("\n=== Extracted Kinetic Parameters ===")
for name, val in fitter.get_params_dict().items():
    if val is not None:
        print(f"  {name:10s} : {val:.4e}")

stats = fitter.get_stats()
print(f"\nGoodness of Fit: R² = {stats['r_squared']:.4f}, Reduced Chi² = {stats['redchi']:.4e}")

# 4. Compute physical observables: Surface Coverage & Rolling Tafel Slopes
theta_h, theta_empty = fitter.compute_theta()
print(f"Hydrogen surface coverage range: [{theta_h.min():.4f}, {theta_h.max():.4f}]")

tafel_data = fitter.compute_tafel_slope(window_size=10, method="rolling")
if len(tafel_data) > 0:
    print(f"Mean rolling Tafel slope: {tafel_data[:, 1].mean():.1f} mV/dec")
print("\nDone!")
