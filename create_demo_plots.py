#!/usr/bin/env python3
"""
Visual demonstration of Tafel and Theta plots
Creates example plots showing what the app produces
"""

import numpy as np
import matplotlib.pyplot as plt
import os

def create_demo_plots():
    """Create demonstration plots for Tafel and Theta"""
    
    # Generate sample data
    potential = np.linspace(-0.3, 0.05, 100)
    
    # Mock theta coverage (from full model)
    # Typically increases (more coverage) at more negative potentials
    theta = 1 / (1 + np.exp(10 * (potential + 0.15)))
    theta = np.clip(theta, 0, 1)
    
    # Mock Tafel slope
    # Generate realistic Tafel slope values
    tafel_slope = 80 + 30 * np.sin(5 * potential) + np.random.normal(0, 5, len(potential))
    tafel_slope = np.clip(tafel_slope, 30, 150)
    
    # Create figure with both plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Theta Coverage
    ax1.plot(potential, theta, 'b-', linewidth=2.5, label='θ (H-ads)')
    ax1.fill_between(potential, 0, theta, alpha=0.3, color='blue')
    ax1.set_xlabel('Potential vs RHE (V)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Coverage θ', fontsize=12, fontweight='bold')
    ax1.set_title('Hydrogen Surface Coverage (θ)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1.1)
    ax1.legend(fontsize=10)
    
    # Add annotation
    ax1.annotate('Higher coverage\nat negative potentials', 
                xy=(-0.25, 0.8), fontsize=10,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
    
    # Plot 2: Tafel Slope
    ax2.plot(potential, tafel_slope, 'g-', linewidth=2.5, label='Tafel slope')
    ax2.fill_between(potential, 0, tafel_slope, alpha=0.3, color='green')
    ax2.set_xlabel('Potential vs RHE (V)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Tafel Slope (mV/dec)', fontsize=12, fontweight='bold')
    ax2.set_title('Tafel Slope Analysis', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    
    # Add mechanism indicators
    ax2.axhline(y=40, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax2.text(-0.28, 42, 'Volmer-Heyrovsky (~40 mV/dec)', fontsize=8, color='red')
    ax2.axhline(y=120, color='orange', linestyle='--', alpha=0.5, linewidth=1)
    ax2.text(-0.28, 122, 'Volmer limiting (~120 mV/dec)', fontsize=8, color='orange')
    
    plt.tight_layout()
    
    # Save figure
    output_dir = 'outputs'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'demo_tafel_theta_plots.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Demo plots saved to: {output_path}")
    
    # Also save individual plots
    fig1, ax = plt.subplots(figsize=(7, 5))
    ax.plot(potential, theta, 'b-', linewidth=3)
    ax.fill_between(potential, 0, theta, alpha=0.3, color='blue')
    ax.set_xlabel('Potential vs RHE (V)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Coverage θ', fontsize=12, fontweight='bold')
    ax.set_title('Hydrogen Coverage (θ)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)
    plt.tight_layout()
    theta_path = os.path.join(output_dir, 'theta_coverage_example.png')
    plt.savefig(theta_path, dpi=150, bbox_inches='tight')
    print(f"✓ Theta plot saved to: {theta_path}")
    
    fig2, ax = plt.subplots(figsize=(7, 5))
    ax.plot(potential, tafel_slope, 'g-', linewidth=3)
    ax.fill_between(potential, 0, tafel_slope, alpha=0.3, color='green')
    ax.set_xlabel('Potential vs RHE (V)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tafel Slope (mV/dec)', fontsize=12, fontweight='bold')
    ax.set_title('Tafel Slope', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    tafel_path = os.path.join(output_dir, 'tafel_slope_example.png')
    plt.savefig(tafel_path, dpi=150, bbox_inches='tight')
    print(f"✓ Tafel plot saved to: {tafel_path}")
    
    plt.show()
    
    return output_path

if __name__ == '__main__':
    print("="*60)
    print("Creating demonstration plots...")
    print("="*60)
    create_demo_plots()
    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)
