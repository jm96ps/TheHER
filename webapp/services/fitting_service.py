import os
import io
import re
import zipfile
import traceback
import numpy as np
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


def build_fitter_from_request(form, files=None):
    uploaded = files.get('datafile') if files is not None else None
    saved_path = _save_uploaded_file(uploaded) if uploaded else None

    # Allow direct file_path or sample preset
    if not saved_path:
        fp = form.get('file_path')
        if fp:
            fp = os.path.abspath(fp)
            if os.path.exists(fp):
                saved_path = fp

    if not saved_path:
        # Default fallback to example file in workspace if nothing uploaded
        pt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Pt_example.txt')
        if os.path.exists(pt_path):
            saved_path = os.path.abspath(pt_path)

    def _to_float(v, default=None):
        try:
            if v is None or str(v).strip() == '':
                return default
            return float(v)
        except Exception:
            return default

    def _to_bool(v, default=True):
        if v is None or str(v).strip() == '':
            return default
        s = str(v).strip().lower()
        if s in ('false', '0', 'off', 'no', 'f', 'none', 'null', 'fixed'):
            return False
        if s in ('true', '1', 'on', 'yes', 't', 'vary', 'fitted'):
            return True
        return default

    params = dict(
        file_path=saved_path,
        area_electrode=_to_float(form.get('area_electrode'), None),
        ohmic_drop=_to_float(form.get('ohmic_drop'), 0.0),
        ref_correction=_to_float(form.get('ref_correction'), None),
        ref_potential=_to_float(form.get('ref_potential'), None),
        pH=_to_float(form.get('pH'), None),
        temperature=_to_float(form.get('temperature'), 298.15),
        gas_constant=_to_float(form.get('gas_constant'), 8.314462618),
        delimiter=form.get('delimiter', 'auto'),
        current_col=form.get('current_col', 1),
        potential_col=form.get('potential_col', 2),
        current_units=form.get('current_units', 'A'),
        bbv_initial=_to_float(form.get('bbv'), 0.5),
        bbh_initial=_to_float(form.get('bbh'), 0.5),
        vary_bbv=_to_bool(form.get('vary_bbv'), default=False),
        vary_bbh=_to_bool(form.get('vary_bbh'), default=False),
        bbv_min=_to_float(form.get('bbv_min'), 0.0),
        bbv_max=_to_float(form.get('bbv_max'), 1.0),
        bbh_min=_to_float(form.get('bbh_min'), 0.0),
        bbh_max=_to_float(form.get('bbh_max'), 1.0)
    )

    params.update({
        'k1_initial': _to_float(form.get('k1_init'), None),
        'k1_min': _to_float(form.get('k1_min'), 1e-20),
        'k1_max': _to_float(form.get('k1_max'), 1e-2),
        'vary_k1': _to_bool(form.get('vary_k1'), default=True),

        'k1r_initial': _to_float(form.get('k1r_init'), None),
        'k1r_min': _to_float(form.get('k1r_min'), 1e-20),
        'k1r_max': _to_float(form.get('k1r_max'), 1e-2),
        'vary_k1r': _to_bool(form.get('vary_k1r'), default=True),

        'k2_initial': _to_float(form.get('k2_init'), None),
        'k2_min': _to_float(form.get('k2_min'), 1e-20),
        'k2_max': _to_float(form.get('k2_max'), 1e-2),
        'vary_k2': _to_bool(form.get('vary_k2'), default=True),

        'k2r_initial': _to_float(form.get('k2r_init'), None),
        'k2r_min': _to_float(form.get('k2r_min'), 1e-20),
        'k2r_max': _to_float(form.get('k2r_max'), 1e-2),
        'vary_k2r': _to_bool(form.get('vary_k2r'), default=True),

        'k3_initial': _to_float(form.get('k3_init'), None),
        'k3_min': _to_float(form.get('k3_min'), 1e-20),
        'k3_max': _to_float(form.get('k3_max'), 1e-2),
        'vary_k3': _to_bool(form.get('vary_k3'), default=True),
    })

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
        fitter.fit_data(
            model_type=form.get('model_type', 'simplified'),
            fitting_method=form.get('fitting_method', 'powell')
        )
        res = fitter.get_results() or {}
    except Exception as e:
        tb = traceback.format_exc()
        return {'success': False, 'error': str(e), 'traceback': tb}

    params = {}
    params_details = {}
    if 'parameters' in res and res['parameters'] is not None:
        for name, p in res['parameters'].items():
            try:
                raw_val = float(p.value) if p.value is not None else None
                val = raw_val if (raw_val is not None and np.isfinite(raw_val)) else None
                params[name] = val

                raw_stderr = float(p.stderr) if (getattr(p, 'stderr', None) is not None) else None
                stderr_val = raw_stderr if (raw_stderr is not None and np.isfinite(raw_stderr)) else None

                raw_min = float(p.min) if (getattr(p, 'min', None) is not None) else None
                min_val = raw_min if (raw_min is not None and np.isfinite(raw_min)) else None

                raw_max = float(p.max) if (getattr(p, 'max', None) is not None) else None
                max_val = raw_max if (raw_max is not None and np.isfinite(raw_max)) else None

                params_details[name] = {
                    'value': val,
                    'stderr': stderr_val,
                    'vary': bool(getattr(p, 'vary', True)),
                    'min': min_val,
                    'max': max_val
                }
            except Exception:
                params[name] = str(getattr(p, 'value', None))
                params_details[name] = {'value': str(getattr(p, 'value', None))}

    stats_dict = fitter.get_stats() or {}

    return sanitize_for_json({
        'success': True,
        'model_type': res.get('model_type'),
        'parameters': params,
        'parameters_details': params_details,
        'stats': stats_dict,
        'fit_report': res.get('fit_report', ''),
        'n_points': int(len(fitter.potential)) if hasattr(fitter, 'potential') else 0,
        'file_path': fitter.file_path if hasattr(fitter, 'file_path') else None
    })


def render_plot(form, files=None):
    """Render Polarization Curve (Data vs Fit) matching hy2.py."""
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )

    result_model = getattr(fitter, 'result_model', None)
    try:
        fitted = getattr(result_model, 'best_fit', None)
        if fitted is None and result_model is not None:
            fitted = result_model.eval(x=fitter.potential)
    except Exception:
        fitted = None

    # Determine scaling: if area is given, plot mA/cm^2; otherwise mA
    area = fitter.area_electrode
    if area and float(area) > 0:
        scale = 1000.0 / float(area)
        ylabel = r'Current Density ($mA \cdot cm^{-2}$)'
    else:
        scale = 1000.0
        ylabel = r'Current ($mA$)'

    y_data = fitter.current * scale
    y_fit = fitted * scale if fitted is not None else None

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

    ax.plot(fitter.potential, y_data, 'o', color='#3b82f6', markersize=4, alpha=0.7, label='Experimental Data')
    if y_fit is not None:
        ax.plot(fitter.potential, y_fit, '-', color='#ef4444', linewidth=2.0, label='HER Kinetic Fit')

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


def render_theta_plot(form, files=None):
    """Render Surface Coverage (theta_H and 1 - theta_H) matching hy2.py."""
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )
    theta_H, theta_empty = fitter.compute_theta()
    x = np.asarray(fitter.potential)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

    ax.plot(x, theta_H, '-', color='#2563eb', linewidth=2.2, label=r'$\theta_H$ (Adsorbed Hydrogen)')
    ax.plot(x, theta_empty, '--', color='#10b981', linewidth=2.2, label=r'$\theta_{empty} = 1 - \theta_H$ (Free Sites)')

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


def render_tafel_plot(form, files=None):
    """Render Tafel slope analysis (Data vs Fit) matching hy2.py."""
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )

    win = int(form.get('tafel_window', 10))
    result_model = getattr(fitter, 'result_model', None)
    try:
        fitted = getattr(result_model, 'best_fit', None)
        if fitted is None and result_model is not None:
            fitted = result_model.eval(x=fitter.potential)
    except Exception:
        fitted = None

    tafel_data = fitter.compute_tafel_slope(x=fitter.potential, use_fitted=False, window_size=win, method='rolling')
    if isinstance(tafel_data, tuple):
        x_data, slope_data = tafel_data
    else:
        x_data, slope_data = (tafel_data[:, 0], tafel_data[:, 1]) if tafel_data is not None and len(tafel_data) > 0 else ([], [])

    tafel_fit = fitter.compute_tafel_slope(x=fitter.potential, use_fitted=True, window_size=win, method='rolling') if fitted is not None else None
    if isinstance(tafel_fit, tuple):
        x_fit, slope_fit = tafel_fit
    else:
        x_fit, slope_fit = (tafel_fit[:, 0], tafel_fit[:, 1]) if tafel_fit is not None and len(tafel_fit) > 0 else (None, None)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

    # The user requested to show the Tafel slope plot for fitted data ONLY, and in point style.
    if x_fit is not None and len(x_fit) > 0:
        ax.scatter(x_fit, slope_fit, marker='o', color='#8b5cf6', s=20, alpha=0.75, label='Fit Tafel Slope')

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


def render_decomposition_plot(form, files=None):
    """Render Volmer and Heyrovsky partial step decomposition matching hy2.py."""
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )
    decomp = fitter.compute_decomposition()
    x = decomp['x']

    area = fitter.area_electrode
    scale = (1000.0 / float(area)) if (area and float(area) > 0) else 1000.0
    ylabel = r'Current Density ($mA \cdot cm^{-2}$)' if (area and float(area) > 0) else r'Current ($mA$)'

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

    ax.plot(x, decomp['volmer'] * scale, '-', color='#3b82f6', linewidth=2.0, label='Volmer Step Rate')
    ax.plot(x, decomp['heyrovsky'] * scale, '-', color='#ec4899', linewidth=2.0, label='Heyrovsky Step Rate')
    ax.plot(x, decomp['total'] * scale, '--', color='#1f2937', linewidth=1.8, label='Total Rate (Volmer + Heyrovsky)')

    ax.set_xlabel('Potential vs RHE (V)', fontsize=11, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
    ax.set_title('Reaction Step Decomposition (Volmer vs Heyrovsky)', fontsize=12, fontweight='bold', pad=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_plot_data(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )
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
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )
    theta_H, theta_empty = fitter.compute_theta()
    x = np.asarray(fitter.potential)
    return sanitize_for_json({
        'x': x.tolist(),
        'theta_H': np.asarray(theta_H).tolist(),
        'theta_empty': np.asarray(theta_empty).tolist()
    })


def render_tafel_data(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )
    win = int(form.get('tafel_window', 10))
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


def render_decomposition_data(form, files=None):
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )
    decomp = fitter.compute_decomposition()
    return sanitize_for_json({
        'x': np.asarray(decomp['x']).tolist(),
        'volmer': np.asarray(decomp['volmer']).tolist(),
        'heyrovsky': np.asarray(decomp['heyrovsky']).tolist(),
        'total': np.asarray(decomp['total']).tolist()
    })


def render_plots_zip(form, files=None):
    """Generate complete downloadable ZIP archive with CSVs, fit report, and PNGs."""
    fitter = build_fitter_from_request(form, files)
    fitter.fit_data(
        model_type=form.get('model_type', 'simplified'),
        fitting_method=form.get('fitting_method', 'powell')
    )

    plot_data = render_plot_data(form, files)
    theta_data = render_theta_data(form, files)
    tafel_data = render_tafel_data(form, files)
    decomp_data = render_decomposition_data(form, files)

    img_plot = render_plot(form, files)
    img_theta = render_theta_plot(form, files)
    img_tafel = render_tafel_plot(form, files)
    img_decomp = render_decomposition_plot(form, files)

    fit_report = fitter.result_model.fit_report() if fitter.result_model else "No fit report generated."

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        # Fit Report
        z.writestr('Fit_Report.txt', fit_report)

        # 1. Polarization Curve CSV
        csv_fit = 'Potential_V,Experimental_Current_A,Fitted_Current_A\n' + '\n'.join(
            f"{plot_data['x'][i]},{plot_data['y_data'][i]},{plot_data['y_fit'][i]}"
            for i in range(len(plot_data['x']))
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

        # 4. Reaction Decomposition CSV
        csv_decomp = 'Potential_V,Volmer_Current_A,Heyrovsky_Current_A,Total_Current_A\n' + '\n'.join(
            f"{decomp_data['x'][i]},{decomp_data['volmer'][i]},{decomp_data['heyrovsky'][i]},{decomp_data['total'][i]}"
            for i in range(len(decomp_data['x']))
        )
        z.writestr('reaction_decomposition.csv', csv_decomp)

        # High-res Images
        z.writestr('polarization_curve.png', img_plot)
        z.writestr('theta_coverage.png', img_theta)
        z.writestr('tafel_slope.png', img_tafel)
        z.writestr('reaction_decomposition.png', img_decomp)

    buf.seek(0)
    return buf.getvalue()
