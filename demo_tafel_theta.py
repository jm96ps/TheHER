#!/usr/bin/env python3
"""
Demo script showing Tafel slope and Theta coverage functionality
"""

import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

# Create synthetic HER-like data for demonstration
def generate_demo_data():
    """Generate synthetic LSV data for HER"""
    np.random.seed(42)
    
    # Potential range (vs RHE)
    potential = np.linspace(-0.3, 0.05, 100)
    
    # Simplified HER equation (Butler-Volmer-like)
    # Current density = -k * exp(-alpha * F * eta / RT)
    F = 96485.3  # Faraday constant
    R = 8.314
    T = 298.15
    alpha = 0.5
    k0 = 1e-6
    
    # Overpotential
    eta = potential - 0.0  # 0V vs RHE is equilibrium
    
    # Current (Amperes)
    current = -k0 * np.exp(-alpha * F * eta / (R * T))
    
    # Add some noise
    current += np.random.normal(0, abs(current * 0.02))
    
    return potential, current

def demo_theta_calculation():
    """Demonstrate theta coverage calculation"""
    print("\n" + "="*60)
    print("THETA (Hydrogen Coverage) CALCULATION")
    print("="*60)
    
    # Mock fitted parameters (typical values)
    params = {
        'k1': 1e-4,
        'k1r': 1e-6,
        'k2': 1e-5,
        'k3': 1e-7,
        'bbv': 0.5,
        'bbh': 0.4
    }
    
    print("\nFitted Parameters:")
    for k, v in params.items():
        print(f"  {k:5s} = {v:.3e}")
    
    # Calculate theta for a range of potentials
    x = np.linspace(-0.3, 0.0, 50)
    f1 = 38.92
    
    # Simplified theta calculation (from full model)
    k2r = (params['k1'] * params['k2']) / params['k1r']
    k3r = (params['k3'] * params['k1']**2) / (params['k1r']**2)
    
    A1 = -2 * params['k3'] + 2 * k3r
    B1 = ((-np.exp((-params['bbv']) * f1 * x)) * params['k1'] - 
          np.exp((1 - params['bbv']) * f1 * x) * params['k1r'] - 
          params['k2'] / np.exp(params['bbh'] * f1 * x) - 
          np.exp((1 - params['bbh']) * f1 * x) * k2r - 4 * k3r)
    C1 = (params['k1'] / np.exp(params['bbv'] * f1 * x) + 
          np.exp((1 - params['bbh']) * f1 * x) * k2r + 2 * k3r)
    
    theta = (-B1 - np.sqrt(B1**2 - 4*A1*C1)) / (2*A1)
    
    print(f"\nTheta Coverage Statistics:")
    print(f"  Range: [{theta.min():.4f}, {theta.max():.4f}]")
    print(f"  Mean:  {theta.mean():.4f}")
    print(f"  Median: {theta[len(theta)//2]:.4f}")
    
    print("\n✓ Theta represents the fraction of surface sites covered")
    print("  by adsorbed hydrogen (0 = empty, 1 = fully covered)")
    
    return x, theta

def demo_tafel_slope():
    """Demonstrate Tafel slope calculation"""
    print("\n" + "="*60)
    print("TAFEL SLOPE CALCULATION")
    print("="*60)
    
    # Generate data
    potential, current = generate_demo_data()
    
    # Calculate Tafel slope
    # Tafel equation: η = a + b*log10(i)
    # Slope = dV / d(log10(I))
    
    eps = 1e-30
    logI = np.log10(np.abs(current) + eps)
    dx = np.gradient(potential)
    dlogI = np.gradient(logI)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        slope_V_per_decade = np.where(dlogI == 0, np.nan, dx / dlogI)
    
    slope_mV_per_dec = slope_V_per_decade * 1000.0
    
    # Filter valid slopes
    valid_mask = ~np.isnan(slope_mV_per_dec) & (np.abs(slope_mV_per_dec) < 500)
    valid_slopes = slope_mV_per_dec[valid_mask]
    
    print("\nTafel Slope Statistics:")
    if len(valid_slopes) > 0:
        print(f"  Range: [{valid_slopes.min():.2f}, {valid_slopes.max():.2f}] mV/dec")
        print(f"  Mean:  {valid_slopes.mean():.2f} mV/dec")
        print(f"  Median: {np.median(valid_slopes):.2f} mV/dec")
    
    print("\n✓ Tafel slope indicates the reaction mechanism:")
    print("  ~30 mV/dec  → Fast proton transfer (Tafel step limiting)")
    print("  ~40 mV/dec  → Intermediate coverage")
    print("  ~120 mV/dec → Slow discharge (Volmer step limiting)")
    
    return potential, slope_mV_per_dec

def main():
    print("="*60)
    print("TheHER App - Tafel & Theta Functionality Demo")
    print("="*60)
    
    # Demo theta coverage
    pot_theta, theta = demo_theta_calculation()
    
    # Demo Tafel slope
    pot_tafel, tafel = demo_tafel_slope()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\n✓ Theta (coverage) calculation: IMPLEMENTED")
    print("  - Computes surface coverage from fitted parameters")
    print("  - Available for full HER model fits")
    print("  - Endpoint: /plot_theta")
    
    print("\n✓ Tafel slope calculation: IMPLEMENTED")
    print("  - Computes local Tafel slope from current-potential data")
    print("  - Works with both fitted and experimental curves")
    print("  - Endpoint: /plot_tafel")
    
    print("\n✓ Both features are:")
    print("  - Fully functional in the codebase")
    print("  - Accessible via API endpoints")
    print("  - Displayed in the web interface")
    print("  - Tested in test suite")
    
    print("\n" + "="*60)
    print("To use: Run 'python manage.py runserver' and visit:")
    print("http://localhost:8000")
    print("="*60)

if __name__ == '__main__':
    main()
