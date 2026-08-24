from django.urls import path
from . import views

app_name = 'her'

urlpatterns = [
    path('', views.index, name='index'),
    path('fit', views.fit, name='fit'),
    path('plot', views.plot, name='plot'),
    path('plot_theta', views.plot_theta, name='plot_theta'),
    path('plot_tafel', views.plot_tafel, name='plot_tafel'),
    path('plot_decomposition', views.plot_decomposition, name='plot_decomposition'),
    path('fit_report', views.fit_report, name='fit_report'),
    path('load_sample', views.load_sample, name='load_sample'),
    path('export_plots_zip', views.export_plots_zip, name='export_plots_zip'),
    path('fit_summary', views.fit_summary, name='fit_summary'),
    path('docs', views.docs, name='docs'),
    path('about', views.about, name='about'),
]
