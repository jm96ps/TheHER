# Configuration Guide

## Experimental Setup Parameters

This guide helps you configure the notebook for your specific electrochemical setup.

### 1. Electrode Specifications

**Area (cm²)**
```python
area_electrode = 0.5  # Your electrode geometric area
```

Typical values:
- Disk electrodes: 0.01 - 0.5 cm²
- Rotating disk electrodes (RDE): 0.1 - 1.0 cm²
- Carbon paper/cloth: 1.0 - 10.0 cm²

### 2. Cell Corrections

**Ohmic Drop (mV)**
```python
ohmic_drop = 6.43  # Electrolyte resistance contribution
```

- Measure using electrochemical impedance spectroscopy (EIS) or current interrupt method
- Typical values: 1 - 20 mV depending on electrolyte concentration and geometry
- Higher for non-aqueous media

**Reference Correction (V)**
```python
ref_correction = 0.924  # Adjustment to standard reference
```

Common reference offsets:
| From | To | Correction |
|------|-----|------------|
| Ag/AgCl (3M KCl) | RHE | +0.210 V |
| Ag/AgCl (1M KCl) | RHE | +0.235 V |
| Ag/AgCl (sat KCl) | RHE | +0.240-0.250 V |
| SCE | RHE | +0.242 V |

### 3. Physical Constants

**Temperature (K)**
```python
temperature = 298.15  # Room temperature (25°C)
```

Adjust for:
- Room temp variation: 293-298 K
- Heated cell experiments: up to 333 K
- f1 constant will update automatically

**Gas Constant**
```python
gas_constant = 8.314  # J/(mol·K) - Universal constant
```

This is fixed for all experiments.

### 4. Data File Format

Expected text file format with space or tab separation:

```
current (mA)  potential (V)
-0.001234     -0.500
-0.002156     -0.450
-0.003421     -0.400
...
```

Tips:
- First row with headers is automatically skipped (`skiprows=1`)
- Current should be in mA (will be normalized by area)
- Potential should be in V (absolute scale for your reference)
- Data points should be in chronological order

### 5. Model Selection

**For most cases use `'simplified'`:**
```python
model_choice = 'simplified'  # 2-step mechanism
```

When to use `'full'`:
```python
model_choice = 'full'  # 3-step mechanism with Tafel
```

Choose `'full'` if:
- Tafel slope analysis shows significant contribution from Tafel step
- Literature suggests direct combination pathway is important
- You want to include k3 (Tafel rate constant)

### 6. Fitting Parameters

The notebook uses Powell optimization with parameter bounds:

**Rate Constants Range:**
```python
k1=dict(value=rnd(), max=1e-2, min=1e-20),  # Forward Volmer
k1r=dict(value=rnd(), max=1e-2, min=1e-20), # Reverse Volmer
k2=dict(value=rnd(), max=1e-2, min=1e-20),  # Forward Heyrovsky
k2r=dict(value=rnd(), max=1e-2, min=1e-20), # Reverse Heyrovsky
```

Typical fitted values: 1e-15 to 1e-8 A/cm²

**Symmetry Factors:**
```python
bbv=dict(value=0.5, min=0, max=1, vary=True),  # Volmer
bbh=dict(value=0.5, min=0, max=1, vary=True),  # Heyrovsky/Tafel
```

Physical range: 0.0 - 1.0

### 7. Advanced Tuning

**If fitting doesn't converge:**

1. Check data quality (remove noise/outliers)
2. Try multiple runs (different random initial parameters)
3. Adjust fitting method in the notebook:
   ```python
   result_model = HER_model.fit(
       current,
       params,
       x=potential,
       method='powell',    # Try: 'leastsq', 'nelder', 'differential_evolution'
       nan_policy='omit'
   )
   ```

4. Check if data range is suitable for fitting

**For better convergence:**
- Ensure potential range covers both low and high overpotential regions
- Remove points too close to open circuit potential (OCP)
- Use data with sufficient signal-to-noise ratio

## Example Configurations

### Mo2C in Acidic Solution
```python
file_path = r'path/to/Mo2C_LSV.txt'
area_electrode = 0.5  # cm²
ohmic_drop = 6.43    # mV
ref_correction = 0.924  # V (vs RHE, measured from Ag/AgCl sat)
model_choice = 'simplified'
```

### Pt in Alkaline Solution
```python
file_path = r'path/to/Pt_LSV.txt'
area_electrode = 0.196  # 5 mm disk electrode
ohmic_drop = 12.0  # mV (higher in alkaline)
ref_correction = 0.0  # Already measured vs RHE
model_choice = 'full'  # Pt often shows Tafel pathway
```

### Transition Metal Chalcogenides
```python
file_path = r'path/to/MoS2_LSV.txt'
area_electrode = 1.0  # Carbon paper substrate
ohmic_drop = 4.5   # mV
ref_correction = 0.924  # vs RHE
model_choice = 'simplified'
```

## Validation Checklist

Before uploading results, verify:
- [ ] Data file loads without errors
- [ ] f1 calculated correctly (~38.92 at 298 K)
- [ ] Fitting converges (check print output)
- [ ] Initial plot shows reasonable fit
- [ ] Slider ranges are sensible (not all zeros or infinities)
- [ ] Parameter values are physically reasonable
- [ ] Tafel slope plot has data (at least 50 points recommended)

## Support

For issues specific to your setup:
1. Check this configuration guide
2. Review the README troubleshooting section
3. Consult HER fitting literature
4. Open an issue on GitHub with:
   - Your configuration
   - Error messages (if any)
   - Sample data (first 10-20 lines)

---

**Last Updated**: December 2024
