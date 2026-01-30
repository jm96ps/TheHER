import io
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Reuse existing service layer from the Flask migration to avoid duplicating logic
from webapp.services.fitting_service import run_fit, render_plot, render_theta_plot, render_tafel_plot, build_fitter_from_request
from webapp.services.fitting_service import render_theta_data, render_tafel_data, render_plot_data, render_plots_zip


def index(request):
    # Render the cleaned, organized template
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
    # support JSON data export when requested via 'as' parameter
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
def export_plots_zip(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        bz = render_plots_zip(request.POST, request.FILES)
        resp = HttpResponse(bz, content_type='application/zip')
        resp['Content-Disposition'] = 'attachment; filename=plots.zip'
        return resp
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def fit_summary(request):
    # Allow POST form (reuses service) or GET to render empty page
    if request.method == 'POST':
        res = run_fit(request.POST, request.FILES)
        if not res.get('success'):
            return JsonResponse(res, status=400)
        stats = res.get('stats', {})
        params = res.get('parameters', {})
        n_points = res.get('n_points', 0)
        return render(request, 'fit_summary.html', {'stats': stats, 'parameters': params, 'n_points': n_points})
    return render(request, 'fit_summary.html', {'stats': {}, 'parameters': {}, 'n_points': 0})


def docs(request):
    return render(request, 'her/documentation.html')


def about(request):
    # Simple about page using README contact and metadata
    author_info = {
        'contact_email': 'jamesmario@usp.br',
        'last_updated': 'January 2026',
        'status': 'Active Development'
    }
    return render(request, 'her/about.html', {'author': author_info})
