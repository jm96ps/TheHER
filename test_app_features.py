#!/usr/bin/env python3
"""Comprehensive test script to verify HER fitting, Tafel slope, Theta coverage, and Decomposition"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    print("Testing imports...")
    try:
        from webapp.models.hydrogen import hydrogen_fitting
        from webapp.services.fitting_service import (
            render_plot,
            render_theta_plot,
            render_tafel_plot,
            render_decomposition_plot,
            render_plots_zip
        )
        print("[OK] Successfully imported hydrogen_fitting and fitting service routines")
        return True
    except Exception as e:
        print(f"[FAIL] Error importing: {e}")
        return False

def test_tafel_theta_and_decomposition():
    print("\nTesting Tafel slope, Theta coverage, and Mechanism decomposition...")
    try:
        from webapp.models.hydrogen import hydrogen_fitting

        fixture_file = 'test_fixture.csv'
        if not os.path.exists(fixture_file):
            print(f"[FAIL] Test fixture not found: {fixture_file}")
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

        print("  Fitting data with full model (Volmer-Heyrovsky-Tafel)...")
        fitter.fit_data(model_type='full', fitting_method='powell')
        assert fitter.result_model is not None, "Fitting failed to produce result_model"

        # Test dual theta coverage
        print("  Computing dual coverage (theta_H and empty sites)...")
        theta_H, theta_empty = fitter.compute_theta()
        print(f"    [OK] Theta_H shape={theta_H.shape}, range=[{theta_H.min():.4f}, {theta_H.max():.4f}]")
        print(f"    [OK] Theta_empty shape={theta_empty.shape}, range=[{theta_empty.min():.4f}, {theta_empty.max():.4f}]")
        np.testing.assert_allclose(theta_H + theta_empty, 1.0, rtol=1e-5)

        # Test rolling Tafel slope
        print("  Computing rolling-window Tafel slope...")
        x_tafel, slope_tafel = fitter.compute_tafel_slope(use_fitted=True, window_size=5, method='rolling')
        print(f"    [OK] Tafel slope points={len(slope_tafel)}, mean={np.nanmean(slope_tafel):.2f} mV/dec")
        assert len(slope_tafel) > 0, "Tafel slope produced 0 points"

        # Test reaction decomposition
        print("  Computing reaction step decomposition...")
        decomp = fitter.compute_decomposition()
        assert 'volmer' in decomp and 'heyrovsky' in decomp and 'total' in decomp
        print(f"    [OK] Volmer & Heyrovsky rates calculated: points={len(decomp['volmer'])}")

        # Test statistics
        stats = fitter.get_stats()
        print(f"    [OK] Fit statistics: R^2={stats.get('r_squared')}, redchi={stats.get('redchi')}")

        print("[OK] All physics and modeling tests passed!")
        return True
    except Exception as e:
        print(f"[FAIL] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_plotting_and_zip():
    print("\nTesting plotting and ZIP export...")
    try:
        from webapp.services.fitting_service import (
            render_plot,
            render_theta_plot,
            render_tafel_plot,
            render_decomposition_plot,
            render_plots_zip
        )
        form = {
            'file_path': 'test_fixture.csv',
            'current_col': '1',
            'potential_col': '2',
            'area_electrode': '1.0',
            'ohmic_drop': '0.0',
            'model_type': 'simplified',
            'fitting_method': 'powell',
            'tafel_window': '5'
        }

        img_plot = render_plot(form)
        img_theta = render_theta_plot(form)
        img_tafel = render_tafel_plot(form)
        img_decomp = render_decomposition_plot(form)
        zip_bytes = render_plots_zip(form)

        assert len(img_plot) > 1000, "Polarization plot empty"
        assert len(img_theta) > 1000, "Theta plot empty"
        assert len(img_tafel) > 1000, "Tafel plot empty"
        assert len(img_decomp) > 1000, "Decomposition plot empty"
        assert len(zip_bytes) > 2000, "ZIP export empty"

        print(f"  [OK] Polarization plot generated ({len(img_plot)} bytes)")
        print(f"  [OK] Theta plot generated ({len(img_theta)} bytes)")
        print(f"  [OK] Tafel plot generated ({len(img_tafel)} bytes)")
        print(f"  [OK] Decomposition plot generated ({len(img_decomp)} bytes)")
        print(f"  [OK] ZIP bundle generated ({len(zip_bytes)} bytes)")
        return True
    except Exception as e:
        print(f"[FAIL] Plotting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_example_datasets():
    print("\nTesting all example datasets with Nernstian reference correction...")
    from webapp.models.hydrogen import hydrogen_fitting

    examples = [
        {'file': 'Pt_example.txt', 'cur': 2, 'pot': 1, 'area': 0.196, 'ohmic': 6.05, 'ref': 0.098, 'ph': 14.0},
        {'file': 'LSV_Mo2C_5_EF1_x(4)_exemple.txt', 'cur': 1, 'pot': 2, 'area': 0.196, 'ohmic': 6.05, 'ref': 0.098, 'ph': 14.0},
        {'file': 'LSV_Mo2C_EF0_3(1)_exemple.txt', 'cur': 1, 'pot': 2, 'area': 0.196, 'ohmic': 6.05, 'ref': 0.098, 'ph': 14.0},
        {'file': 'LSV_Mo2C_EF3_3(2)_exemple.txt', 'cur': 1, 'pot': 2, 'area': 0.196, 'ohmic': 6.05, 'ref': 0.098, 'ph': 14.0},
        {'file': 'Pt_NaOH_non-free_before(1)_exemple.txt', 'cur': 2, 'pot': 1, 'area': 0.196, 'ohmic': 6.05, 'ref': 0.098, 'ph': 14.0},
    ]

    for ex in examples:
        filename = ex['file']
        if not os.path.exists(filename):
            print(f"  [SKIP] {filename} not found")
            continue
        
        f = hydrogen_fitting(
            file_path=filename,
            area_electrode=ex['area'],
            ohmic_drop=ex['ohmic'],
            ref_potential=ex['ref'],
            pH=ex['ph'],
            current_col=ex['cur'],
            potential_col=ex['pot'],
            bbv_initial=0.5,
            bbh_initial=0.5,
            vary_bbv=False,
            vary_bbh=False
        )
        assert f._parsed is True, f"Failed to parse {filename}"
        assert len(f.potential) > 10, f"Insufficient points in {filename}"

        # Fit with simplified model
        f.fit_data(model_type='simplified', fitting_method='powell')
        assert f.result_model is not None, f"Fitting failed for {filename}"
        st = f.get_stats()
        r2 = st.get('r_squared')
        assert r2 is not None and r2 > 0.5, f"R^2 too low for {filename}: {r2}"
        
        # Verify coverage
        th_H, th_empty = f.compute_theta()
        assert len(th_H) == len(f.potential)
        np.testing.assert_allclose(th_H + th_empty, 1.0, rtol=1e-4)

        # Verify Tafel slope
        x_tafel, slope_tafel = f.compute_tafel_slope(window_size=10, method='rolling')
        assert len(slope_tafel) > 0

        print(f"  [OK] {filename} -> R^2={r2:.4f}, Chi-sq={st.get('chisqr'):.3e}, Points={len(f.potential)}")

    return True

if __name__ == '__main__':
    print("="*60)
    print("Testing TheHER Web App - Physics, Tafel, Theta, & Exports")
    print("="*60)
    success = True
    success &= test_imports()
    success &= test_tafel_theta_and_decomposition()
    success &= test_plotting_and_zip()
    success &= test_all_example_datasets()
    print("\n" + "="*60)
    if success:
        print("ALL TESTS PASSED [OK]")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED [FAIL]")
        sys.exit(1)
