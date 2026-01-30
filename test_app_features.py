#!/usr/bin/env python3
"""Test script to verify Tafel slope and Theta coverage functionality"""

import os
import sys
import numpy as np

# Add the project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all necessary modules can be imported"""
    print("Testing imports...")
    try:
        from webapp.models.hydrogen import hydrogen_fitting
        print("✓ Successfully imported hydrogen_fitting")
        return True
    except Exception as e:
        print(f"✗ Error importing: {e}")
        return False

def test_tafel_and_theta():
    """Test Tafel slope and theta coverage calculation"""
    print("\nTesting Tafel slope and Theta coverage...")
    
    try:
        from webapp.models.hydrogen import hydrogen_fitting
        
        # Use test fixture file
        fixture_file = 'test_fixture.csv'
        if not os.path.exists(fixture_file):
            print(f"✗ Test fixture not found: {fixture_file}")
            return False
        
        print(f"  Loading data from {fixture_file}...")
        fitter = hydrogen_fitting(
            file_path=fixture_file,
            area_electrode=1.0,
            ohmic_drop=0.0,
            current_col=1,
            potential_col=2,
            delimiter='auto',
            current_units='A',
            bbv_initial=0.5,
            bbh_initial=0.5
        )
        
        print("  Fitting data with full model...")
        fitter.fit_data(model_type='full', fitting_method='powell')
        
        # Test theta coverage
        print("  Computing theta (hydrogen coverage)...")
        theta = fitter.compute_theta()
        print(f"    ✓ Theta computed: shape={theta.shape}, range=[{theta.min():.4f}, {theta.max():.4f}]")
        
        # Test Tafel slope
        print("  Computing Tafel slope...")
        x, slope = fitter.compute_tafel_slope(use_fitted=True)
        print(f"    ✓ Tafel slope computed: shape={slope.shape}")
        
        # Print some statistics
        valid_slopes = slope[~np.isnan(slope)]
        if len(valid_slopes) > 0:
            print(f"    Tafel slope range: [{valid_slopes.min():.2f}, {valid_slopes.max():.2f}] mV/dec")
            print(f"    Mean Tafel slope: {valid_slopes.mean():.2f} mV/dec")
        
        print("\n✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_plotting_functions():
    """Test that plotting functions exist"""
    print("\nTesting plotting functions...")
    try:
        from webapp.services.fitting_service import render_theta_plot, render_tafel_plot
        print("  ✓ render_theta_plot imported")
        print("  ✓ render_tafel_plot imported")
        return True
    except Exception as e:
        print(f"  ✗ Error importing plotting functions: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("Testing TheHER App - Tafel & Theta Functionality")
    print("="*60)
    
    success = True
    success &= test_imports()
    success &= test_tafel_and_theta()
    success &= test_plotting_functions()
    
    print("\n" + "="*60)
    if success:
        print("ALL TESTS PASSED ✓")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)
