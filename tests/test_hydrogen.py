import os
import numpy as np
from webapp.models.hydrogen import hydrogen_fitting

HERE = os.path.dirname(__file__)
FIXTURE = os.path.abspath(os.path.join(HERE, "..", "test_fixture.csv"))


def test_parse_and_construct_default_parameters():
    fitter = hydrogen_fitting(
        file_path=FIXTURE,
        area_electrode=1.0,
        ohmic_drop=0.0,
        current_col=1,
        potential_col=2,
        delimiter="auto",
        current_units="A",
    )
    assert fitter._parsed is True
    assert fitter.current.size >= 2
    assert fitter.potential.size == fitter.current.size

    params = fitter._make_log_params("simplified")
    assert "log_k1" in params
    assert "k1" in params
    assert params["k1"].expr == "exp(log_k1)"
    assert params["k1"].value > 0
    assert params["bbv"].vary is False
    assert params["bbh"].vary is False


def test_full_model_has_derived_reverse_rates():
    fitter = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0)
    params = fitter._make_log_params("full")

    assert params["k2r"].expr == "(k1*k2)/k1r"
    assert params["k3r"].expr == "(k3*k1**2)/(k1r**2)"
    assert "log_k3" in params


def test_simplified_local_fit_has_finite_output():
    fitter = hydrogen_fitting(
        file_path=FIXTURE,
        area_electrode=1.0,
        vary_bbv=False,
        vary_bbh=False,
    )
    result = fitter.fit_data(
        model_type="simplified",
        fitting_method="least_squares",
        use_global_search=False,
        n_starts=2,
        max_nfev_local=2000,
        relative_error=0.03,
    )

    assert result.success
    assert np.isfinite(result.chisqr)
    assert np.all(np.isfinite(result.best_fit))
    assert np.all(np.isfinite(result.residual))
    assert result.params["k1"].value > 0
    assert result.params["k1r"].value > 0
    assert result.params["k2"].value > 0
    assert result.params["k2r"].value > 0


def test_fitted_coverage_is_physical_when_fit_is_valid():
    fitter = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0)
    fitter.fit_data(
        model_type="simplified",
        fitting_method="least_squares",
        use_global_search=False,
        n_starts=1,
        max_nfev_local=2000,
    )
    theta_h, theta_empty = fitter.compute_theta()

    assert np.all(np.isfinite(theta_h))
    assert np.all(theta_h >= 0.0)
    assert np.all(theta_h <= 1.0)
    assert np.allclose(theta_h + theta_empty, 1.0)


# ──────────────────────────────────────────────────────────────────────────────
# Section 9.2 — Log-parametrização cria taxas físicas positivas (explícito)
# ──────────────────────────────────────────────────────────────────────────────

def test_log_parameterization_creates_positive_physical_rates():
    """Taxas físicas k_i devem ser positivas e expressas via exp(log_k_i)."""
    fitter = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0)
    params = fitter._make_log_params("simplified")

    for name in ("k1", "k1r", "k2", "k2r"):
        assert name in params, f"Parâmetro físico ausente: {name}"
        assert f"log_{name}" in params, f"log_{name} ausente nos parâmetros"
        assert params[name].expr == f"exp(log_{name})", (
            f"{name}.expr deve ser 'exp(log_{name})'"
        )
        assert params[name].value > 0, f"{name} deve ser positivo"


# ──────────────────────────────────────────────────────────────────────────────
# Section 9.3 — Taxas derivadas no modelo full (explícito e independente)
# ──────────────────────────────────────────────────────────────────────────────

def test_full_model_derived_rate_constants_explicit():
    """k2r e k3r devem ser derivados por relações de equilíbrio termodinâmico."""
    fitter = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0)
    params = fitter._make_log_params("full")

    assert params["k2r"].expr == "(k1*k2)/k1r", (
        "k2r deve satisfazer equilíbrio: k2r = k1*k2/k1r"
    )
    assert params["k3r"].expr == "(k3*k1**2)/(k1r**2)", (
        "k3r deve satisfazer equilíbrio: k3r = k3*k1²/k1r²"
    )
    # Parâmetros derivados NÃO devem ser ajustados diretamente
    assert params["k2r"].vary is False, "k2r derivado não deve variar diretamente"
    assert params["k3r"].vary is False, "k3r derivado não deve variar diretamente"


# ──────────────────────────────────────────────────────────────────────────────
# Section 9.4 — Teste sintético de recuperação de resposta conhecida
# ──────────────────────────────────────────────────────────────────────────────

def _make_synthetic_fitter():
    """Cria um fitter a partir de dados sintéticos gerados pelo próprio modelo."""
    import tempfile, csv

    # Parâmetros de referência (valores físicos típicos para HER em Pt alcalino)
    TRUE_K1  = 5e-6
    TRUE_K1R = 2e-8
    TRUE_K2  = 3e-5
    TRUE_K2R = 1e-7
    BBV = 0.5
    BBH = 0.5

    F = 96485.3321
    T = 298.15
    R = 8.314462618
    f1 = F / (R * T)

    potential = np.linspace(-0.40, -0.02, 60)

    def simplified_current(E):
        u = f1 * E
        k1, k1r, k2, k2r = TRUE_K1, TRUE_K1R, TRUE_K2, TRUE_K2R
        bbv, bbh = BBV, BBH
        e_u      = np.exp(u)
        e_shift  = np.exp((bbh - bbv) * u)
        num      = 2.0 * k1 * k2 * (1.0 - e_u**2) * np.exp(-bbh * u)
        den      = k1 * e_shift + k2 + e_u * (k1r * e_shift + k2r)
        return -F * num / den

    current = simplified_current(potential)

    # Adicionar ruído de ≈ 1%
    rng = np.random.default_rng(42)
    current_noisy = current * (1.0 + rng.normal(0, 0.01, size=current.size))

    # Escrever CSV temporário
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8'
    )
    writer = csv.writer(tmp)
    for e, i in zip(potential, current_noisy):
        writer.writerow([e, i])
    tmp_path = tmp.name
    tmp.close()

    fitter = hydrogen_fitting(
        file_path=tmp_path,
        area_electrode=1.0,
        ohmic_drop=0.0,
        ref_potential=0.0,
        pH=0.0,
        temperature=T,
        current_col=2,
        potential_col=1,
        delimiter=',',
        current_units='A',
        vary_bbv=False,
        vary_bbh=False,
    )
    return fitter, tmp_path


def test_synthetic_recovery_simplified_shape():
    """O ajuste deve recuperar a forma da curva sintética com R² > 0.95."""
    import os

    fitter, tmp_path = _make_synthetic_fitter()
    try:
        result = fitter.fit_data(
            model_type='simplified',
            fitting_method='least_squares',
            use_global_search=False,
            n_starts=5,
            max_nfev_local=5000,
            relative_error=0.03,
        )

        assert result is not None, "fit_data deve retornar um objeto de resultado"
        assert result.success, "O ajuste sintético deve convergir"
        assert np.all(np.isfinite(result.best_fit)), "best_fit deve ser finito"
        assert np.all(np.isfinite(result.residual)), "Resíduos devem ser finitos"

        # Verificar qualidade: correlação entre fit e dados deve ser alta
        y_exp = np.asarray(fitter.current)
        y_fit = np.asarray(result.best_fit)
        ss_res = np.sum((y_exp - y_fit) ** 2)
        ss_tot = np.sum((y_exp - np.mean(y_exp)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        assert r_squared > 0.95, (
            f"R² = {r_squared:.4f} — o ajuste deve recuperar a forma sintética com R² > 0.95"
        )

        # Verificar que taxas são positivas
        for name in ("k1", "k1r", "k2", "k2r"):
            assert result.params[name].value > 0, f"{name} deve ser positivo"

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def test_volmer_tafel_log_params():
    fitter = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0)
    for model_name in ("Volmer-Tafel", "tafel_volmer", "VT"):
        params = fitter._make_log_params(model_name)
        for name in ("k1", "k1r", "k3", "k3r"):
            assert name in params, f"{name} must be in Volmer-Tafel params"
            assert f"log_{name}" in params, f"log_{name} must be in Volmer-Tafel params"
            assert params[name].expr == f"exp(log_{name})"
            assert params[name].value > 0
        assert "bbv" in params
        assert "k2" not in params
        assert "bbh" not in params


def test_volmer_tafel_theta_lasia_equations():
    fitter = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0)
    potentials = np.linspace(-0.6, 0.1, 50)

    # 1. Quadratic regime: k3 != k3r
    k1, k1r, k3, k3r, bbv = 1e-6, 1e-7, 1e-5, 1e-8, 0.5
    theta = fitter._theta_volmer_tafel(potentials, k1, k1r, k3, k3r, bbv, strict=True)
    assert theta is not None
    assert np.all(np.isfinite(theta))
    assert np.all(theta >= 0.0)
    assert np.all(theta <= 1.0)

    # Check Lasia Eq. 97 residue: a*theta^2 + b*theta + c == 0
    u = fitter.f1 * potentials
    k1_fwd = k1 * fitter._safe_exp(-bbv * u)
    k1_rev = k1r * fitter._safe_exp((1.0 - bbv) * u)
    a = 2.0 * k3 - 2.0 * k3r
    b = 4.0 * k3r + k1_fwd + k1_rev
    c = -k1_fwd - 2.0 * k3r
    residue = a * (theta ** 2) + b * theta + c
    assert np.allclose(residue, 0.0, atol=1e-10), f"Max residue: {np.max(np.abs(residue))}"

    # 2. Linear / equal rate regime: k3 == k3r (a = 0, Maclaurin / Eq. 100)
    theta_eq = fitter._theta_volmer_tafel(potentials, k1, k1r, 1e-6, 1e-6, bbv, strict=True)
    assert theta_eq is not None
    assert np.all(np.isfinite(theta_eq))
    assert np.all(theta_eq >= 0.0)
    assert np.all(theta_eq <= 1.0)

    # Alias check
    theta_alias = fitter._theta_Tafel_Volmer(potentials, k1, k1r, k3, k3r, bbv, strict=True)
    assert np.allclose(theta, theta_alias)


def test_volmer_tafel_fit_and_decomposition():
    fitter = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0)
    result = fitter.fit_data(
        model_type="Volmer-Tafel",
        fitting_method="least_squares",
        use_global_search=False,
        n_starts=2,
        max_nfev_local=2000,
    )
    assert result.success
    assert np.isfinite(result.chisqr)
    for name in ("k1", "k1r", "k3", "k3r", "bbv"):
        assert name in result.params
        assert result.params[name].value > 0

    theta_h, theta_empty = fitter.compute_theta()
    assert np.all(np.isfinite(theta_h))
    assert np.all(theta_h >= 0.0)
    assert np.all(theta_h <= 1.0)
    assert np.allclose(theta_h + theta_empty, 1.0)

    decomp = fitter.compute_decomposition()
    assert "volmer" in decomp
    assert "tafel" in decomp
    assert "total" in decomp
    assert np.all(np.isfinite(decomp["total"]))
    assert np.allclose(decomp["total"], decomp["volmer"] - decomp["tafel"])


def test_model_type_normalization():
    fitter = hydrogen_fitting(file_path=FIXTURE)
    assert fitter._normalize_model_type("simplified") == "Volmer-Heyrovsky"
    assert fitter._normalize_model_type("Volmer-Heyrovsky") == "Volmer-Heyrovsky"
    assert fitter._normalize_model_type("vh") == "Volmer-Heyrovsky"

    assert fitter._normalize_model_type("Volmer-Tafel") == "Volmer-Tafel"
    assert fitter._normalize_model_type("tafel_volmer") == "Volmer-Tafel"
    assert fitter._normalize_model_type("vt") == "Volmer-Tafel"

    assert fitter._normalize_model_type("full") == "Volmer-Heyrovsky-Tafel"
    assert fitter._normalize_model_type("Volmer-Heyrovsky-Tafel") == "Volmer-Heyrovsky-Tafel"
    assert fitter._normalize_model_type("vht") == "Volmer-Heyrovsky-Tafel"

