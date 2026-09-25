import json

with open('HER_Fitting_Tutorial.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the target cell
cell_idx = 3

old_source = "".join(nb['cells'][cell_idx]['source'])

crop_logic = """
import numpy as np

# Data Cropping by Normalized Current (mA cm-2)
# Since HER currents are negative, current >= -100 means -99, -98...
# current <= -10 means -11, -12...
current_min_mA = -100  # None to disable
current_max_mA = -10   # None to disable

current_mA = fitter.current * 1000  # fitter.current is in A cm-2, convert to mA cm-2
mask_current = np.ones_like(current_mA, dtype=bool)

if current_min_mA is not None:
    mask_current &= (current_mA >= current_min_mA)
if current_max_mA is not None:
    mask_current &= (current_mA <= current_max_mA)

if not np.all(mask_current):
    fitter.potential = fitter.potential[mask_current]
    fitter.current = fitter.current[mask_current]
    fitter.current_density = fitter.current_density[mask_current]

print(f"Loaded {len(fitter.potential)} valid data points after processing.")
"""

new_source = old_source.replace('print(f"Loaded {len(fitter.potential)} valid data points after processing.")\n', crop_logic)

# Make sure it actually replaced
if crop_logic not in new_source:
    print("Warning: Replacement failed.")
    new_source = old_source.replace('print(f"Loaded {len(fitter.potential)} valid data points after processing.")', crop_logic)

nb['cells'][cell_idx]['source'] = [line + '\n' for line in new_source.split('\n')[:-1]]
if not new_source.endswith('\n'):
    nb['cells'][cell_idx]['source'].append(new_source.split('\n')[-1])

with open('HER_Fitting_Tutorial.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook updated successfully.")
