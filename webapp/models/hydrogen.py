"""Hydrogen-evolution-reaction fitting model.

Implements simplified Volmer-Heyrovsky and full Volmer-Heyrovsky-Tafel
steady-state models, coverage, reaction decomposition, moving-window Tafel
analysis, and robust kinetic fitting in log-rate-constant space.
"""

from math import log
from math import log10
import os
import random

import warnings

import numpy as np
import pandas as pd
from scipy import stats
from lmfit import Model, Parameters

warnings.filterwarnings(
    "ignore", 
    message="Using UFloat objects with std_dev==0 may give unexpected results."
)

F_CONST = 96485.3321  # C mol^-1
R_CONST = 8.314462618  # J mol^-1 K^-1


class InvalidModelState(ValueError):
    """Raised when a parameter set leads to an invalid model prediction."""


def rnd(min_val=1e-20, max_val=1e-2):
    """Sample a positive value uniformly in log10-space."""
    try:
        min_v = float(min_val)
        max_v = float(max_val)
        min_v = min_v if min_v > 0 else 1e-20
        max_v = max_v if max_v > 0 else 1e-2
        if min_v >= max_v:
            return min_v
        return float(10.0 ** random.uniform(np.log10(min_v), np.log10(max_v)))
    except Exception:
        return float((10.0 ** random.randint(-15, -4)) * random.uniform(0.1, 9.0))


class HydrogenFitting:
    """Hydrogen Evolution Reaction (HER) kinetic fitting and analysis engine.

    Implements steady-state Volmer-Heyrovsky, Volmer-Tafel and Volmer-Heyrovsky-Tafel models,
    reaction decomposition, moving-window Tafel slope analysis, and robust kinetic optimization.
    """
    def __init__(
        self,
        file_path=None,
        area_electrode=None,
        ohmic_drop=0.0,# Resistence of electrolyte between the reference and work electrode
        ref_correction=None,
        ref_potential=None,# Reference electrode potential
        pH=None,# Electrolyte pH
        temperature=298.15,
        gas_constant=R_CONST,
        potential_min=None,
        potential_max=None,
        bbv_initial=0.5, 
        bbh_initial=0.5, 
        vary_bbv=False,
        vary_bbh=False,
        bbv_min=0.0,
        bbv_max=1.0,
        bbh_min=0.0,
        bbh_max=1.0,
        k1_initial=None,
        k1_min=1e-20,
        k1_max=1e-2,
        vary_k1=True,
        k1r_initial=None,
        k1r_min=1e-20,
        k1r_max=1e-2,
        vary_k1r=True,
        k2_initial=None,
        k2_min=1e-20,
        k2_max=1e-2,
        vary_k2=True,
        k2r_initial=None,
        k2r_min=1e-20,
        k2r_max=1e-2,
        vary_k2r=True,
        k3_initial=None,
        k3_min=1e-20,
        k3_max=1e-2,
        vary_k3=True,
        k3r_initial=None,
        k3r_min=1e-20,
        k3r_max=1e-2,
        vary_k3r=True,
        delimiter="auto",
        current_col=2,
        potential_col=1,
        current_units="A",
    ):
        self.file_path = file_path
        self.area_electrode = area_electrode
        self.ohmic_drop = self._safe_float(ohmic_drop, 0.0)
        self.ref_potential = ref_potential
        self.pH = pH
        self.temperature = self._safe_float(temperature, 298.15)
        self.gas_constant = self._safe_float(gas_constant, R_CONST)
        self.potential_min = self._safe_float(potential_min, None)
        self.potential_max = self._safe_float(potential_max, None)
        self.current_units = current_units
        self.delimiter = delimiter

        self.bbv_initial = self._safe_float(bbv_initial, 0.5)
        self.bbh_initial = self._safe_float(bbh_initial, 0.5)
        self.vary_bbv = bool(vary_bbv)
        self.vary_bbh = bool(vary_bbh)
        self.bbv_min = self._safe_float(bbv_min, 0.0)
        self.bbv_max = self._safe_float(bbv_max, 1.0)
        self.bbh_min = self._safe_float(bbh_min, 0.0)
        self.bbh_max = self._safe_float(bbh_max, 1.0)

        self.k1_initial = self._safe_float(k1_initial, None)
        self.k1_min = self._positive_bound(k1_min, 1e-20)
        self.k1_max = self._positive_bound(k1_max, 1e-2)
        self.vary_k1 = bool(vary_k1)

        self.k1r_initial = self._safe_float(k1r_initial, None)
        self.k1r_min = self._positive_bound(k1r_min, 1e-20)
        self.k1r_max = self._positive_bound(k1r_max, 1e-2)
        self.vary_k1r = bool(vary_k1r)

        self.k2_initial = self._safe_float(k2_initial, None)
        self.k2_min = self._positive_bound(k2_min, 1e-20)
        self.k2_max = self._positive_bound(k2_max, 1e-2)
        self.vary_k2 = bool(vary_k2)

        self.k2r_initial = self._safe_float(k2r_initial, None)
        self.k2r_min = self._positive_bound(k2r_min, 1e-20)
        self.k2r_max = self._positive_bound(k2r_max, 1e-2)
        self.vary_k2r = bool(vary_k2r)

        self.k3_initial = self._safe_float(k3_initial, None)
        self.k3_min = self._positive_bound(k3_min, 1e-20)
        self.k3_max = self._positive_bound(k3_max, 1e-2)
        self.vary_k3 = bool(vary_k3)

        self.k3r_initial = self._safe_float(k3r_initial, None)
        self.k3r_min = self._positive_bound(k3r_min, 1e-20)
        self.k3r_max = self._positive_bound(k3r_max, 1e-2)
        self.vary_k3r = bool(vary_k3r)

        try:
            self.current_col = int(current_col) - 1
        except Exception:
            self.current_col = 0
        try:
            self.potential_col = int(potential_col) - 1
        except Exception:
            self.potential_col = 1

        self.f1 = F_CONST / (self.gas_constant * self.temperature)
        self.ref_correction = self._reference_correction(ref_correction)

        self.result_model = None
        self.model_type = None
        self._raw = None
        self._parsed = False
        self._fit_metadata = {}

        self._load_data()
        self._process_variables()

    @staticmethod
    def _safe_float(value, default=None):
        try:
            if value is None or str(value).strip() == "":
                return default
            val = float(value)
            return val if np.isfinite(val) else default
        except Exception:
            return default

    @staticmethod
    def _positive_bound(value, default, floor=1e-30):
        try:
            val = float(value)
            return max(val, floor) if np.isfinite(val) else default
        except Exception:
            return default

    def _reference_correction(self, ref_correction):
        supplied = self._safe_float(ref_correction, None)
        if supplied is not None:
            return supplied
        ref_p = self._safe_float(self.ref_potential, 0.0)
        ph_val = self._safe_float(self.pH, 0.0)
        slope = 2.302585 * self.gas_constant * self.temperature / F_CONST
        return ref_p + slope * ph_val

    def _load_data(self):
        if not (self.file_path and os.path.exists(self.file_path)):
            self._parsed = False
            return
        try:
            sep = None if self.delimiter in (None, "", "auto") else self.delimiter
            df = pd.read_csv(self.file_path, sep=sep, engine="python", comment="#", header=None)
            max_idx = max(self.current_col, self.potential_col)
            if df.shape[1] > max_idx:
                data = df.iloc[:, [self.current_col, self.potential_col]]
            elif df.shape[1] >= 2:
                data = df.iloc[:, :2]
            else:
                self._parsed = False
                return
            data = data.apply(pd.to_numeric, errors="coerce").dropna(how="any")
            if len(data) < 2:
                self._parsed = False
                return
            self._raw = data.to_numpy(dtype=float)
            self._parsed = True
        except Exception:
            self._parsed = False

    def _process_variables(self):
        if self._raw is None:
            raise ValueError("No data loaded. Check the file path, columns, and delimiter.")
        current_raw = np.asarray(self._raw[:, 0], dtype=float)
        potential_raw = np.asarray(self._raw[:, 1], dtype=float)
        
        area = self._safe_float(self.area_electrode, 1.0)
        if area <= 0:
            area = 1.0
        self.area_electrode = area
        
        self.current_density = current_raw / area
        self.current = self.current_density
        self.potential = potential_raw - current_raw * self.ohmic_drop + self.ref_correction
        
        p_min = self.potential_min
        p_max = self.potential_max
        if p_min is not None and p_max is not None and p_min > p_max:
            p_min, p_max = p_max, p_min
            
        mask = np.ones_like(self.potential, dtype=bool)
        if p_min is not None:
            mask &= (self.potential >= p_min)
        if p_max is not None:
            mask &= (self.potential <= p_max)
            
        if not np.all(mask):
            self.potential = self.potential[mask]
            self.current_density = self.current_density[mask]
            self.current = self.current[mask]

    @staticmethod
    def _safe_exp(z):
        return np.exp(np.clip(z, -700.0, 700.0))

    @staticmethod
    def _safe_log_bounds(lower, upper, floor=1e-30):
        lo = max(float(lower), floor)
        hi = max(float(upper), lo * (1.0 + 1e-12))
        return float(np.log(lo)), float(np.log(hi))

    @staticmethod
    def _clip_initial_rate(value, lower, upper):
        lo = max(float(lower), 1e-30)
        hi = max(float(upper), lo * (1.0 + 1e-12))
        if value is None or not np.isfinite(value) or value <= 0:
            value = rnd(lo, hi)
        return float(np.clip(value, lo, hi))

    def _add_log_rate(self, params, name, initial, lower, upper, vary=True):
        lo, hi = self._safe_log_bounds(lower, upper)
        k0 = self._clip_initial_rate(initial, lower, upper)
        params.add(f"log_{name}", value=np.log(k0), min=lo, max=hi, vary=bool(vary))
        params.add(name, expr=f"exp(log_{name})")

    @staticmethod
    def _normalize_model_type(model_type):
        if not model_type:
            return "Volmer-Heyrovsky"
        norm = str(model_type).strip().lower().replace("_", "-").replace(" ", "-")
        if norm in {"volmer-tafel", "tafel-volmer", "vt", "tv", "her-volmer-tafel-fitting"}:
            return "Volmer-Tafel"
        if norm in {"volmer-heyrovsky-irreversible", "vhi", "vh-irreversible", "her-volmer-heyrovsky-irreversible-fitting"}:
            return "Volmer-Heyrovsky-Irreversible"
        if norm in {"full", "vht", "volmer-heyrovsky-tafel", "hydrogen-full-fitting", "her-volmer-heyrovsky-tafel-fitting"}:
            return "Volmer-Heyrovsky-Tafel"
        if norm in {"simplified", "vh", "volmer-heyrovsky", "her-simplified-fitting", "her-volmer-heyrovsky-fitting"}:
            return "Volmer-Heyrovsky"
        raise ValueError(
            f"Unknown model_type '{model_type}'. Supported: 'Volmer-Heyrovsky', 'Volmer-Heyrovsky-Irreversible', 'Volmer-Tafel', 'Volmer-Heyrovsky-Tafel'."
        )

    def _make_log_params(self, model_type):
        params = Parameters()
        norm_model = self._normalize_model_type(model_type)

        self._add_log_rate(params, "k1", self.k1_initial, self.k1_min, self.k1_max, self.vary_k1)
        if norm_model != "Volmer-Heyrovsky-Irreversible":
            self._add_log_rate(params, "k1r", self.k1r_initial, self.k1r_min, self.k1r_max, self.vary_k1r)

        if norm_model == "Volmer-Heyrovsky":
            self._add_log_rate(params, "k2", self.k2_initial, self.k2_min, self.k2_max, self.vary_k2)
            self._add_log_rate(params, "k2r", self.k2r_initial, self.k2r_min, self.k2r_max, self.vary_k2r)
        elif norm_model == "Volmer-Tafel":
            self._add_log_rate(params, "k3", self.k3_initial, self.k3_min, self.k3_max, self.vary_k3)
            self._add_log_rate(params, "k3r", self.k3r_initial, self.k3r_min, self.k3r_max, self.vary_k3r)
        elif norm_model == "Volmer-Heyrovsky-Irreversible":
            self._add_log_rate(params, "k2", self.k2_initial, self.k2_min, self.k2_max, self.vary_k2)
        elif norm_model == "Volmer-Heyrovsky-Tafel":
            self._add_log_rate(params, "k2", self.k2_initial, self.k2_min, self.k2_max, self.vary_k2)
            self._add_log_rate(params, "k3", self.k3_initial, self.k3_min, self.k3_max, self.vary_k3)
            params.add("k2r", self.k2r_min, self.k2r_max, expr="(k1*k2)/k1r")
            params.add("k3r", self.k3r_min, self.k3r_max, expr="(k3*k1**2)/(k1r**2)")
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        params.add(
            "bbv",
            value=float(np.clip(self.bbv_initial, self.bbv_min, self.bbv_max)),
            min=self.bbv_min,
            max=self.bbv_max,
            vary=self.vary_bbv,
        )
        if norm_model in {"Volmer-Heyrovsky", "Volmer-Heyrovsky-Tafel", "Volmer-Heyrovsky-Irreversible"}:
            params.add(
                "bbh",
                value=float(np.clip(self.bbh_initial, self.bbh_min, self.bbh_max)),
                min=self.bbh_min,
                max=self.bbh_max,
                vary=self.vary_bbh,
            )
        return params

    def _fit_weights(self, relative_error=0.03, current_noise=0.0):
        current = np.asarray(self.current, dtype=float)
        if relative_error is None or float(relative_error) < 0:
            raise ValueError("relative_error must be non-negative.")
        relative_error = float(relative_error)
        if current_noise is None:
            finite = np.abs(current[np.isfinite(current)])
            scale = np.max(finite) if finite.size else 1.0
            current_noise = max(1e-12, 1e-6 * scale)
        current_noise = max(float(current_noise), 1e-30)
        sigma = np.maximum(relative_error * np.abs(current), current_noise)
        return 1.0 / sigma

    def _invalid_prediction(self, x, scale):
        return np.full_like(np.asarray(x, dtype=float), 1e6 * max(float(scale), 1e-12), dtype=float)
"""
    Description of the kinetic parameters:
    k1 and k1r are the foward and backward rate constants of the Volmer step (electrochemical adsorption step), respectively;
    k2 and k2r are the foward and backward rate constants of the Heyrovsky step (electrochemical desorption step), respectively;
    k3 and k3r are the foward and backward rate constant of the Tafel step (chemical desorption step), respectively;
    bbv and bbh are the transfer coeficients of the Volmer and Heyrovsky steps, respectively.
"""
    # Hydrogen coverage - Volmer-Heyrovsky mechanism    
    def _theta_volmer_heyrovsky(self, x, k1, k1r, k2, k2r, bbv, bbh, strict=True):
         """Compute surface coverage for Volmer-Heyrovsky mechanism using Lasia Eq. (68)-(69)."""
        x = np.asarray(x, dtype=float)
        u = self.f1 * x
        denom = (
            k1 * self._safe_exp(-bbv * u)
            + k1r * self._safe_exp((1.0 - bbv) * u)
            + k2 * self._safe_exp(-bbh * u)
            + k2r * self._safe_exp((1.0 - bbh) * u)
        )
        num = (
            k1 * self._safe_exp(-bbv * u)
            + k2r * self._safe_exp((1.0 - bbh) * u)
        )
        if np.any(~np.isfinite(denom)) or np.any(np.abs(denom) < 1e-28):
            if strict:
                return None
            return np.full_like(x, np.nan, dtype=float)
        theta = num / denom
        if np.any(~np.isfinite(theta)):
            return None if strict else np.full_like(x, np.nan, dtype=float)
        if strict and (np.any(theta < -1e-8) or np.any(theta > 1.0 + 1e-8)):
            return None
        return np.clip(theta, 0.0, 1.0)
    
    # Hydrogen coverage - Volmer-Tafel mechanism
    def _theta_volmer_tafel(self, x, k1, k1r, k3, k3r, bbv, strict=True):
        """Compute surface coverage for Volmer-Tafel mechanism using Lasia Eq. (97)-(100)."""
        x = np.asarray(x, dtype=float)
        u = self.f1 * x
        if min(k1, k1r, k3, k3r) <= 0:
            return None if strict else np.full_like(x, np.nan, dtype=float)

        k1_fwd = k1 * self._safe_exp(-bbv * u)
        k1_rev = k1r * self._safe_exp((1.0 - bbv) * u)

        # Lasia Eq. (97):
        # theta_H^2 (2 k_3 - 2 k_{-3}) + theta_H (4 k_{-3} + \vec{k}_1 + \overleftarrow{k}_{-1}) + (-\vec{k}_1 - 2 k_{-3}) = 0
        # a theta^2 + b theta + c = 0
        a = 2.0 * k3 - 2.0 * k3r
        b = 4.0 * k3r + k1_fwd + k1_rev
        c = -k1_fwd - 2.0 * k3r

        if np.any(b <= 0):
            return None if strict else np.full_like(x, np.nan, dtype=float)

        theta = np.empty_like(x, dtype=float)
        if abs(a) < 1e-20:
            # When a = 0 (k3 == k3r), b*theta + c = 0 -> theta = -c/b (Lasia Eq. 100)
            theta = -c / b
        else:
            arg = 4.0 * a * c / (b ** 2)
            # Use Maclaurin expansion (Lasia Eq. 99-100) when |arg| < 1e-5 to prevent catastrophic cancellation:
            # 1 - sqrt(1 - x) = x/2 + x^2/8 + ...
            # -b/(2a) * [1 - sqrt(1 - x)] = -c/b * [1 + ac/b^2 + 2*(ac/b^2)^2]
            small_mask = np.abs(arg) < 1e-5
            if np.any(small_mask):
                term = a * c[small_mask] / (b[small_mask] ** 2)
                theta[small_mask] = (-c[small_mask] / b[small_mask]) * (1.0 + term + 2.0 * (term ** 2))
            if np.any(~small_mask):
                disc_term = 1.0 - arg[~small_mask]
                disc_term = np.maximum(disc_term, 0.0)
                theta[~small_mask] = (-b[~small_mask] / (2.0 * a)) * (1.0 - np.sqrt(disc_term))

        if np.any(~np.isfinite(theta)):
            return None if strict else np.full_like(x, np.nan, dtype=float)
        if strict and (np.any(theta < -1e-8) or np.any(theta > 1.0 + 1e-8)):
            return None
        return np.clip(theta, 0.0, 1.0)

    # Alias for Tafel-Volmer
    _theta_Tafel_Volmer = _theta_volmer_tafel
    
    # Hydrogen coverage - Volmer-Heyrovsky-Tafel mechanism
    def _theta_volmer_heyrovsky_tafel(self, x, k1, k1r, k2, k3, bbv, bbh, strict=True):
         """Compute surface coverage for Volmer-Tafel mechanism using Lasia Eq. (115)."""
        x = np.asarray(x, dtype=float)
        u = self.f1 * x
        if min(k1, k1r, k2, k3) <= 0:
            return None

        k2r = (k1 * k2) / k1r
        k3r = (k3 * k1**2) / (k1r**2)
        a = -2.0 * k3 + 2.0 * k3r
        b = (
            -self._safe_exp(-bbv * u) * k1
            -self._safe_exp((1.0 - bbv) * u) * k1r
            -k2 * self._safe_exp(-bbh * u)
            -self._safe_exp((1.0 - bbh) * u) * k2r
            -4.0 * k3r
        )
        c = (
            k1 * self._safe_exp(-bbv * u)
            + self._safe_exp((1.0 - bbh) * u) * k2r
            + 2.0 * k3r
        )
        disc = b**2 - 4.0 * a * c
        if np.any(~np.isfinite(disc)) or np.any(disc < -1e-12):
            return None if strict else np.full_like(x, np.nan, dtype=float)
        disc = np.maximum(disc, 0.0)

        theta = np.empty_like(x, dtype=float)
        small_a = np.abs(a) < 1e-20
        if np.any(~small_a):
            theta[~small_a] = (-b[~small_a] - np.sqrt(disc[~small_a])) / (2.0 * a)
        if np.any(small_a):
            if np.any(np.abs(b[small_a]) < 1e-28):
                return None if strict else np.full_like(x, np.nan, dtype=float)
            theta[small_a] = -c[small_a] / b[small_a]

        if np.any(~np.isfinite(theta)):
            return None if strict else np.full_like(x, np.nan, dtype=float)
        if strict and (np.any(theta < -1e-8) or np.any(theta > 1.0 + 1e-8)):
            return None
        return np.clip(theta, 0.0, 1.0)
        
    # HER current density - Volmer-Heyrovsky mechanism
    def _volmer_heyrovsky_current_density(self, x, k1, k1r, k2, k2r, bbv, bbh, invalid_scale):
        x = np.asarray(x, dtype=float)
        theta = self._theta_volmer_heyrovsky(x, k1, k1r, k2, k2r, bbv, bbh, strict=True)
        if theta is None:
            return self._invalid_prediction(x, invalid_scale)

        u = self.f1 * x
        theta_empty = 1.0 - theta
        
        term1 = k1 * theta_empty * self._safe_exp(-bbv * u)          # v1
        term2 = k1r * theta * self._safe_exp((1.0 - bbv) * u)        # v-1
        term3 = k2 * theta * self._safe_exp(-bbh * u)                # v2
        term4 = k2r * theta_empty * self._safe_exp((1.0 - bbh) * u)  # v-2
        
        out = -F_CONST * (term1 - term2 + term3 - term4)
        return out if np.all(np.isfinite(out)) else self._invalid_prediction(x, invalid_scale)

    # HER current density - Volmer-Heyrovsky Irreversible
    def _volmer_heyrovsky_irreversible_current_density(self, x, k1, k2, bbv, bbh, invalid_scale):
        x = np.asarray(x, dtype=float)
        u = self.f1 * x
        e_shift = self._safe_exp((bbh - bbv) * u)
        numerator = 2.0 * k1 * k2 * self._safe_exp(-bbv * u)
        denominator = k1 * e_shift + k2
        if (
            np.any(~np.isfinite(numerator))
            or np.any(~np.isfinite(denominator))
            or np.any(np.abs(denominator) < 1e-28)
        ):
            return self._invalid_prediction(x, invalid_scale)
        out = -F_CONST * numerator / denominator
        return out if np.all(np.isfinite(out)) else self._invalid_prediction(x, invalid_scale)
    
    # HER current density - Volmer-Heyrovsky-Tafel mechanism
    def _volmer_heyrovsky_tafel_current_density(self, x, k1, k1r, k2, k3, bbv, bbh, invalid_scale):
        x = np.asarray(x, dtype=float)
        theta = self._theta_volmer_heyrovsky_tafel(x, k1, k1r, k2, k3, bbv, bbh, strict=True)
        if theta is None:
            return self._invalid_prediction(x, invalid_scale)

        u = self.f1 * x
        theta_empty = 1.0 - theta
        k2r = (k1 * k2) / k1r
        term1 = k1 * theta_empty * self._safe_exp(-bbv * u)
        term2 = self._safe_exp((1.0 - bbh) * u) * k2r * theta_empty
        term3 = self._safe_exp((1.0 - bbv) * u) * k1r * theta
        term4 = k2 * theta * self._safe_exp(-bbh * u)
        out = -F_CONST * (term1 - term3 + term4 - term2)
        return out if np.all(np.isfinite(out)) else self._invalid_prediction(x, invalid_scale)
    
    # HER current density - Volmer-Tafel mechanism
    def _volmer_tafel_current(self, x, k1, k1r, k3, k3r, bbv, invalid_scale):
        x = np.asarray(x, dtype=float)
        theta = self._theta_volmer_tafel(x, k1, k1r, k3, k3r, bbv, strict=True)
        if theta is None:
            return self._invalid_prediction(x, invalid_scale)

        u = self.f1 * x
        theta_empty = 1.0 - theta
        volmer_rate = (
            k1 * theta_empty * self._safe_exp(-bbv * u)
            - self._safe_exp((1.0 - bbv) * u) * k1r * theta
        )
        tafel_rate = (
            k3 * (theta**2) - k3r * theta_empty**2
        )
        current_volmer_tafel = (
            -F_CONST * (2.0 * tafel_rate)
        )
        return current_volmer_tafel if np.all(np.isfinite(current_volmer_tafel)) else self._invalid_prediction(x, invalid_scale)

    _current_volmer_tafel = _volmer_tafel_current
    _tafel_volmer_current = _volmer_tafel_current

    def fit_data(
        self,
        model_type="Volmer-Heyrovsky",
        fitting_method="least_squares",
        global_method="differential_evolution",
        use_global_search=True,
        n_starts=1,
        relative_error=0.03,
        current_noise=0.0,
        max_nfev_global=30000,
        max_nfev_local=20000,
        robust_loss="soft_l1",
        robust_f_scale=1.0,
    ):
        """Fit HER current-potential data.

        Rate constants are fitted in log-space. ``differential_evolution`` is
        used only to locate promising basins; bounded ``least_squares`` gives
        the final local solution. Set ``use_global_search=False`` and increase
        ``n_starts`` for faster random multi-start local fitting.
        """
        norm_model = self._normalize_model_type(model_type)

        x_data = np.asarray(self.potential, dtype=float)
        y_data = np.asarray(self.current, dtype=float)
        if x_data.ndim != 1 or y_data.ndim != 1 or x_data.size != y_data.size:
            raise ValueError("Potential and current must be one-dimensional arrays of equal length.")
        if x_data.size < 3 or not np.all(np.isfinite(x_data)) or not np.all(np.isfinite(y_data)):
            raise ValueError("At least three finite potential/current observations are required.")

        invalid_scale = max(np.max(np.abs(y_data)), 1e-12)
        weights = self._fit_weights(relative_error=relative_error, current_noise=current_noise)

        if norm_model == "Volmer-Heyrovsky":
            self.model_type = "HER_Volmer_Heyrovsky_Fitting"

            def model_func(x, k1, k1r, k2, k2r, bbv, bbh):
                return self._volmer_heyrovsky_current_density(x, k1, k1r, k2, k2r, bbv, bbh, invalid_scale)

        elif norm_model == "Volmer-Heyrovsky-Irreversible":
            self.model_type = "HER_Volmer_Heyrovsky_Irreversible_Fitting"

            def model_func(x, k1, k2, bbv, bbh):
                return self._volmer_heyrovsky_irreversible_current_density(x, k1, k2, bbv, bbh, invalid_scale)

        elif norm_model == "Volmer-Tafel":
            self.model_type = "HER_Volmer_Tafel_Fitting"

            def model_func(x, k1, k1r, k3, k3r, bbv):
                return self._volmer_tafel_current(x, k1, k1r, k3, k3r, bbv, invalid_scale)

        else:
            self.model_type = "Hydrogen_Full_Fitting"

            def model_func(x, k1, k1r, k2, k3, bbv, bbh):
                return self._volmer_heyrovsky_tafel_current_density(x, k1, k1r, k2, k3, bbv, bbh, invalid_scale)

        her_model = Model(model_func, independent_vars=["x"])
        candidates = []
        n_starts = max(1, int(n_starts))

        for _ in range(n_starts):
            initial_params = self._make_log_params(norm_model)
            local_start = initial_params

            if use_global_search:
                try:
                    global_result = her_model.fit(
                        y_data,
                        initial_params,
                        x=x_data,
                        weights=weights,
                        method=global_method,
                        nan_policy="raise",
                        max_nfev=int(max_nfev_global),
                    )
                    local_start = global_result.params
                except Exception:
                    # Retain the log-random start and permit the local fit to try it.
                    local_start = initial_params

            fit_kwargs = {}
            if fitting_method == "least_squares":
                fit_kwargs = {
                    "fit_kws": {
                        "x_scale": "jac",
                        "loss": robust_loss,
                        "f_scale": float(robust_f_scale),
                    }
                }

            try:
                local_result = her_model.fit(
                    y_data,
                    local_start,
                    x=x_data,
                    weights=weights,
                    method=fitting_method,
                    nan_policy="raise",
                    max_nfev=int(max_nfev_local),
                    **fit_kwargs,
                )
                if np.isfinite(local_result.chisqr):
                    candidates.append(local_result)
            except Exception:
                continue

        if not candidates:
            raise RuntimeError(
                "All fitting attempts failed. Check units, parameter ranges, "
                "mechanism validity, and whether the experimental interval is "
                "compatible with the steady-state HER model."
            )

        self.result_model = min(candidates, key=lambda result: result.chisqr)
        self._fit_metadata = {
            "model_type": norm_model,
            "fitting_method": fitting_method,
            "global_method": global_method if use_global_search else None,
            "use_global_search": bool(use_global_search),
            "n_starts": n_starts,
            "relative_error": float(relative_error),
            "current_noise": current_noise,
            "robust_loss": robust_loss if fitting_method == "least_squares" else None,
        }
        return self.result_model

    def get_results(self):
        if self.result_model is None:
            return None
        return {
            "result_model": self.result_model,
            "model_type": self.model_type,
            "parameters": self.result_model.params,
            "fit_report": self.result_model.fit_report(),
            "fit_metadata": dict(self._fit_metadata),
        }

    def get_params_dict(self, include_internal=False):
        if self.result_model is None:
            return None
        out = {}
        for name, par in self.result_model.params.items():
            if not include_internal and name.startswith("log_"):
                continue
            try:
                out[name] = float(par.value) if np.isfinite(par.value) else None
            except Exception:
                out[name] = None
        return out

    def get_stats(self):
        if self.result_model is None:
            return None
        result = self.result_model
        y_data = np.asarray(self.current, dtype=float)
        y_fit = np.asarray(result.best_fit, dtype=float)
        ss_res = np.sum((y_data - y_fit) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = None if ss_tot <= 0 else float(1.0 - ss_res / ss_tot)

        def clean_float(value):
            try:
                value = float(value)
                return value if np.isfinite(value) else None
            except Exception:
                return None

        def clean_int(value):
            try:
                return int(value)
            except Exception:
                return None

        return {
            "chisqr": clean_float(getattr(result, "chisqr", None)),
            "redchi": clean_float(getattr(result, "redchi", None)),
            "aic": clean_float(getattr(result, "aic", None)),
            "bic": clean_float(getattr(result, "bic", None)),
            "nfree": clean_int(getattr(result, "nfree", None)),
            "r_squared": clean_float(r_squared),
            "nvarys": clean_int(getattr(result, "nvarys", None)),
            "ndata": clean_int(getattr(result, "ndata", len(self.current))),
        }

    def compute_theta(self, x=None):
        """Compute fitted theta_H and empty-site coverage."""
        if self.result_model is None:
            raise ValueError("No fit is available. Run fit_data() first.")
        params = self.result_model.params
        x_arr = np.asarray(self.potential if x is None else x, dtype=float)

        def value(name, default=0.0):
            return float(params[name].value) if name in params else default

        k1 = value("k1")
        k1r = value("k1r")
        bbv = value("bbv", 0.5)

        norm = self._normalize_model_type(self.model_type)
        if norm == "Volmer-Tafel":
            theta = self._theta_volmer_tafel(x_arr, k1, k1r, value("k3"), value("k3r"), bbv, strict=False)
        elif norm == "Volmer-Heyrovsky-Tafel":
            theta = self._theta_volmer_heyrovsky_tafel(x_arr, k1, k1r, value("k2"), value("k3"), bbv, value("bbh", 0.5), strict=False)
        else:
            theta = self._theta_volmer_heyrovsky(x_arr, k1, k1r, value("k2"), value("k2r"), bbv, value("bbh", 0.5), strict=False)

        if theta is None or np.any(~np.isfinite(theta)):
            raise InvalidModelState("Could not calculate a physical fitted coverage.")
        return theta, 1.0 - theta

    def compute_decomposition(self, x=None):
        """Compute Volmer, Heyrovsky, or Tafel partial-current contributions."""
        if self.result_model is None:
            raise ValueError("No fit is available. Run fit_data() first.")
        params = self.result_model.params
        x_arr = np.asarray(self.potential if x is None else x, dtype=float)

        def value(name, default=0.0):
            return float(params[name].value) if name in params else default

        k1 = value("k1")
        k1r = value("k1r")
        bbv = value("bbv", 0.5)
        theta, theta_empty = self.compute_theta(x_arr)
        u = self.f1 * x_arr

        volmer_rate = (
            k1 * theta_empty * self._safe_exp(-bbv * u)
            - self._safe_exp((1.0 - bbv) * u) * k1r * theta
        )
        norm = self._normalize_model_type(self.model_type)
        if norm == "Volmer-Tafel":
            k3 = value("k3")
            k3r = value("k3r")
            tafel_rate = k3 * (theta ** 2) - k3r * (theta_empty ** 2)
            rate_volmer = np.log10(np.abs(volmer_rate) + 1e-30)
            rate_tafel = np.log10(np.abs(tafel_rate) + 1e-30)
            total = np.log10(np.abs(2 * tafel_rate) + 1e-30)
            return {
                "x": x_arr,
                "volmer": rate_volmer,
                "tafel": rate_tafel,
                "total": total,
            }
        elif norm == "Volmer-Heyrovsky-Tafel":
            k2 = value("k2")
            k2r = value("k2r")
            k3 = value("k3")
            k3r = value("k3r")
            bbh = value("bbh", 0.5)
            heyrovsky_rate = (
                k2 * theta * self._safe_exp(-bbh * u)
                - self._safe_exp((1.0 - bbh) * u) * k2r * theta_empty
            )
            tafel_rate = k3 * (theta ** 2) - k3r * (theta_empty ** 2)
            rate_volmer = np.log10(np.abs(volmer_rate) + 1e-30)
            rate_heyrovsky = np.log10(np.abs(heyrovsky_rate) + 1e-30)
            rate_tafel = np.log10(np.abs(tafel_rate) + 1e-30)
            total = np.log10(np.abs(volmer_rate + heyrovsky_rate) + 1e-30)
            return {
                "x": x_arr,
                "volmer": rate_volmer,
                "heyrovsky": rate_heyrovsky,
                "tafel": rate_tafel,
                "total": total,
            }
        else:
            k2 = value("k2")
            k2r = value("k2r")
            bbh = value("bbh", 0.5)
            heyrovsky_rate = (
                k2 * theta * self._safe_exp(-bbh * u)
                - self._safe_exp((1.0 - bbh) * u) * k2r * theta_empty
            )
            rate_volmer = np.log10(np.abs(volmer_rate) + 1e-30)
            rate_heyrovsky = np.log10(np.abs(heyrovsky_rate) + 1e-30)
            total = np.log10(np.abs(volmer_rate + heyrovsky_rate) + 1e-30)
            return {
                "x": x_arr,
                "volmer": rate_volmer,
                "heyrovsky": rate_heyrovsky,
                "total": total,
            }

    def compute_tafel_slope(self, x=None, use_fitted=True, window_size=10, method="rolling", skip_initial=0):
        """Compute local Tafel slope in mV decade^-1."""
        x_arr = np.asarray(self.potential if x is None else x, dtype=float)
        if use_fitted and self.result_model is not None:
            current = np.asarray(self.result_model.eval(x=x_arr), dtype=float)
        else:
            current = np.asarray(self.current, dtype=float)

        if x_arr.size != current.size:
            raise ValueError("Potential and current arrays must have the same length.")
            
        skip = int(skip_initial)
        if skip > 0 and x_arr.size > skip:
            x_arr = x_arr[skip:]
            current = current[skip:]

        if method == "rolling":
            n = x_arr.size
            win = max(3, min(int(window_size), n))
            output = []
            for index in range(n - win + 1):
                potential_window = x_arr[index:index + win]
                current_window = np.abs(current[index:index + win]) + 1e-30
                try:
                    regression = stats.linregress(np.log10(current_window), potential_window)
                    output.append([np.mean(potential_window), abs(regression.slope) * 1000.0])
                except Exception:
                    continue
            if output:
                return np.asarray(output, dtype=float)

        log_current = np.log10(np.abs(current) + 1e-30)
        dpotential = np.gradient(x_arr)
        dlog_current = np.gradient(log_current)
        with np.errstate(divide="ignore", invalid="ignore"):
            slope = np.where(np.abs(dlog_current) > 1e-30, dpotential / dlog_current, np.nan)
        return x_arr, np.abs(np.nan_to_num(slope * 1000.0, nan=0.0, posinf=0.0, neginf=0.0))


# Backward compatibility alias for legacy scripts and imports
hydrogen_fitting = HydrogenFitting
