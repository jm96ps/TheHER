import json

with open('HER_Fitting_Tutorial.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_source = """import os
import json
import pandas as pd

export_dir = 'results'
os.makedirs(export_dir, exist_ok=True)

# Extract a safe base name from the file_path to prefix the exported files
try:
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    prefix = f"{base_name}_" if base_name else ""
except NameError:
    prefix = ""

# 1. Save Fit Report
with open(os.path.join(export_dir, f'{prefix}Fit_Report.txt'), 'w', encoding='utf-8') as f:
    f.write(fitter.result_model.fit_report())

# 2. Save Metadata JSON
metadata = {
    "model_type": model_type,
    "temperature_K": 298.15,
    "pH": 14.0,
    "area_electrode_cm2": 0.196,
    "ohmic_drop_ohm": 6.05,
    "ref_potential_V_vs_SHE": 0.098,
    "stats": stats
}
with open(os.path.join(export_dir, f'{prefix}fit_metadata.json'), 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2)

# 3. Export Polarization Curve CSV (with raw residuals)
# Note: y_data and y_fit are in Amperes internally in the model
df_polarization = pd.DataFrame({
    'potential_corrected_V': x_data,
    'current_exp_A': fitter.current,
    'current_fit_A': fitter.result_model.eval(x=x_data),
    'residual_raw_A': fitter.result_model.eval(x=x_data) - fitter.current
})
df_polarization.to_csv(os.path.join(export_dir, f'{prefix}polarization_curve.csv'), index=False)

# 4. Export Theta Coverage CSV
df_theta = pd.DataFrame({
    'Potential_V': x_data,
    'Theta_H': theta_H,
    'Theta_Empty': theta_empty
})
df_theta.to_csv(os.path.join(export_dir, f'{prefix}theta_coverage.csv'), index=False)

# 5. Export Tafel Slope CSV
min_len = min(len(x_exp_t), len(x_fit_t))
df_tafel = pd.DataFrame({
    'Potential_V': x_exp_t[:min_len],
    'Tafel_Slope_Data_mV_dec': y_exp_t[:min_len],
    'Tafel_Slope_Fit_mV_dec': y_fit_t[:min_len]
})
df_tafel.to_csv(os.path.join(export_dir, f'{prefix}tafel_slope.csv'), index=False)

# 6. Export PNG Figures
fig1.savefig(os.path.join(export_dir, f'{prefix}polarization_curve.png'), dpi=150, bbox_inches='tight')
fig2.savefig(os.path.join(export_dir, f'{prefix}theta_coverage.png'), dpi=150, bbox_inches='tight')
fig3.savefig(os.path.join(export_dir, f'{prefix}tafel_slope.png'), dpi=150, bbox_inches='tight')

print(f"All data and figures successfully exported to the '{export_dir}' folder with prefix '{prefix}'.")
"""

nb['cells'][11]['source'] = [line + '\n' for line in new_source.split('\n')]

with open('HER_Fitting_Tutorial.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
