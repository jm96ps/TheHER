import os
import io
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from webapp.services.fitting_service import (
    run_fit,
    render_plot,
    render_theta_plot,
    render_tafel_plot,
    render_decomposition_plot,
    render_plot_data,
    render_theta_data,
    render_tafel_data,
    render_decomposition_data,
    render_plots_zip,
    build_fitter_from_request
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
def plot_decomposition(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    if request.POST.get('as') == 'json':
        data = render_decomposition_data(request.POST, request.FILES)
        return JsonResponse(data)
    img = render_decomposition_plot(request.POST, request.FILES)
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
            'model_type': 'simplified',
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
            'model_type': 'simplified',
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
            'model_type': 'simplified',
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
            'model_type': 'simplified',
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
            'model_type': 'simplified',
            'tafel_window': 10,
            'vary_bbv': 'false',
            'vary_bbh': 'false'
        }
    }

    preset = sample_registry.get(sample_key, sample_registry['Pt_example.txt'])
    target_filename = preset['filename']
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
    if request.method == 'POST':
        res = run_fit(request.POST, request.FILES)
        if not res.get('success'):
            return JsonResponse(res, status=400)
        stats = res.get('stats', {})
        params = res.get('parameters', {})
        n_points = res.get('n_points', 0)
        fit_report_text = res.get('fit_report', '')
        return render(request, 'fit_summary.html', {
            'stats': stats,
            'parameters': params,
            'n_points': n_points,
            'fit_report': fit_report_text
        })
    return render(request, 'fit_summary.html', {'stats': {}, 'parameters': {}, 'n_points': 0})


def docs(request):
    return render(request, 'her/documentation.html')


def about(request):
    author_info = {
        'contact_email': 'jamesmario@usp.br',
        'last_updated': '2026',
        'status': 'Active Development'
    }
    return render(request, 'her/about.html', {'author': author_info})
