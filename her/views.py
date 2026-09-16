import os
import io
import math
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from webapp.services.fitting_service import (
    run_fit,
    render_plot,
    render_theta_plot,
    render_tafel_plot,
    render_plot_data,
    render_theta_data,
    render_tafel_data,
    render_plots_zip,
    build_fitter_from_request,
    fit_options_from_request,
)


def index(request):
    return render(request, 'index_organized.html')


@csrf_exempt
def fit(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    result = run_fit(request.POST, request.FILES)
    status = 200 if result.get('success') else 400
    return JsonResponse(result, status=status)


@csrf_exempt
def plot(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    if request.POST.get('as') == 'json':
        data = render_plot_data(request.POST, request.FILES)
        return JsonResponse(data)
    img = render_plot(request.POST, request.FILES)
    return HttpResponse(img, content_type='image/png')


@csrf_exempt
def plot_theta(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    if request.POST.get('as') == 'json':
        data = render_theta_data(request.POST, request.FILES)
        return JsonResponse(data)
    img = render_theta_plot(request.POST, request.FILES)
    return HttpResponse(img, content_type='image/png')


@csrf_exempt
def plot_tafel(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    if request.POST.get('as') == 'json':
        data = render_tafel_data(request.POST, request.FILES)
        return JsonResponse(data)
    img = render_tafel_plot(request.POST, request.FILES)
    return HttpResponse(img, content_type='image/png')


@csrf_exempt
def fit_report(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    res = run_fit(request.POST, request.FILES)
    if not res.get('success'):
        return JsonResponse(res, status=400)
    report_text = res.get('fit_report', 'No report available')
    response = HttpResponse(report_text, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="Fit_Report.txt"'
    return response


def load_sample(request):
    """Provide sample dataset content and electrochemical configuration."""
    sample_key = request.GET.get('sample', 'Pt_example.txt')

    sample_registry = {
        'Pt_example.txt': {
            'filename': 'Pt_example.txt',
            'name': 'Pt in Alkaline (Pt_example.txt)',
            'current_col': 2,
            'potential_col': 1,
            'area_electrode': 0.196,
            'ohmic_drop': 6.05,
            'ref_potential': 0.098,
            'pH': 14.0,
            'temperature': 298.15,
            'delimiter': 'auto',
            'model_type': 'Volmer-Heyrovsky',
            'tafel_window': 10,
            'vary_bbv': 'false',
            'vary_bbh': 'false'
        },
        'LSV_Mo2C_5_EF1_x(4)_exemple.txt': {
            'filename': 'LSV_Mo2C_5_EF1_x(4)_exemple.txt',
            'name': 'Mo2C EF1 (LSV_Mo2C_5_EF1_x(4)_exemple.txt)',
            'current_col': 1,
            'potential_col': 2,
            'area_electrode': 0.196,
            'ohmic_drop': 6.05,
            'ref_potential': 0.098,
            'pH': 14.0,
            'temperature': 298.15,
            'delimiter': 'auto',
            'model_type': 'Volmer-Heyrovsky',
            'tafel_window': 10,
            'vary_bbv': 'false',
            'vary_bbh': 'false'
        },
        'LSV_Mo2C_EF0_3(1)_exemple.txt': {
            'filename': 'LSV_Mo2C_EF0_3(1)_exemple.txt',
            'name': 'Mo2C EF0 (LSV_Mo2C_EF0_3(1)_exemple.txt)',
            'current_col': 1,
            'potential_col': 2,
            'area_electrode': 0.196,
            'ohmic_drop': 6.05,
            'ref_potential': 0.098,
            'pH': 14.0,
            'temperature': 298.15,
            'delimiter': 'auto',
            'model_type': 'Volmer-Heyrovsky',
            'tafel_window': 10,
            'vary_bbv': 'false',
            'vary_bbh': 'false'
        },
        'LSV_Mo2C_EF3_3(2)_exemple.txt': {
            'filename': 'LSV_Mo2C_EF3_3(2)_exemple.txt',
            'name': 'Mo2C EF3 (LSV_Mo2C_EF3_3(2)_exemple.txt)',
            'current_col': 1,
            'potential_col': 2,
            'area_electrode': 0.196,
            'ohmic_drop': 6.05,
            'ref_potential': 0.098,
            'pH': 14.0,
            'temperature': 298.15,
            'delimiter': 'auto',
            'model_type': 'Volmer-Heyrovsky',
            'tafel_window': 10,
            'vary_bbv': 'false',
            'vary_bbh': 'false'
        },
        'Pt_NaOH_non-free_before(1)_exemple.txt': {
            'filename': 'Pt_NaOH_non-free_before(1)_exemple.txt',
            'name': 'Pt in NaOH (Pt_NaOH_non-free_before(1)_exemple.txt)',
            'current_col': 2,
            'potential_col': 1,
            'area_electrode': 0.196,
            'ohmic_drop': 6.05,
            'ref_potential': 0.098,
            'pH': 14.0,
            'temperature': 298.15,
            'delimiter': 'auto',
            'model_type': 'Volmer-Heyrovsky',
            'tafel_window': 10,
            'vary_bbv': 'false',
            'vary_bbh': 'false'
        }
    }

    preset = sample_registry.get(sample_key, sample_registry['Pt_example.txt'])
    target_filename = preset['filename']
    sample_file = os.path.join(settings.BASE_DIR, 'sample_data', target_filename)
    if not os.path.exists(sample_file):
        sample_file = os.path.join(settings.BASE_DIR, target_filename)

    content = ""
    if os.path.exists(sample_file):
        with open(sample_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

    return JsonResponse({
        'success': True,
        'filename': target_filename,
        'content': content,
        'defaults': preset,
        'available_samples': [
            {'key': k, 'name': v['name']} for k, v in sample_registry.items()
        ]
    })


@csrf_exempt
def export_plots_zip(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        bz = render_plots_zip(request.POST, request.FILES)
        resp = HttpResponse(bz, content_type='application/zip')
        resp['Content-Disposition'] = 'attachment; filename=HER_Fitting_Results.zip'
        return resp
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def fit_summary(request):
    """Run fit and render summary page with enriched context."""
    if request.method == 'POST':
        res = run_fit(request.POST, request.FILES)
        if not res.get('success'):
            return JsonResponse(res, status=400)

        stats = res.get('stats', {})
        params = res.get('parameters', {})
        params_details = res.get('parameters_details', {})
        n_points = res.get('n_points', 0)
        fit_report_text = res.get('fit_report', '')

        # Build fit metadata from form values
        fit_options = fit_options_from_request(request.POST)
        fit_meta = {
            'model_type': fit_options.get('model_type', '-'),
            'fitting_method': fit_options.get('fitting_method', '-'),
            'use_global_search': fit_options.get('use_global_search', False),
            'global_method': fit_options.get('global_method', '-'),
            'n_starts': fit_options.get('n_starts', '-'),
            'relative_error': fit_options.get('relative_error', '-'),
            'current_noise': fit_options.get('current_noise', None),
            'robust_loss': fit_options.get('robust_loss', '-'),
            'vary_bbv': request.POST.get('vary_bbv', 'false').lower() in ('true', '1', 'yes', 'on'),
            'vary_bbh': request.POST.get('vary_bbh', 'false').lower() in ('true', '1', 'yes', 'on'),
            'bbv': request.POST.get('bbv', '0.5'),
            'bbh': request.POST.get('bbh', '0.5'),
            'temperature': request.POST.get('temperature', '-'),
            'pH': request.POST.get('pH', '-'),
            'area_electrode': request.POST.get('area_electrode', '-'),
            'ohmic_drop': request.POST.get('ohmic_drop', '-'),
            'ref_potential': request.POST.get('ref_potential', '-'),
        }

        # Build identifiability alerts
        PHYS_KEYS = ('k1', 'k1r', 'k2', 'k2r', 'k3', 'k3r', 'bbv', 'bbh')
        alerts = []
        for name in PHYS_KEYS:
            det = params_details.get(name)
            if not det:
                continue
            val = det.get('value')
            mn = det.get('min')
            mx = det.get('max')
            stderr = det.get('stderr')
            vary = det.get('vary', True)

            if not vary:
                continue  # fixed params are expected to have no stderr

            if stderr is None:
                alerts.append(
                    f"\u2022 <strong>{name}</strong>: erro padrão indisponível — "
                    "o parâmetro pode não ser identificado pelos dados."
                )

            if val is not None and mn is not None and mx is not None:
                try:
                    span = float(mx) - float(mn)
                    if span > 0 and abs(float(val) - float(mn)) / span < 0.01:
                        alerts.append(
                            f"\u2022 <strong>{name}</strong>: valor próximo ao limite inferior ({mn}). "
                            "Considere ampliar os limites ou verificar os dados."
                        )
                    elif span > 0 and abs(float(val) - float(mx)) / span < 0.01:
                        alerts.append(
                            f"\u2022 <strong>{name}</strong>: valor próximo ao limite superior ({mx}). "
                            "Considere ampliar os limites ou verificar os dados."
                        )
                except (TypeError, ValueError):
                    pass

        return render(request, 'fit_summary.html', {
            'stats': stats,
            'parameters': params,
            'parameters_details': params_details,
            'internal_parameters': res.get('internal_parameters', {}),
            'internal_parameters_details': res.get('internal_parameters_details', {}),
            'n_points': n_points,
            'fit_report': fit_report_text,
            'fit_meta': fit_meta,
            'identifiability_alerts': alerts,
        })

    return render(request, 'fit_summary.html', {
        'stats': {}, 'parameters': {}, 'parameters_details': {},
        'internal_parameters': {}, 'internal_parameters_details': {},
        'n_points': 0, 'fit_meta': {}, 'identifiability_alerts': [],
    })


def docs(request):
    return render(request, 'her/documentation.html')


def about(request):
    author_info = {
        'contact_email': 'jamesmario@usp.br',
        'last_updated': '2026',
        'status': 'Active Development'
    }
    return render(request, 'her/about.html', {'author': author_info})
