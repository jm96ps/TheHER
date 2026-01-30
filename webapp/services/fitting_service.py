import os
import io
import traceback
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
from ..models.hydrogen import hydrogen_fitting

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_uploaded_file(file_storage):
    if not file_storage:
        return None
    # Support both Flask's FileStorage and Django's UploadedFile
    filename = getattr(file_storage, 'filename', None) or getattr(file_storage, 'name', None) or ''
    filename = secure_filename(filename)
    if not filename:
        return None
    path = os.path.join(UPLOAD_DIR, filename)

    # If the object supports a .save(path) method (Flask FileStorage), use it.
    try:
        save_fn = getattr(file_storage, 'save', None)
        if callable(save_fn):
            # Some frameworks accept a path, others expect a file-like object.
            try:
                file_storage.save(path)
                return path
            except TypeError:
                # Maybe expects a file object
                with open(path, 'wb') as f:
                    save_fn(f)
                return path
    except Exception:
        pass

    # Fallback: write bytes from .read() or iterate .chunks() (Django UploadedFile)
    try:
        # Django UploadedFile provides chunks() for potentially large uploads
        if hasattr(file_storage, 'chunks'):
            with open(path, 'wb') as destination:
                for chunk in file_storage.chunks():
                    destination.write(chunk)
            return path
        # file-like object with read()
        data = None
        if hasattr(file_storage, 'read'):
            data = file_storage.read()
        elif isinstance(file_storage, (bytes, bytearray)):
            data = file_storage
        if data is not None:
            # If data is text, encode to bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
            with open(path, 'wb') as f:
                f.write(data)
            return path
    except Exception:
        pass

    return None


def build_fitter_from_request(form, files):
    # Save uploaded file (if any) and assemble kwargs for hydrogen_fitting
    uploaded = files.get('datafile') if files is not None else None
    saved_path = _save_uploaded_file(uploaded) if uploaded and getattr(uploaded, 'filename', None) else None
    # allow file_path override
    if (not saved_path) and form.get('file_path'):
        fp = os.path.abspath(form.get('file_path'))
        if os.path.exists(fp):
            saved_path = fp

    # collect params with defensive numeric coercion
    def _to_float(v, default=None):
        try:
            return float(v)
        except Exception:
            return default

    params = dict(
        file_path=saved_path,
        area_electrode=form.get('area_electrode'),
        ohmic_drop=_to_float(form.get('ohmic_drop'), 0.0),
        ref_correction=_to_float(form.get('ref_correction'), None),
        ref_potential=_to_float(form.get('ref_potential'), None),
        pH=_to_float(form.get('pH'), None),
        temperature=_to_float(form.get('temperature'), None),
        gas_constant=_to_float(form.get('gas_constant'), None),
        delimiter=form.get('delimiter', 'auto'),
        current_col=form.get('current_col', 1),
        potential_col=form.get('potential_col', 2),
        current_units=form.get('current_units', 'A'),
        bbv_initial=_to_float(form.get('bbv'), 0.5),
        bbh_initial=_to_float(form.get('bbh'), 0.5),
        vary_bbv=(form.get('vary_bbv', 'true').lower() != 'false'),
        vary_bbh=(form.get('vary_bbh', 'true').lower() != 'false')
    )

    fitter = hydrogen_fitting(**params)
    return fitter


def run_fit(form, files):
    try:
        fitter = build_fitter_from_request(form, files)
        fitter.fit_data(model_type=form.get('model_type', 'simplified'), fitting_method=form.get('fitting_method', 'powell'))
        res = fitter.get_results() or {}
    except Exception as e:
        tb = traceback.format_exc()
        return {'success': False, 'error': str(e), 'traceback': tb}

    params = {}
    if 'parameters' in res and res['parameters'] is not None:
        for name, p in res['parameters'].items():
            try:
                params[name] = float(p.value)
            except Exception:
                params[name] = str(getattr(p, 'value', None))

    return {
        'success': True,
        'model_type': res.get('model_type'),
        'parameters': params,
        'n_points': int(getattr(fitter, '_raw', getattr(fitter, 'current', [])).shape[0]) if getattr(fitter, '_raw', None) is not None else (len(getattr(fitter, 'current', [])) if hasattr(fitter, 'current') else 0),
        'stats': {
            'chisqr': getattr(fitter.result_model, 'chisqr', None),
            'redchi': getattr(fitter.result_model, 'redchi', None),
            'aic': getattr(fitter.result_model, 'aic', None),
            'bic': getattr(fitter.result_model, 'bic', None),
            'nfree': getattr(fitter.result_model, 'nfree', None),
        }
    }


def render_plot(form, files):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(model_type=form.get('model_type', 'simplified'), fitting_method=form.get('fitting_method', 'powell'))

    result_model = getattr(fitter, 'result_model', None)
    try:
        fitted = getattr(result_model, 'best_fit', None)
        if fitted is None and result_model is not None:
            fitted = result_model.eval(x=fitter.potential)
    except Exception:
        fitted = None

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(fitter.potential, fitter.current, 'k.', label='data')
    if fitted is not None:
        ax.plot(fitter.potential, fitted, 'r-', label='fit')
    ax.set_xlabel('Potential (V)')
    ax.set_ylabel('Current (A)')
    ax.legend()
    ax.grid(True)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _compute_theta(fitter, x=None):
    if getattr(fitter, 'result_model', None) is None:
        raise ValueError('No fit available to compute theta')
    params = fitter.result_model.params
    model_type = getattr(fitter, 'model_type', '')
    f1_val = getattr(fitter, 'f1', 38.92)
    if x is None:
        x = np.array(fitter.potential)
    x = np.asarray(x, dtype=float)

    if 'Hydrogen_Full' not in model_type and 'full' not in model_type.lower():
        raise ValueError('Theta (coverage) only available for full model fits')

    def val(name):
        p = params.get(name)
        return float(p.value) if p is not None else 0.0

    k1 = val('k1')
    k1r = val('k1r')
    k2 = val('k2')
    k2r = val('k2r')
    k3 = val('k3')
    k3r = val('k3r')
    bbv = val('bbv')
    bbh = val('bbh')

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


def render_theta_plot(form, files):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(model_type=form.get('model_type', 'simplified'), fitting_method=form.get('fitting_method', 'powell'))
    theta = _compute_theta(fitter)
    x = np.asarray(fitter.potential)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, theta, 'b-', label='coverage (theta)')
    ax.set_xlabel('Potential (V)')
    ax.set_ylabel('Theta (coverage)')
    ax.legend()
    ax.grid(True)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_tafel_plot(form, files):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(model_type=form.get('model_type', 'simplified'), fitting_method=form.get('fitting_method', 'powell'))
    result_model = getattr(fitter, 'result_model', None)
    if result_model is None:
        raise ValueError('No fit available to compute Tafel slope')

    try:
        fitted = getattr(result_model, 'best_fit', None)
        if fitted is None:
            fitted = result_model.eval(x=fitter.potential)
    except Exception:
        fitted = None

    x = np.asarray(fitter.potential)
    I = np.asarray(fitted) if fitted is not None else np.asarray(fitter.current)
    eps = 1e-30
    logI = np.log10(np.abs(I) + eps)
    dx = np.gradient(x)
    dlogI = np.gradient(logI)
    with np.errstate(divide='ignore', invalid='ignore'):
        slope_V_per_decade = np.where(dlogI == 0, np.nan, dx / dlogI)

    slope_mV_per_dec = slope_V_per_decade * 1000.0

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, slope_mV_per_dec, 'g-', label='Tafel slope (mV/dec)')
    ax.set_xlabel('Potential (V)')
    ax.set_ylabel('Tafel slope (mV/dec)')
    ax.legend()
    ax.grid(True)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
