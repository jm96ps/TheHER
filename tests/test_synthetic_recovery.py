import numpy as np
import pandas as pd

from webapp.models.hydrogen import F_CONST, R_CONST, hydrogen_fitting


def test_simplified_model_recovers_the_generated_current(tmp_path):
    temperature = 298.15
    f1 = F_CONST / (R_CONST * temperature)
    potential = np.linspace(-0.20, -0.02, 120)

    true = {
        "k1": 2.0e-7,
        "k1r": 8.0e-8,
        "k2": 5.0e-7,
        "k2r": 1.5e-7,
        "bbv": 0.5,
        "bbh": 0.5,
    }
    u = f1 * potential
    numerator = (
        2.0
        * true["k1"]
        * true["k2"]
        * (1.0 - np.exp(2.0 * u))
        * np.exp(-true["bbh"] * u)
    )
    denominator = (
        true["k1"] * np.exp((true["bbh"] - true["bbv"]) * u)
        + true["k2"]
        + np.exp(u)
        * (
            true["k1r"] * np.exp((true["bbh"] - true["bbv"]) * u)
            + true["k2r"]
        )
    )
    current = -F_CONST * numerator / denominator

    input_file = tmp_path / "synthetic.csv"
    pd.DataFrame({"current_A": current, "potential_V": potential}).to_csv(
        input_file,
        index=False,
        header=False,
    )

    fitter = hydrogen_fitting(
        file_path=str(input_file),
        area_electrode=1.0,
        temperature=temperature,
        bbv_initial=0.5,
        bbh_initial=0.5,
        vary_bbv=False,
        vary_bbh=False,
        k1_min=1e-9,
        k1_max=1e-5,
        k1r_min=1e-9,
        k1r_max=1e-5,
        k2_min=1e-9,
        k2_max=1e-5,
        k2r_min=1e-9,
        k2r_max=1e-5,
    )
    result = fitter.fit_data(
        model_type="simplified",
        use_global_search=False,
        n_starts=10,
        fitting_method="least_squares",
        relative_error=0.01,
        current_noise=1e-14,
        max_nfev_local=10000,
        robust_loss="linear",
    )

    relative_current_error = np.linalg.norm(result.best_fit - current) / np.linalg.norm(current)
    assert relative_current_error < 1e-5
