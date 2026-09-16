#!/usr/bin/env python3
"""Comprehensive test script to verify HER fitting, Tafel slope, Theta coverage, and Decomposition."""

import os
import sys
import numpy as np

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FIXTURE = os.path.join(ROOT, "test_fixture.csv")
if not os.path.exists(FIXTURE):
    FIXTURE = os.path.join(ROOT, "sample_data", "test_fixture.csv")


def test_imports():
    """Verify that HydrogenFitting and all service routines import cleanly."""
    from webapp.models.hydrogen import HydrogenFitting, hydrogen_fitting
    from webapp.services.fitting_service import (
        render_plot,
        render_theta_plot,
        render_tafel_plot,
        render_plots_zip,
    )
    assert HydrogenFitting is not None
    assert hydrogen_fitting is HydrogenFitting
    assert callable(render_plot)
    assert callable(render_theta_plot)
    assert callable(render_tafel_plot)
    assert callable(render_plots_zip)


def test_tafel_theta_and_decomposition():
    """Verify Tafel slope, dual Theta coverage, and step decomposition."""
    from webapp.models.hydrogen import HydrogenFitting

    assert os.path.exists(FIXTURE), f"Test fixture not found at {FIXTURE}"

    fitter = HydrogenFitting(
        file_path=FIXTURE,
        area_electrode=1.0,
        ohmic_drop=0.0,
        current_col=1,
        potential_col=2,
        delimiter="auto",
        current_units="A",
        bbv_initial=0.5,
        bbh_initial=0.5,
    )

    fitter.fit_data(model_type="full", fitting_method="powell")
    assert fitter.result_model is not None, "Fitting failed to produce result_model"

    # Test dual theta coverage
    theta_H, theta_empty = fitter.compute_theta()
    assert theta_H.size > 0
    assert np.all(theta_H >= 0.0)
    assert np.all(theta_H <= 1.0)
    np.testing.assert_allclose(theta_H + theta_empty, 1.0, rtol=1e-5)

    # Test rolling Tafel slope
    tafel_data = fitter.compute_tafel_slope(use_fitted=True, window_size=5, method="rolling")
    assert len(tafel_data) > 0, "Tafel slope produced 0 points"
    slope_tafel = tafel_data[:, 1]
    assert np.all(np.isfinite(slope_tafel))
    assert np.all(slope_tafel > 0)

    # Test reaction decomposition
    decomp = fitter.compute_decomposition()
    assert "volmer" in decomp and "heyrovsky" in decomp and "total" in decomp
    assert len(decomp["volmer"]) == len(fitter.potential)

    # Test statistics
    stats = fitter.get_stats()
    assert stats.get("r_squared") is not None
    assert stats.get("chisqr") is not None


def test_plotting_and_zip():
    """Verify generation of PNG plot bytes and ZIP bundle."""
    from webapp.services.fitting_service import (
        render_plot,
        render_theta_plot,
        render_tafel_plot,
        render_plots_zip,
    )

    form = {
        "file_path": FIXTURE,
        "current_col": "1",
        "potential_col": "2",
        "area_electrode": "1.0",
        "ohmic_drop": "0.0",
        "model_type": "simplified",
        "fitting_method": "powell",
        "tafel_window": "5",
    }

    img_plot = render_plot(form)
    img_theta = render_theta_plot(form)
    img_tafel = render_tafel_plot(form)
    zip_bytes = render_plots_zip(form)

    assert len(img_plot) > 1000, "Polarization plot empty"
    assert len(img_theta) > 1000, "Theta plot empty"
    assert len(img_tafel) > 1000, "Tafel plot empty"
    assert len(zip_bytes) > 2000, "ZIP export empty"


def test_all_example_datasets():
    """Verify loading and fitting across all benchmark datasets."""
    from webapp.models.hydrogen import HydrogenFitting

    examples = [
        {"file": "Pt_example.txt", "cur": 2, "pot": 1, "area": 0.196, "ohmic": 6.05, "ref": 0.098, "ph": 14.0},
        {"file": "LSV_Mo2C_5_EF1_x(4)_exemple.txt", "cur": 1, "pot": 2, "area": 0.196, "ohmic": 6.05, "ref": 0.098, "ph": 14.0},
        {"file": "LSV_Mo2C_EF0_3(1)_exemple.txt", "cur": 1, "pot": 2, "area": 0.196, "ohmic": 6.05, "ref": 0.098, "ph": 14.0},
        {"file": "LSV_Mo2C_EF3_3(2)_exemple.txt", "cur": 1, "pot": 2, "area": 0.196, "ohmic": 6.05, "ref": 0.098, "ph": 14.0},
        {"file": "Pt_NaOH_non-free_before(1)_exemple.txt", "cur": 2, "pot": 1, "area": 0.196, "ohmic": 6.05, "ref": 0.098, "ph": 14.0},
    ]

    for ex in examples:
        filename = ex["file"]
        file_path = os.path.join(ROOT, "sample_data", filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(ROOT, filename)
        if not os.path.exists(file_path):
            continue

        f = HydrogenFitting(
            file_path=file_path,
            area_electrode=ex["area"],
            ohmic_drop=ex["ohmic"],
            ref_potential=ex["ref"],
            pH=ex["ph"],
            current_col=ex["cur"],
            potential_col=ex["pot"],
            bbv_initial=0.5,
            bbh_initial=0.5,
            vary_bbv=False,
            vary_bbh=False,
        )
        assert f._parsed is True, f"Failed to parse {filename}"
        assert len(f.potential) > 10, f"Insufficient points in {filename}"

        mtype = "full" if "Pt" in filename else "simplified"
        f.fit_data(model_type=mtype, fitting_method="powell")
        assert f.result_model is not None, f"Fitting failed for {filename}"
        st = f.get_stats()
        r2 = st.get("r_squared")
        assert r2 is not None and r2 > 0.5, f"R^2 too low for {filename}: {r2}"

        th_H, th_empty = f.compute_theta()
        assert len(th_H) == len(f.potential)
        np.testing.assert_allclose(th_H + th_empty, 1.0, rtol=1e-4)

        tafel_data = f.compute_tafel_slope(window_size=10, method="rolling")
        assert len(tafel_data) > 0
