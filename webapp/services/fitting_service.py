import os
import io
import re
import zipfile
import traceback
import numpy as np
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

from ..models.hydrogen import hydrogen_fitting


def secure_filename(filename):
    """Sanitize filename to prevent directory traversal attacks."""
    filename = os.path.basename(filename)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    if filename.startswith('.'):
        filename = '_' + filename
    return filename or 'unnamed'


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_uploaded_file(file_storage):
    if not file_storage:
        return None
    filename = getattr(file_storage, 'filename', None) or getattr(file_storage, 'name', None) or ''
    filename = secure_filename(filename)
    if not filename:
        return None
    path = os.path.join(UPLOAD_DIR, filename)

    try:
        save_fn = getattr(file_storage, 'save', None)
        if callable(save_fn):
            try:
                file_storage.save(path)
                return path
            except TypeError:
                with open(path, 'wb') as f:
                    save_fn(f)
                return path
    except Exception:
        pass

    try:
        if hasattr(file_storage, 'chunks'):
            with open(path, 'wb') as destination:
                for chunk in file_storage.chunks():
                    destination.write(chunk)
            return path
        data = None
        if hasattr(file_storage, 'read'):
            data = file_storage.read()
        elif isinstance(file_storage, (bytes, bytearray)):
            data = file_storage
        if data is not None:
            if isinstance(data, str):
                data = data.encode('utf-8')
            with open(path, 'wb') as f:
                f.write(data)
            return path
    except Exception:
        pass

    return None


from pathlib import Path

def as_bool(value, default=False):
    """Parse checkbox/form values without treating 'false' as True."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def as_float(value, default=None):
    """Return a finite float, or the supplied default."""
    try:
        if value is None or str(value).strip() == "":
            return default
        parsed = float(value)
        return parsed
    except (TypeError, ValueError):
        return default


def as_int(value, default=None, minimum=None, maximum=None):
    """Parse an integer and optionally keep it in an allowed range."""
    try:
        if value is None or str(value).strip() == "":
            return default
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def _request_value(form, name, default=None):
    """Work with Django QueryDict, a normal dict, or a test fixture dict."""
    try:
        return form.get(name, default)
    except AttributeError:
        return default


def _first_float(form, keys, default=None):
    """Return the first key in form that yields a valid float."""
    for k in keys:
        val = _request_value(form, k)
        f = as_float(val)
        if f is not None:
            return f
    return default


def build_fitter_from_request(form, files=None):
    """Build `hydrogen_fitting` from validated request values."""
    uploaded = files.get('datafile') if files is not None else None
    saved_path = _save_uploaded_file(uploaded) if uploaded else None

    # Allow direct file_path or sample preset
    if not saved_path:
        fp = _request_value(form, 'file_path')
        if fp:
            fp = os.path.abspath(fp)
            if os.path.exists(fp):
                saved_path = fp

    if not saved_path:
        # Default fallback to example file in workspace if nothing uploaded
        pt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Pt_example.txt')
        if os.path.exists(pt_path):
            saved_path = os.path.abspath(pt_path)

    resolved_file_path = saved_path
    if resolved_file_path is not None:
        resolved_file_path = str(Path(resolved_file_path))

    params = {
        "file_path": resolved_file_path,
        "area_electrode": as_float(_request_value(form, "area_electrode"), None),
        "ohmic_drop": as_float(_request_value(form, "ohmic_drop"), 0.0),
        "ref_correction": as_float(_request_value(form, "ref_correction"), None),
        "ref_potential": as_float(_request_value(form, "ref_potential"), None),
        "pH": as_float(_request_value(form, "pH"), None),
        "temperature": as_float(_request_value(form, "temperature"), 298.15),
        "gas_constant": as_float(_request_value(form, "gas_constant"), 8.314462618),
        "potential_min": as_float(_request_value(form, "potential_min"), None),
        "potential_max": as_float(_request_value(form, "potential_max"), None),
        "bbv_initial": _first_float(form, ["bbv_initial", "bbv"], 0.5),
        "bbh_initial": _first_float(form, ["bbh_initial", "bbh"], 0.5),
        "vary_bbv": as_bool(_request_value(form, "vary_bbv"), False),
        "vary_bbh": as_bool(_request_value(form, "vary_bbh"), False),
        "bbv_min": as_float(_request_value(form, "bbv_min"), 0.0),
        "bbv_max": as_float(_request_value(form, "bbv_max"), 1.0),
        "bbh_min": as_float(_request_value(form, "bbh_min"), 0.0),
        "bbh_max": as_float(_request_value(form, "bbh_max"), 1.0),
        "k1_initial": _first_float(form, ["k1_initial", "k1_init"], None),
        "k1_min": as_float(_request_value(form, "k1_min"), 1e-20),
        "k1_max": as_float(_request_value(form, "k1_max"), 1e-2),
        "vary_k1": as_bool(_request_value(form, "vary_k1"), True),
        "k1r_initial": _first_float(form, ["k1r_initial", "k1r_init"], None),
        "k1r_min": as_float(_request_value(form, "k1r_min"), 1e-20),
        "k1r_max": as_float(_request_value(form, "k1r_max"), 1e-2),
        "vary_k1r": as_bool(_request_value(form, "vary_k1r"), True),
        "k2_initial": _first_float(form, ["k2_initial", "k2_init"], None),
        "k2_min": as_float(_request_value(form, "k2_min"), 1e-20),
        "k2_max": as_float(_request_value(form, "k2_max"), 1e-2),
        "vary_k2": as_bool(_request_value(form, "vary_k2"), True),
        "k2r_initial": _first_float(form, ["k2r_initial", "k2r_init"], None),
        "k2r_min": as_float(_request_value(form, "k2r_min"), 1e-20),
        "k2r_max": as_float(_request_value(form, "k2r_max"), 1e-2),
        "vary_k2r": as_bool(_request_value(form, "vary_k2r"), True),
        "k3_initial": _first_float(form, ["k3_initial", "k3_init"], None),
        "k3_min": as_float(_request_value(form, "k3_min"), 1e-20),
        "k3_max": as_float(_request_value(form, "k3_max"), 1e-2),
        "vary_k3": as_bool(_request_value(form, "vary_k3"), True),
        "k3r_initial": _first_float(form, ["k3r_initial", "k3r_init"], None),
        "k3r_min": as_float(_request_value(form, "k3r_min"), 1e-20),
        "k3r_max": as_float(_request_value(form, "k3r_max"), 1e-2),
        "vary_k3r": as_bool(_request_value(form, "vary_k3r"), True),
        "delimiter": _request_value(form, "delimiter", "auto"),
        "current_col": as_int(_request_value(form, "current_col"), 1, minimum=1),
        "potential_col": as_int(_request_value(form, "potential_col"), 2, minimum=1),
        "current_units": _request_value(form, "current_units", "A"),
    }
    
    try:
        d = params.get('delimiter')
        if isinstance(d, str):
            if d in ('\\t', r'\t', '\t'):
                params['delimiter'] = '\t'
            elif d in ('space', ' '):
                params['delimiter'] = ' '
            elif d in ('comma', ','):
                params['delimiter'] = ','
            elif d in ('semicolon', ';'):
                params['delimiter'] = ';'
    except Exception:
        pass

    return hydrogen_fitting(**params)


def fit_options_from_request(form):
    """Return fit controls separately from physical model parameters."""
    method = str(_request_value(form, "fitting_method", "least_squares")).strip()
    if method not in {"least_squares", "leastsq", "powell", "nelder"}:
        method = "least_squares"

    global_method = str(
        _request_value(form, "global_method", "differential_evolution")
    ).strip()
    if global_method not in {"differential_evolution", "powell", "nelder"}:
        global_method = "differential_evolution"

    robust_loss = str(_request_value(form, "robust_loss", "soft_l1")).strip()
    if robust_loss not in {"linear", "soft_l1", "huber", "cauchy", "arctan"}:
        robust_loss = "soft_l1"

    raw_model = str(_request_value(form, "model_type", "Volmer-Heyrovsky")).strip()
    norm = raw_model.lower().replace(" ", "_").replace("-", "_")
    if norm in {"simplified", "volmer_heyrovsky", "vh"}:
        model_type = "Volmer-Heyrovsky"
    elif norm in {"volmer_tafel", "tafel_volmer", "vt", "tv"}:
        model_type = "Volmer-Tafel"
    elif norm in {"full", "volmer_heyrovsky_tafel", "vht"}:
        model_type = "Volmer-Heyrovsky-Tafel"
    else:
        model_type = "Volmer-Heyrovsky"

    return {
        "model_type": model_type,
        "fitting_method": method,
        "use_global_search": as_bool(_request_value(form, "use_global_search"), False),
        "global_method": global_method,
        "n_starts": as_int(_request_value(form, "n_starts"), 10, minimum=1, maximum=100),
        "relative_error": as_float(_request_value(form, "relative_error"), 0.03),
        "current_noise": as_float(_request_value(form, "current_noise"), None),
        "max_nfev_global": as_int(_request_value(form, "max_nfev_global"), 30000, minimum=100),
        "max_nfev_local": as_int(_request_value(form, "max_nfev_local"), 20000, minimum=100),
        "robust_loss": robust_loss,
        "robust_f_scale": as_float(_request_value(form, "robust_f_scale"), 1.0),
    }


def sanitize_for_json(obj):
    """Recursively convert NaN, Infinity, -Infinity, and numpy scalars to standard JSON-compliant types."""
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, str):
        return obj
    if isinstance(obj, np.ndarray):
        return [sanitize_for_json(x) for x in obj.tolist()]
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(x) for x in obj]
    return obj


def run_fit(form, files=None):
    try:
        fitter = build_fitter_from_request(form, files)
        fitter.fit_data(**fit_options_from_request(form))
        res = fitter.get_results() or {}
    except Exception as e:
        tb = traceback.format_exc()
        return {'success': False, 'error': str(e), 'traceback': tb}

    try:
        plot_b64 = base64.b64encode(_get_plot_bytes(fitter)).decode('utf-8')
        theta_b64 = base64.b64encode(_get_theta_bytes(fitter)).decode('utf-8')
        win = int(form.get('tafel_window', 10))
        skip = int(form.get('tafel_skip', 0))
        tafel_b64 = base64.b64encode(_get_tafel_bytes(fitter, win, skip)).decode('utf-8')
    except Exception as e:
        plot_b64 = theta_b64 = tafel_b64 = None


    params = {}
    params_details = {}
    internal_params = {}
    internal_parameters_details = {}

    if 'parameters' in res and res['parameters'] is not None:
        raw_params = res['parameters']
        parsed_all = {}
        for name, p in raw_params.items():
            try:
                raw_val = float(p.value) if p.value is not None else None
                val = raw_val if (raw_val is not None and np.isfinite(raw_val)) else None

                raw_stderr = float(p.stderr) if (getattr(p, 'stderr', None) is not None) else None
                stderr_val = raw_stderr if (raw_stderr is not None and np.isfinite(raw_stderr)) else None

                raw_min = float(p.min) if (getattr(p, 'min', None) is not None) else None
                min_val = raw_min if (raw_min is not None and np.isfinite(raw_min)) else None

                raw_max = float(p.max) if (getattr(p, 'max', None) is not None) else None
                max_val = raw_max if (raw_max is not None and np.isfinite(raw_max)) else None

                parsed_all[name] = {
                    'p': p,
                    'value': val,
                    'stderr': stderr_val,
                    'min': min_val,
                    'max': max_val,
                    'vary': bool(getattr(p, 'vary', True)),
                    'expr': getattr(p, 'expr', None),
                }
            except Exception:
                parsed_all[name] = {
                    'p': p,
                    'value': str(getattr(p, 'value', None)),
                    'stderr': None,
                    'min': None,
                    'max': None,
                    'vary': bool(getattr(p, 'vary', True)),
                    'expr': getattr(p, 'expr', None),
                }

        # Separate internal log-space variables and physical rate constants
        for name, item in parsed_all.items():
            if name.startswith('log_'):
                internal_params[name] = item['value']
                internal_parameters_details[name] = {
                    'value': item['value'],
                    'stderr': item['stderr'],
                    'min': item['min'],
                    'max': item['max'],
                    'vary': item['vary'],
                    'expr': item['expr'],
                    'status': 'Fitted' if item['vary'] else 'Fixed',
                }
            else:
                log_name = f"log_{name}"
                is_log_mapped = log_name in parsed_all

                if is_log_mapped:
                    log_item = parsed_all[log_name]
                    effective_vary = bool(log_item['vary'])
                    status = 'Fitted' if effective_vary else 'Fixed'

                    phys_min = item['min']
                    if phys_min is None and log_item['min'] is not None:
                        try:
                            phys_min = float(np.exp(log_item['min']))
                        except Exception:
                            phys_min = None

                    phys_max = item['max']
                    if phys_max is None and log_item['max'] is not None:
                        try:
                            phys_max = float(np.exp(log_item['max']))
                        except Exception:
                            phys_max = None

                    params[name] = item['value']
                    params_details[name] = {
                        'value': item['value'],
                        'stderr': item['stderr'],
                        'vary': effective_vary,
                        'status': status,
                        'min': phys_min,
                        'max': phys_max,
                        'expr': None,
                    }
                else:
                    if item['expr']:
                        status = 'Derived'
                        effective_vary = False
                    elif item['vary']:
                        status = 'Fitted'
                        effective_vary = True
                    else:
                        status = 'Fixed'
                        effective_vary = False

                    params[name] = item['value']
                    params_details[name] = {
                        'value': item['value'],
                        'stderr': item['stderr'],
                        'vary': effective_vary,
                        'status': status,
                        'min': item['min'],
                        'max': item['max'],
                        'expr': item['expr'],
                    }

        # Sort physical parameters according to standard kinetic order
        CANONICAL_ORDER = ['k1', 'k1r', 'k2', 'k2r', 'k3', 'k3r', 'bbv', 'bbh']
        ordered_params = {}
        ordered_details = {}
        for k in CANONICAL_ORDER:
            if k in params:
                ordered_params[k] = params[k]
                ordered_details[k] = params_details[k]
        for k in params:
            if k not in ordered_params:
                ordered_params[k] = params[k]
                ordered_details[k] = params_details[k]
        params = ordered_params
        params_details = ordered_details

    stats_dict = fitter.get_stats() or {}

    return sanitize_for_json({
        'success': True,
        'model_type': res.get('model_type'),
        'parameters': params,
        'parameters_details': params_details,
        'internal_parameters': internal_params,
        'internal_parameters_details': internal_parameters_details,
        'stats': stats_dict,
        'fit_report': res.get('fit_report', ''),
        'n_points': int(len(fitter.potential)) if hasattr(fitter, 'potential') else 0,
        'file_path': fitter.file_path if hasattr(fitter, 'file_path') else None,
        'plots': {
            'polarization': plot_b64,
            'theta': theta_b64,
            'tafel': tafel_b64
        }
    })


def _get_plot_bytes(fitter):
    result_model = getattr(fitter, 'result_model', None)
    try:
        fitted = getattr(result_model, 'best_fit', None)
        if fitted is None and result_model is not None:
            fitted = result_model.eval(x=fitter.potential)
    except Exception:
        fitted = None

    # Eliminate any correction by the area: plot raw Current in mA directly
    scale = 1000.0
    area_val = getattr(fitter, 'area_electrode', 1.0)
    ylabel = r'Current Density ($mA \cdot cm^{-2}$)' if area_val != 1.0 else r'Current ($mA$)'

    y_data = fitter.current * scale
    y_fit = fitted * scale if fitted is not None else None

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

    # Color-blind safe (Deuteranopia/Protanopia: Okabe-Ito Cobalt Blue & Vermilion)
    ax.plot(fitter.potential, y_data, 'o', color='#0072B2', markersize=4, alpha=0.7, label='Experimental Data')
    if y_fit is not None:
        ax.plot(fitter.potential, y_fit, '-', color='#D55E00', linewidth=2.2, label='HER Kinetic Fit')

    ax.set_xlabel('Potential vs RHE (V)', fontsize=11, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
    ax.set_title('HER Polarization Curve (LSV Fit)', fontsize=12, fontweight='bold', pad=10)
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_plot(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(**fit_options_from_request(form))
    return _get_plot_bytes(fitter)


def _get_theta_bytes(fitter):
    theta_H, theta_empty = fitter.compute_theta()
    x = np.asarray(fitter.potential)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

    # Color-blind safe: Blue vs Amber with solid vs dashed line styling
    ax.plot(x, theta_H, '-', color='#0072B2', linewidth=2.2, label=r'$\theta_H$')
    ax.plot(x, theta_empty, '--', color='#E69F00', linewidth=2.2, label=r'$1 - \theta_H$')

    ax.set_xlabel('Potential vs RHE (V)', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Surface Coverage ($\theta$)', fontsize=11, fontweight='bold')
    ax.set_title(r'Hydrogen Surface Coverage ($\theta_H$ vs Potential)', fontsize=12, fontweight='bold', pad=10)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_theta_plot(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(**fit_options_from_request(form))
    return _get_theta_bytes(fitter)


def _get_tafel_bytes(fitter, win=10, skip=0):
    result_model = getattr(fitter, 'result_model', None)
    try:
        fitted = getattr(result_model, 'best_fit', None)
        if fitted is None and result_model is not None:
            fitted = result_model.eval(x=fitter.potential)
    except Exception:
        fitted = None

    tafel_data = fitter.compute_tafel_slope(x=fitter.potential, use_fitted=False, window_size=win, method='rolling', skip_initial=skip)
    if isinstance(tafel_data, tuple):
        x_data, slope_data = tafel_data
    else:
        x_data, slope_data = (tafel_data[:, 0], tafel_data[:, 1]) if tafel_data is not None and len(tafel_data) > 0 else ([], [])

    tafel_fit = fitter.compute_tafel_slope(x=fitter.potential, use_fitted=True, window_size=win, method='rolling', skip_initial=skip) if fitted is not None else None
    if isinstance(tafel_fit, tuple):
        x_fit, slope_fit = tafel_fit
    else:
        x_fit, slope_fit = (tafel_fit[:, 0], tafel_fit[:, 1]) if tafel_fit is not None and len(tafel_fit) > 0 else (None, None)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

    # Color-blind safe: Blue points and Vermilion fit line
    if x_data is not None and len(x_data) > 0:
        ax.plot(x_data, slope_data, 'o', color='#0072B2', markersize=4, alpha=0.7, label='Experimental Tafel')
    if x_fit is not None and len(x_fit) > 0:
        ax.plot(x_fit, slope_fit, '-', color='#D55E00', linewidth=2.2, label='Fit Tafel Slope')

    ax.set_xlabel('Potential vs RHE (V)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Tafel Slope (mV / decade)', fontsize=11, fontweight='bold')
    ax.set_title(f'Tafel Slope vs Potential (Moving Window = {win} pts)', fontsize=12, fontweight='bold', pad=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_tafel_plot(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(**fit_options_from_request(form))
    win = int(form.get('tafel_window', 10))
    skip = int(form.get('tafel_skip', 0))
    return _get_tafel_bytes(fitter, win=win, skip=skip)





def render_plot_data(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(**fit_options_from_request(form))
    result_model = getattr(fitter, 'result_model', None)
    try:
        fitted = getattr(result_model, 'best_fit', None)
        if fitted is None and result_model is not None:
            fitted = result_model.eval(x=fitter.potential)
    except Exception:
        fitted = None

    x = np.asarray(fitter.potential)
    y_data = np.asarray(fitter.current)
    y_fit = np.asarray(fitted) if fitted is not None else y_data
    return sanitize_for_json({
        'x': x.tolist(),
        'y_data': y_data.tolist(),
        'y_fit': y_fit.tolist()
    })


def render_theta_data(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(**fit_options_from_request(form))
    theta_H, theta_empty = fitter.compute_theta()
    x = np.asarray(fitter.potential)
    return sanitize_for_json({
        'x': x.tolist(),
        'theta_H': np.asarray(theta_H).tolist(),
        'theta_empty': np.asarray(theta_empty).tolist()
    })


def render_tafel_data(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(**fit_options_from_request(form))
    win = int(form.get('tafel_window', 10))
    skip_pts = int(form.get('tafel_skip', 55))
    tafel_data = fitter.compute_tafel_slope(x=fitter.potential, use_fitted=False, window_size=win, method='rolling')
    if isinstance(tafel_data, tuple):
        x_data, slope_data = tafel_data
    else:
        x_data, slope_data = (tafel_data[:, 0], tafel_data[:, 1]) if tafel_data is not None and len(tafel_data) > 0 else ([], [])

    tafel_fit = fitter.compute_tafel_slope(x=fitter.potential, use_fitted=True, window_size=win, method='rolling')
    if isinstance(tafel_fit, tuple):
        x_fit, slope_fit = tafel_fit
    else:
        x_fit, slope_fit = (tafel_fit[:, 0], tafel_fit[:, 1]) if tafel_fit is not None and len(tafel_fit) > 0 else ([], [])

    return sanitize_for_json({
        'x_data': np.asarray(x_data).tolist(),
        'slope_data': np.asarray(slope_data).tolist(),
        'x_fit': np.asarray(x_fit).tolist(),
        'slope_fit': np.asarray(slope_fit).tolist()
    })





def render_plots_zip(form, files=None):
    """Generate complete downloadable ZIP archive with CSVs, fit report, PNGs and metadata."""
    import json as _json

    fitter = build_fitter_from_request(form, files)
    fit_opts = fit_options_from_request(form)
    fitter.fit_data(**fit_opts)

    plot_data = render_plot_data(form, files)
    theta_data = render_theta_data(form, files)
    tafel_data = render_tafel_data(form, files)

    img_plot = render_plot(form, files)
    img_theta = render_theta_plot(form, files)
    img_tafel = render_tafel_plot(form, files)

    fit_report = fitter.result_model.fit_report() if fitter.result_model else "No fit report generated."

    # Gather fit metadata for JSON export
    fit_metadata = {
        # Numerical strategy
        "fitting_method": fit_opts.get("fitting_method"),
        "use_global_search": fit_opts.get("use_global_search"),
        "global_method": fit_opts.get("global_method"),
        "n_starts": fit_opts.get("n_starts"),
        "relative_error": fit_opts.get("relative_error"),
        "current_noise_A": fit_opts.get("current_noise"),
        "robust_loss": fit_opts.get("robust_loss"),
        "robust_f_scale": fit_opts.get("robust_f_scale"),
        "max_nfev_global": fit_opts.get("max_nfev_global"),
        "max_nfev_local": fit_opts.get("max_nfev_local"),
        # Kinetic model
        "model_type": fit_opts.get("model_type"),
        "vary_bbv": as_bool(_request_value(form, "vary_bbv"), False),
        "vary_bbh": as_bool(_request_value(form, "vary_bbh"), False),
        "bbv": as_float(_request_value(form, "bbv"), 0.5),
        "bbh": as_float(_request_value(form, "bbh"), 0.5),
        # Experimental conditions
        "temperature_K": as_float(_request_value(form, "temperature"), 298.15),
        "pH": as_float(_request_value(form, "pH"), None),
        "area_electrode_cm2": as_float(_request_value(form, "area_electrode"), None),
        "ohmic_drop_ohm": as_float(_request_value(form, "ohmic_drop"), 0.0),
        "ref_potential_V_vs_SHE": as_float(_request_value(form, "ref_potential"), None),
    }

    # Compute raw residuals for polarization CSV
    x_arr = plot_data['x']
    y_exp_arr = plot_data['y_data']
    y_fit_arr = plot_data['y_fit']
    residuals = [
        (sanitize_for_json(y_fit_arr[i]) or 0.0) - (sanitize_for_json(y_exp_arr[i]) or 0.0)
        for i in range(len(x_arr))
    ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        # Fit Report
        z.writestr('Fit_Report.txt', fit_report)

        # Fit Metadata JSON — key for reproducibility
        z.writestr('fit_metadata.json', _json.dumps(fit_metadata, indent=2, ensure_ascii=False))

        # 1. Polarization Curve CSV (with raw residuals)
        csv_fit = (
            'potential_corrected_V,current_exp_A,current_fit_A,residual_raw_A\n'
            + '\n'.join(
                f"{x_arr[i]},{y_exp_arr[i]},{y_fit_arr[i]},{residuals[i]}"
                for i in range(len(x_arr))
            )
        )
        z.writestr('polarization_curve.csv', csv_fit)

        # 2. Theta Coverage CSV
        csv_theta = 'Potential_V,Theta_H,Theta_Empty\n' + '\n'.join(
            f"{theta_data['x'][i]},{theta_data['theta_H'][i]},{theta_data['theta_empty'][i]}"
            for i in range(len(theta_data['x']))
        )
        z.writestr('theta_coverage.csv', csv_theta)

        # 3. Tafel Slope CSV
        min_len = min(len(tafel_data['x_data']), len(tafel_data['x_fit']))
        csv_tafel = 'Potential_V,Tafel_Slope_Data_mV_dec,Tafel_Slope_Fit_mV_dec\n' + '\n'.join(
            f"{tafel_data['x_data'][i]},{tafel_data['slope_data'][i]},{tafel_data['slope_fit'][i]}"
            for i in range(min_len)
        )
        z.writestr('tafel_slope.csv', csv_tafel)

        # High-res Images
        z.writestr('polarization_curve.png', img_plot)
        z.writestr('theta_coverage.png', img_theta)
        z.writestr('tafel_slope.png', img_tafel)

    buf.seek(0)
    return buf.getvalue()

