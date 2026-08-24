"""Lightweight and robust hydrogen fitting model for web and scientific use.

Implements HER kinetic models (Volmer-Heyrovsky and Volmer-Heyrovsky-Tafel),
coverage calculations (theta_H and empty sites), reaction step decomposition,
moving-window Tafel regression, and comprehensive goodness-of-fit statistics.
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
from lmfit import Model, create_params

F_CONST = 96485.3321  # C / mol (Faraday's constant)
R_CONST = 8.314462618  # J / (mol * K) (Universal gas constant)


def rnd(min_val=1e-20, max_val=1e-2):
    import random
    try:
        min_v = float(min_val) if (min_val is not None and float(min_val) > 0) else 1e-20
        max_v = float(max_val) if (max_val is not None and float(max_val) > 0) else 1e-2
        if min_v >= max_v:
            return min_v
        log_min = np.log10(min_v)
        log_max = np.log10(max_v)
        log_val = random.uniform(log_min, log_max)
        return float(10 ** log_val)
    except Exception:
        exp1 = random.randint(-15, -4)
        significand = round(random.uniform(0.1, 9), 2)
        return float(significand * (10 ** exp1))


class hydrogen_fitting:
    def __init__(self, file_path=None, area_electrode=None, ohmic_drop=0.0, ref_correction=None,
                 ref_potential=None, pH=None, temperature=298.15, gas_constant=8.314462618,
                 bbv_initial=0.5, bbh_initial=0.5, vary_bbv=True, vary_bbh=True,
                 bbv_min=0.0, bbv_max=1.0, bbh_min=0.0, bbh_max=1.0,
                 k1_initial=None, k1_min=1e-20, k1_max=1e-2, vary_k1=True,
                 k1r_initial=None, k1r_min=1e-20, k1r_max=1e-2, vary_k1r=True,
                 k2_initial=None, k2_min=1e-20, k2_max=1e-2, vary_k2=True,
                 k2r_initial=None, k2r_min=1e-20, k2r_max=1e-2, vary_k2r=True,
                 k3_initial=None, k3_min=1e-20, k3_max=1e-2, vary_k3=True,
                 delimiter='auto', current_col=1, potential_col=2, current_units='A'):
        self.file_path = file_path
        self.area_electrode = area_electrode
        self.ohmic_drop = float(ohmic_drop) if ohmic_drop is not None else 0.0
        self.ref_correction = ref_correction
        self.temperature = float(temperature) if temperature is not None else 298.15
        self.gas_constant = float(gas_constant) if gas_constant is not None else R_CONST
        self.ref_potential = ref_potential
        self.pH = pH
        self.bbv_initial = float(bbv_initial) if bbv_initial is not None else 0.5
        self.bbh_initial = float(bbh_initial) if bbh_initial is not None else 0.5
        self.vary_bbv = bool(vary_bbv)
        self.vary_bbh = bool(vary_bbh)

        try:
            self.bbv_min = float(bbv_min)
        except Exception:
            self.bbv_min = 0.0
        try:
            self.bbv_max = float(bbv_max)
        except Exception:
            self.bbv_max = 1.0
        try:
            self.bbh_min = float(bbh_min)
        except Exception:
            self.bbh_min = 0.0
        try:
            self.bbh_max = float(bbh_max)
        except Exception:
            self.bbh_max = 1.0

        self.delimiter = delimiter

        def _safe_float(v, default=None):
            try:
                return float(v) if v is not None and str(v).strip() != '' else default
            except Exception:
                return default

        self.k1_initial = _safe_float(k1_initial, None)
        self.k1_min = _safe_float(k1_min, 1e-20)
        self.k1_max = _safe_float(k1_max, 1e-2)
        self.vary_k1 = bool(vary_k1)

        self.k1r_initial = _safe_float(k1r_initial, None)
        self.k1r_min = _safe_float(k1r_min, 1e-20)
        self.k1r_max = _safe_float(k1r_max, 1e-2)
        self.vary_k1r = bool(vary_k1r)

        self.k2_initial = _safe_float(k2_initial, None)
        self.k2_min = _safe_float(k2_min, 1e-20)
        self.k2_max = _safe_float(k2_max, 1e-2)
        self.vary_k2 = bool(vary_k2)

        self.k2r_initial = _safe_float(k2r_initial, None)
        self.k2r_min = _safe_float(k2r_min, 1e-20)
        self.k2r_max = _safe_float(k2r_max, 1e-2)
        self.vary_k2r = bool(vary_k2r)

        self.k3_initial = _safe_float(k3_initial, None)
        self.k3_min = _safe_float(k3_min, 1e-20)
        self.k3_max = _safe_float(k3_max, 1e-2)
        self.vary_k3 = bool(vary_k3)

        try:
            self.current_col = int(current_col) - 1 if current_col is not None else 0
        except Exception:
            self.current_col = 0
        try:
            self.potential_col = int(potential_col) - 1 if potential_col is not None else 1
        except Exception:
            self.potential_col = 1

        self.current_units = current_units

        # Calculate f1 = F / (R * T)
        try:
            self.f1 = F_CONST / (self.gas_constant * self.temperature)
        except Exception:
            self.f1 = 38.92

        # Reference potential correction vs RHE: E_corr = E_ref + (2.302585 * R * T / F) * pH
        if ref_correction is not None and str(ref_correction).strip() != '':
            try:
                self.ref_correction = float(ref_correction)
            except Exception:
                self.ref_correction = 0.0
        else:
            try:
                slope = 2.302585 * self.gas_constant * self.temperature / F_CONST
            except Exception:
                slope = 0.05916

            ref_p = 0.0
            if self.ref_potential is not None and str(self.ref_potential).strip() != '':
                try:
                    ref_p = float(self.ref_potential)
                except Exception:
                    ref_p = 0.0

            ph_val = 0.0
            if self.pH is not None and str(self.pH).strip() != '':
                try:
                    ph_val = float(self.pH)
                except Exception:
                    ph_val = 0.0

            self.ref_correction = ref_p + (slope * ph_val)

        self.result_model = None
        self.model_type = None
        self._raw = None
        self._parsed = False

        self._load_data()
        self._process_variables()

    def _load_data(self):
        if not (self.file_path and os.path.exists(self.file_path)):
            self._parsed = False
            return

        try:
            sep = None if (self.delimiter == 'auto' or not self.delimiter) else self.delimiter
            df = pd.read_csv(self.file_path, sep=sep, engine='python', comment='#', header=None)
            max_idx = max(int(self.current_col), int(self.potential_col))
            if df.shape[1] > max_idx:
                cols = [int(self.current_col), int(self.potential_col)]
                df2 = df.iloc[:, cols].apply(pd.to_numeric, errors='coerce')
            elif df.shape[1] >= 2:
                df2 = df.iloc[:, :2].apply(pd.to_numeric, errors='coerce')
            else:
                self._parsed = False
                return

            df2 = df2.dropna(how='any')
            arr = df2.values
            if arr.shape[0] < 2:
                self._parsed = False
                return

            self._raw = arr
            self._parsed = True
        except Exception:
            self._parsed = False

    def _process_variables(self):
        if self._raw is None:
            raise ValueError("No data loaded. Check uploaded file path and delimiter selection.")

        dframe = self._raw
        current_raw = np.asarray(dframe[:, 0], dtype=float)
        potential_raw = np.asarray(dframe[:, 1], dtype=float)

        self.current = current_raw
        self.current_density = None
        if self.area_electrode is not None and str(self.area_electrode).strip() != '':
            try:
                area_val = float(self.area_electrode)
                if area_val > 0:
                    self.current_density = current_raw / area_val
            except Exception:
                pass

        # Apply Ohmic drop and Reference potential corrections
        self.potential = potential_raw - (current_raw * float(self.ohmic_drop)) + float(self.ref_correction)

    def fit_data(self, model_type='simplified', fitting_method='powell'):
        f1_val = self.f1
        f_val = F_CONST

        def Theta_VH_func(x, k1, k1r, k2, k2r, bbv, bbh):
            denom = (k1 / np.exp(bbv * f1_val * x) + np.exp((1 - bbv) * f1_val * x) * k1r +
                     k2 / np.exp(bbh * f1_val * x) + np.exp((1 - bbh) * f1_val * x) * k2r)
            num = (k1 / np.exp(bbv * f1_val * x) + np.exp((1 - bbh) * f1_val * x) * k2r)
            with np.errstate(divide='ignore', invalid='ignore'):
                theta = np.where(denom != 0, num / denom, 0.5)
            return theta, 1.0 - theta

        def Theta_Total_func(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh):
            k2r_calc = (k1 * k2) / (k1r + 1e-30)
            k3r_calc = (k3 * (k1 ** 2)) / ((k1r ** 2) + 1e-30)
            A1 = -2.0 * k3 + 2.0 * k3r_calc
            B1 = (-np.exp((-bbv) * f1_val * x) * k1 - np.exp((1.0 - bbv) * f1_val * x) * k1r -
                  k2 / np.exp(bbh * f1_val * x) - np.exp((1.0 - bbh) * f1_val * x) * k2r_calc - 4.0 * k3r_calc)
            C1 = (k1 / np.exp(bbv * f1_val * x) + np.exp((1.0 - bbh) * f1_val * x) * k2r_calc + 2.0 * k3r_calc)

            disc = B1 ** 2 - (4.0 * A1 * C1)
            disc = np.where(disc < 0, 0.0, disc)
            with np.errstate(divide='ignore', invalid='ignore'):
                theta = np.where(np.abs(A1) > 1e-30, (-B1 - np.sqrt(disc)) / (2.0 * A1), -C1 / (B1 + 1e-30))
            theta = np.clip(theta, 0.0, 1.0)
            return theta, 1.0 - theta

        def HER_simplified_wrapper(x, k1, k1r, k2, k2r, bbv, bbh):
            num = 2.0 * (k1 * k2 * (1.0 - np.exp(2.0 * f1_val * x))) * np.exp(-bbh * x * f1_val)
            denom = (k1 * np.exp((bbh - bbv) * f1_val * x) + k2 +
                     np.exp(f1_val * x) * (k1r * np.exp((bbh - bbv) * f1_val * x) + k2r))
            with np.errstate(divide='ignore', invalid='ignore'):
                vtotal = np.where(denom != 0, num / denom, 0.0)
            return -f_val * vtotal

        def Hydrogen_Full_wrapper(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh):
            k2r_calc = (k1 * k2) / (k1r + 1e-30)
            theta, theta2 = Theta_Total_func(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh)
            term1 = (k1 * theta2) / np.exp(bbv * f1_val * x)
            term2 = np.exp((1.0 - bbh) * f1_val * x) * k2r_calc * theta2
            term3 = np.exp((1.0 - bbv) * f1_val * x) * k1r * theta
            term4 = (k2 * theta) / np.exp(bbh * f1_val * x)
            return -f_val * (term1 + term2 + term3 - term4)

        if model_type.lower() == 'simplified':
            self.model_type = 'HER_simplified_fitting'
            model_func = HER_simplified_wrapper
        elif model_type.lower() == 'full':
            self.model_type = 'Hydrogen_Full_Fitting'
            model_func = Hydrogen_Full_wrapper
        else:
            raise ValueError("model_type must be 'simplified' or 'full'")

        HER_model = Model(model_func, independent_vars=['x'])

        if self.model_type == 'HER_simplified_fitting':
            k1_val = self.k1_initial if self.k1_initial is not None else rnd(self.k1_min, self.k1_max)
            k1r_val = self.k1r_initial if self.k1r_initial is not None else rnd(self.k1r_min, self.k1r_max)
            k2_val = self.k2_initial if self.k2_initial is not None else rnd(self.k2_min, self.k2_max)
            k2r_val = self.k2r_initial if self.k2r_initial is not None else rnd(self.k2r_min, self.k2r_max)

            params = create_params(
                k1=dict(value=k1_val, min=self.k1_min, max=self.k1_max, vary=self.vary_k1),
                k1r=dict(value=k1r_val, min=self.k1r_min, max=self.k1r_max, vary=self.vary_k1r),
                k2=dict(value=k2_val, min=self.k2_min, max=self.k2_max, vary=self.vary_k2),
                k2r=dict(value=k2r_val, min=self.k2r_min, max=self.k2r_max, vary=self.vary_k2r),
                bbv=dict(value=self.bbv_initial, min=self.bbv_min, max=self.bbv_max, vary=self.vary_bbv),
                bbh=dict(value=self.bbh_initial, min=self.bbh_min, max=self.bbh_max, vary=self.vary_bbh)
            )
        else:
            k1_val = self.k1_initial if self.k1_initial is not None else rnd(self.k1_min, self.k1_max)
            k1r_val = self.k1r_initial if self.k1r_initial is not None else rnd(self.k1r_min, self.k1r_max)
            k2_val = self.k2_initial if self.k2_initial is not None else rnd(self.k2_min, self.k2_max)
            k3_val = self.k3_initial if self.k3_initial is not None else rnd(self.k3_min, self.k3_max)

            params = create_params(
                k1=dict(value=k1_val, min=self.k1_min, max=self.k1_max, vary=self.vary_k1),
                k1r=dict(value=k1r_val, min=self.k1r_min, max=self.k1r_max, vary=self.vary_k1r),
                k2=dict(value=k2_val, min=self.k2_min, max=self.k2_max, vary=self.vary_k2),
                k2r=dict(expr='(k1*k2)/k1r'),
                k3=dict(value=k3_val, min=self.k3_min, max=self.k3_max, vary=self.vary_k3),
                k3r=dict(expr='(k3*k1**2)/k1r**2'),
                bbv=dict(value=self.bbv_initial, min=self.bbv_min, max=self.bbv_max, vary=self.vary_bbv),
                bbh=dict(value=self.bbh_initial, min=self.bbh_min, max=self.bbh_max, vary=self.vary_bbh)
            )

        params._asteval.symtable['x'] = self.potential
        self.result_model = HER_model.fit(self.current, params, x=self.potential, method=fitting_method, nan_policy='omit')
        return self.result_model

    def get_results(self):
        if self.result_model is None:
            return None
        return {
            'result_model': self.result_model,
            'model_type': self.model_type,
            'parameters': self.result_model.params,
            'fit_report': self.result_model.fit_report()
        }

    def get_params_dict(self):
        if self.result_model is None:
            return None
        out = {}
        for name, p in self.result_model.params.items():
            try:
                val = float(p.value)
                out[name] = val if np.isfinite(val) else None
            except Exception:
                out[name] = getattr(p, 'value', None)
        return out

    def get_stats(self):
        if self.result_model is None:
            return None
        res = self.result_model
        # Compute R-squared
        r_squared = None
        try:
            y_data = np.asarray(self.current)
            y_fit = getattr(res, 'best_fit', None)
            if y_fit is not None:
                ss_res = np.sum((y_data - y_fit) ** 2)
                ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
                if ss_tot > 0:
                    r_val = float(1.0 - (ss_res / (ss_tot + 1e-30)))
                    r_squared = r_val if np.isfinite(r_val) else None
        except Exception:
            pass

        def _clean_stat(v):
            if v is None:
                return None
            try:
                val = float(v)
                return val if np.isfinite(val) else None
            except Exception:
                return None

        def _clean_int(v):
            if v is None:
                return None
            try:
                return int(v)
            except Exception:
                return None

        return {
            'chisqr': _clean_stat(getattr(res, 'chisqr', None)),
            'redchi': _clean_stat(getattr(res, 'redchi', None)),
            'aic': _clean_stat(getattr(res, 'aic', None)),
            'bic': _clean_stat(getattr(res, 'bic', None)),
            'nfree': _clean_int(getattr(res, 'nfree', None)),
            'r_squared': _clean_stat(r_squared),
            'nvarys': _clean_int(getattr(res, 'nvarys', None)),
            'ndata': _clean_int(getattr(res, 'ndata', len(self.current) if hasattr(self, 'current') else 0))
        }

    def compute_theta(self, x=None):
        """Compute coverage (theta_H and empty sites 1-theta_H) using fitted params."""
        if self.result_model is None:
            raise ValueError('No fit available to compute theta')

        params = self.result_model.params
        def _val(n):
            p = params.get(n)
            return float(p.value) if p is not None else 0.0

        f1_val = getattr(self, 'f1', 38.92)
        if x is None:
            x_arr = np.asarray(self.potential)
        else:
            x_arr = np.asarray(x, dtype=float)

        k1 = _val('k1')
        k1r = _val('k1r')
        k2 = _val('k2')
        k2r = _val('k2r')
        bbv = _val('bbv')
        bbh = _val('bbh')

        model_type = getattr(self, 'model_type', '')
        if 'full' in model_type.lower():
            k3 = _val('k3')
            k2r_calc = (k1 * k2) / (k1r + 1e-30)
            k3r_calc = (k3 * (k1 ** 2)) / ((k1r ** 2) + 1e-30)
            A1 = -2.0 * k3 + 2.0 * k3r_calc
            B1 = (-np.exp((-bbv) * f1_val * x_arr) * k1 - np.exp((1.0 - bbv) * f1_val * x_arr) * k1r -
                  k2 / np.exp(bbh * f1_val * x_arr) - np.exp((1.0 - bbh) * f1_val * x_arr) * k2r_calc - 4.0 * k3r_calc)
            C1 = (k1 / np.exp(bbv * f1_val * x_arr) + np.exp((1.0 - bbh) * f1_val * x_arr) * k2r_calc + 2.0 * k3r_calc)
            disc = B1 ** 2 - (4.0 * A1 * C1)
            disc = np.where(disc < 0, 0.0, disc)
            with np.errstate(divide='ignore', invalid='ignore'):
                theta = np.where(np.abs(A1) > 1e-30, (-B1 - np.sqrt(disc)) / (2.0 * A1), -C1 / (B1 + 1e-30))
            theta = np.clip(theta, 0.0, 1.0)
            return theta, 1.0 - theta
        else:
            denom = (k1 / np.exp(bbv * f1_val * x_arr) + np.exp((1.0 - bbv) * f1_val * x_arr) * k1r +
                     k2 / np.exp(bbh * f1_val * x_arr) + np.exp((1.0 - bbh) * f1_val * x_arr) * k2r)
            num = (k1 / np.exp(bbv * f1_val * x_arr) + np.exp((1.0 - bbh) * f1_val * x_arr) * k2r)
            with np.errstate(divide='ignore', invalid='ignore'):
                theta = np.where(denom != 0, num / denom, 0.5)
            theta = np.clip(theta, 0.0, 1.0)
            return theta, 1.0 - theta

    def compute_decomposition(self, x=None):
        """Compute Volmer and Heyrovsky partial reaction contributions."""
        if self.result_model is None:
            raise ValueError('No fit available to compute decomposition')

        params = self.result_model.params
        def _val(n):
            p = params.get(n)
            return float(p.value) if p is not None else 0.0

        f1_val = getattr(self, 'f1', 38.92)
        f_val = F_CONST
        if x is None:
            x_arr = np.asarray(self.potential)
        else:
            x_arr = np.asarray(x, dtype=float)

        k1 = _val('k1')
        k1r = _val('k1r')
        k2 = _val('k2')
        k2r = _val('k2r')
        bbv = _val('bbv')
        bbh = _val('bbh')

        theta, theta2 = self.compute_theta(x=x_arr)

        volmer_rate = (k1 * theta2) / np.exp(f1_val * bbv * x_arr) - np.exp(f1_val * (1.0 - bbv) * x_arr) * k1r * theta
        heyrovsky_rate = -np.exp(f1_val * (1.0 - bbh) * x_arr) * k2r * theta2 + (k2 * theta) / np.exp(bbh * f1_val * x_arr)

        # Convert to current (A)
        i_volmer = -f_val * volmer_rate
        i_heyrovsky = -f_val * heyrovsky_rate
        i_total = i_volmer + i_heyrovsky

        return {
            'x': x_arr,
            'volmer': i_volmer,
            'heyrovsky': i_heyrovsky,
            'total': i_total
        }

    def compute_tafel_slope(self, x=None, use_fitted=True, window_size=10, method='rolling'):
        """Compute Tafel slope in mV/decade.

        Implements rolling-window linear regression dV/d(log10|I|) matching hy2.py,
        or numerical gradient when method='gradient'.
        Returns (x_pot, slope_mV_per_dec).
        """
        if x is None:
            x_arr = np.asarray(self.potential)
        else:
            x_arr = np.asarray(x, dtype=float)

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

        # Instead of cutting by current value, skip the first 55 points to match hy2.py
        if len(x_arr) > 55 and len(I) > 55:
            x_arr = x_arr[55:]
            I = I[55:]

        if method == 'rolling':
            n = len(x_arr)
            win = max(3, min(int(window_size), n))
            v1 = []
            for i in range(n - win + 1):
                sub_p = x_arr[i : i + win]
                sub_c = np.abs(I[i : i + win]) + 1e-30
                log_c = np.log10(sub_c)
                try:
                    res = stats.linregress(log_c, sub_p)
                    xm = np.mean(sub_p)
                    slope_val = np.abs(res.slope)
                    v1.append([xm, slope_val])
                except Exception:
                    pass
            if len(v1) > 0:
                return np.asarray(v1)

        # Fallback to gradient method
        eps = 1e-30
        logI = np.log10(np.abs(I) + eps)
        dx = np.gradient(x_arr)
        dlogI = np.gradient(logI)
        with np.errstate(divide='ignore', invalid='ignore'):
            slope_V_per_dec = np.where(np.abs(dlogI) > 1e-30, dx / dlogI, 0.0)
        slope_mV_per_dec = np.nan_to_num(np.abs(slope_V_per_dec * 1000.0), nan=0.0, posinf=0.0, neginf=0.0)
        return x_arr, slope_mV_per_dec
