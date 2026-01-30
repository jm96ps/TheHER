from flask import Blueprint, render_template, request, jsonify, Response
from .services.fitting_service import run_fit, render_plot
import traceback
from .services.fitting_service import render_theta_plot, render_tafel_plot
from .services.fitting_service import build_fitter_from_request

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/simple')
def simple():
    return render_template('simple.html')


@bp.route('/fit', methods=['POST'])
def fit():
    try:
        result = run_fit(request.form, request.files)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/plot', methods=['POST'])
def plot():
    try:
        img = render_plot(request.form, request.files)
        return Response(img, mimetype='image/png')
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"success": False, "error": str(e), "traceback": tb}), 500


@bp.route('/plot_theta', methods=['POST'])
def plot_theta():
    try:
        img = render_theta_plot(request.form, request.files)
        return Response(img, mimetype='image/png')
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"success": False, "error": str(e), "traceback": tb}), 500


@bp.route('/plot_tafel', methods=['POST'])
def plot_tafel():
    try:
        img = render_tafel_plot(request.form, request.files)
        return Response(img, mimetype='image/png')
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"success": False, "error": str(e), "traceback": tb}), 500


@bp.route('/fit_summary', methods=['POST'])
def fit_summary():
    # run fit and render a summary page with stats and parameter table
    res = run_fit(request.form, request.files)
    if not res.get('success'):
        return jsonify(res), 400

    # stats and params come from run_fit
    stats = res.get('stats', {})
    params = res.get('parameters', {})
    n_points = res.get('n_points', 0)
    return render_template('fit_summary.html', stats=stats, parameters=params, n_points=n_points)
