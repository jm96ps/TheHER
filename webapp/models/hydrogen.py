"""Lightweight hydrogen fitting model for web use.

This module reads a user-supplied data file (no synthetic fallback),
converts current units, computes current density, applies ohmic and
reference corrections, and exposes fitting routines.
"""
import os
import numpy as np
import pandas as pd
from lmfit import Model, create_params

F = 96485.3


def rnd():
    import random
    exp1 = random.randint(-15, -4)
    significand = round(random.uniform(0.1, 9), 2)
    return significand * 10 ** exp1


class hydrogen_fitting:
    def __init__(self, file_path=None, area_electrode=None, ohmic_drop=0.0, ref_correction=None,
                 ref_potential=None, pH=None, temperature=None, gas_constant=None,
                 bbv_initial=0.5, bbh_initial=0.5, vary_bbv=True, vary_bbh=True,
                 delimiter='auto', current_col=1, potential_col=2, current_units='A'):
        self.file_path = file_path
        self.area_electrode = area_electrode
        self.ohmic_drop = float(ohmic_drop) if ohmic_drop is not None else 0.0
        self.ref_correction = ref_correction
        self.temperature = temperature
        self.gas_constant = gas_constant
        self.ref_potential = ref_potential
        self.pH = pH
        self.bbv_initial = bbv_initial
        self.bbh_initial = bbh_initial
        self.vary_bbv = vary_bbv
        self.vary_bbh = vary_bbh
        self.delimiter = delimiter
        # user-provided column mapping (1-based indices in the UI), convert to 0-based
        try:
            self.current_col = int(current_col) - 1 if current_col is not None else 0
        except Exception:
            self.current_col = 0
        try:
            self.potential_col = int(potential_col) - 1 if potential_col is not None else 1
        except Exception:
            self.potential_col = 1
        # ensure columns are integers (defensive: form values may be strings)
        try:
            self.current_col = int(self.current_col)
        except Exception:
            self.current_col = 0
        try:
            self.potential_col = int(self.potential_col)
        except Exception:
            self.potential_col = 1
        self.current_units = current_units

        self.f1 = 38.92

        # Determine reference correction (priority: explicit ref_correction > ref_potential+pH)
        if ref_correction is not None:
            try:
                self.ref_correction = float(ref_correction)
            except Exception:
                self.ref_correction = 0.0
        else:
            try:
                R = float(self.gas_constant) if self.gas_constant is not None else 8.314
                T = float(self.temperature) if self.temperature is not None else 298.15
                slope = 2.303 * R * T / F
            except Exception:
                slope = 0.05916

            if (self.ref_potential is not None) and (self.pH is not None):
                try:
                    self.ref_correction = float(self.ref_potential) + slope * float(self.pH)
                except Exception:
                    self.ref_correction = 0.0
            else:
                self.ref_correction = 0.0

        self.result_model = None
        self.model_type = None

        self._raw = None
        self._parsed = False

        self._load_data()
        self._process_variables()

    def _load_data(self):
        # Require a user-supplied file; no synthetic data generation.
        if not (self.file_path and os.path.exists(self.file_path)):
            self._parsed = False
            return

        try:
            sep = None if (self.delimiter == 'auto' or not self.delimiter) else self.delimiter
            df = pd.read_csv(self.file_path, sep=sep, engine='python', comment='#', header=None)
            # select columns if available
            # guard against non-integer column indices from form input
            try:
                max_idx = max(int(self.current_col), int(self.potential_col))
            except Exception:
                max_idx = 1
            if df.shape[1] > max_idx:
                cols = [int(self.current_col), int(self.potential_col)]
                df2 = df.iloc[:, cols].apply(pd.to_numeric, errors='coerce')
            elif df.shape[1] >= 2:
                df2 = df.iloc[:, :2].apply(pd.to_numeric, errors='coerce')
            else:
                self._parsed = False
                return

            # drop rows with any NaN in the selected columns
            df2 = df2.dropna(how='any')
            arr = df2.values
            if arr.shape[0] < 2:
                self._parsed = False
                return

            self._raw = arr
            self._parsed = True
            return
        except Exception:
            self._parsed = False
            return

    def _process_variables(self):
        if self._raw is None:
            raise ValueError("No data loaded. Check uploaded file path and delimiter selection.")

        dframe = self._raw

        # extract raw columns according to user mapping
        current_raw = np.asarray(dframe[:, 0], dtype=float)
        potential_raw = np.asarray(dframe[:, 1], dtype=float)

        # The model now requires the user to supply current in Amperes (A).
        # We will NOT divide by area for the data used in fitting.
        # Area, if provided, is only used to compute current density for plotting.
        current_A = current_raw

        # store raw current (A) for fitting
        self.current = current_A

        # compute current density only for plotting (do not modify data used for fitting)
        self.current_density = None
        if self.area_electrode is not None and self.area_electrode != '':
            try:
                area_val = float(self.area_electrode)
                self.current_density = current_A / area_val
            except Exception:
                raise ValueError('Electrode area must be numeric')

        # apply ohmic drop correction using raw current (A) * ohmic_drop
        # Note: area is intentionally NOT applied here so fitting uses raw current values only.
        self.potential = potential_raw - (current_A * float(self.ohmic_drop)) + float(self.ref_correction)

    def fit_data(self, model_type='simplified', fitting_method='powell'):
        f1_val = self.f1

        def Theta_Total_local(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh):
            # calculate coverage theta for full model (vectorized)
            k2r_calc = (k1 * k2) / k1r
            k3r_calc = (k3 * k1 ** 2) / (k1r ** 2)
            A1 = -2 * k3 + 2 * k3r_calc
            B1 = (-np.e ** ((-bbv) * f1_val * x)) * k1 - np.e ** ((1 - bbv) * f1_val * x) * k1r - k2 / np.e ** (bbh * f1_val * x) - np.e ** ((1 - bbh) * f1_val * x) * k2r_calc - 4 * k3r_calc
            C1 = k1 / np.e ** (bbv * f1_val * x) + np.e ** ((1 - bbh) * f1_val * x) * k2r_calc + 2 * k3r_calc
            # guard against negative discriminant
            disc = B1 ** 2 - (4 * A1 * C1)
            disc = np.where(disc < 0, 0.0, disc)
            theta = (-B1 - np.sqrt(disc)) / (2 * A1)
            return theta

        def HER_simplified_wrapper(x, k1, k1r, k2, k2r, bbv, bbh):
            vtotal = 2 * (((k1 * k2 * (1 - np.e ** (2 * f1_val * x))) * np.e ** (-bbh * x * f1_val)) /
                          (k1 * np.e ** ((bbh - bbv) * f1_val * x) + k2 + np.e ** (f1_val * x) *
                           (k1r * np.e ** ((bbh - bbv) * f1_val * x) + k2r)))
            return -F * vtotal

        def Hydrogen_Full_wrapper(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh):
            # full model current using Theta_Total_local
            k2r_calc = (k1 * k2) / k1r
            k3r_calc = (k3 * k1 ** 2) / (k1r ** 2)
            theta = Theta_Total_local(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh)
            term1 = (k1 * (1 - theta)) / np.e ** (bbv * f1_val * x)
            term2 = np.e ** ((1 - bbh) * f1_val * x) * k2r_calc * (1 - theta)
            term3 = np.e ** ((1 - bbv) * f1_val * x) * k1r * theta
            term4 = (k2 * theta) / np.e ** (bbh * f1_val * x)
            return -F * (term1 + term2 + term3 - term4)

        # choose model
        if model_type.lower() == 'simplified':
            self.model_type = 'HER_simplified_fitting'
            model_func = HER_simplified_wrapper
        elif model_type.lower() == 'full':
            self.model_type = 'Hydrogen_Full_Fitting'
            model_func = Hydrogen_Full_wrapper
        else:
            raise ValueError("model_type must be 'simplified' or 'full'")

        HER_model = Model(model_func, independent_vars=['x'])
        # build parameter set depending on model
        if self.model_type == 'HER_simplified_fitting':
            rand_params = np.array([rnd() for _ in range(6)])
            params = create_params(
                k1=dict(value=rand_params[0], max=1e-2, min=1e-20),
                k1r=dict(value=rand_params[1], max=1e-2, min=1e-20),
                k2=dict(value=rand_params[2], max=1e-2, min=1e-20),
                k2r=dict(value=rand_params[3], max=1e-2, min=1e-20),
                bbv=dict(value=self.bbv_initial, min=0, max=1, vary=self.vary_bbv),
                bbh=dict(value=self.bbh_initial, min=0, max=1, vary=self.vary_bbh)
            )
        else:
            # full model params
            rand_params = np.array([rnd() for _ in range(8)])
            params = create_params(
                k1=dict(value=rand_params[0], max=1e-2, min=1e-20),
                k1r=dict(value=rand_params[1], max=1e-2, min=1e-20),
                k2=dict(value=rand_params[2], max=1e-2, min=1e-20),
                k2r=dict(expr='(k1*k2)/k1r'),
                k3=dict(value=rand_params[3], max=1e-2, min=1e-20),
                k3r=dict(expr='(k3*k1**2)/k1r**2'),
                bbv=dict(value=self.bbv_initial, min=0, max=1, vary=self.vary_bbv),
                bbh=dict(value=self.bbh_initial, min=0, max=1, vary=self.vary_bbh)
            )

        params._asteval.symtable['x'] = self.potential

        # perform fitting (weight omitted for simplicity)
        self.result_model = HER_model.fit(self.current, params, x=self.potential, method=fitting_method, nan_policy='omit')

        return self.result_model

    def get_results(self):
        if self.result_model is None:
            return None
        return {'result_model': self.result_model, 'model_type': self.model_type, 'parameters': self.result_model.params}

    def get_params_dict(self):
        """Return fitted parameter values as a plain dict of floats/strings."""
        if self.result_model is None:
            return None
        out = {}
        for name, p in self.result_model.params.items():
            try:
                out[name] = float(p.value)
            except Exception:
                out[name] = getattr(p, 'value', None)
        return out

    def get_stats(self):
        """Return basic fit statistics from the lmfit Result object."""
        if self.result_model is None:
            return None
        res = self.result_model
        return {
            'chisqr': getattr(res, 'chisqr', None),
            'redchi': getattr(res, 'redchi', None),
            'aic': getattr(res, 'aic', None),
            'bic': getattr(res, 'bic', None),
            'nfree': getattr(res, 'nfree', None),
        }

    def compute_theta(self, x=None):
        """Compute coverage (theta) for the full Hydrogen model using fitted params.

        Returns theta array for the provided x (potential) or the fitted `self.potential`.
        """
        if self.result_model is None:
            raise ValueError('No fit available to compute theta')
        model_type = getattr(self, 'model_type', '')
        if 'full' not in model_type.lower():
            raise ValueError('Theta available only for full model fits')

        params = self.result_model.params
        def _val(n):
            p = params.get(n)
            return float(p.value) if p is not None else 0.0

        k1 = _val('k1')
        k1r = _val('k1r')
        k2 = _val('k2')
        k3 = _val('k3')
        bbv = _val('bbv')
        bbh = _val('bbh')

        f1_val = getattr(self, 'f1', 38.92)
        if x is None:
            x = np.asarray(self.potential)
        else:
            x = np.asarray(x, dtype=float)

        k2r_calc = (k1 * k2) / k1r if k1r != 0 else 0.0
        k3r_calc = (k3 * k1 ** 2) / (k1r ** 2) if k1r != 0 else 0.0
        A1 = -2 * k3 + 2 * k3r_calc
        B1 = (-np.e ** ((-bbv) * f1_val * x)) * k1 - np.e ** ((1 - bbv) * f1_val * x) * k1r - k2 / np.e ** (bbh * f1_val * x) - np.e ** ((1 - bbh) * f1_val * x) * k2r_calc - 4 * k3r_calc
        C1 = k1 / np.e ** (bbv * f1_val * x) + np.e ** ((1 - bbh) * f1_val * x) * k2r_calc + 2 * k3r_calc
        disc = B1 ** 2 - (4 * A1 * C1)
        disc = np.where(disc < 0, 0.0, disc)
        denom = 2 * A1
        denom = np.where(denom == 0, np.nan, denom)
        theta = (-B1 - np.sqrt(disc)) / denom
        return theta

    def compute_tafel_slope(self, x=None, use_fitted=True):
        """Compute local Tafel slope in mV/decade.

        If `use_fitted` is True and a fitted curve is available it will use fitted current,
        otherwise it uses `self.current`.
        Returns (x, slope_mV_per_dec).
        """
        if x is None:
            x = np.asarray(self.potential)
        else:
            x = np.asarray(x, dtype=float)

        I = None
        if use_fitted and self.result_model is not None:
            try:
                fitted = getattr(self.result_model, 'best_fit', None)
                if fitted is None:
                    fitted = self.result_model.eval(x=self.potential)
                I = np.asarray(fitted)
            except Exception:
                I = None

        if I is None:
            I = np.asarray(self.current)

        eps = 1e-30
        logI = np.log10(np.abs(I) + eps)
        dx = np.gradient(x)
        dlogI = np.gradient(logI)
        with np.errstate(divide='ignore', invalid='ignore'):
            slope_V_per_dec = np.where(dlogI == 0, np.nan, dx / dlogI)
        slope_mV_per_dec = slope_V_per_dec * 1000.0
        return x, slope_mV_per_dec
