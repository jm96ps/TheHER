from django.urls import path
from . import views

app_name = 'her'

urlpatterns = [
    path('', views.index, name='index'),
    path('fit', views.fit, name='fit'),
    path('plot', views.plot, name='plot'),
    path('plot_theta', views.plot_theta, name='plot_theta'),
    path('plot_tafel', views.plot_tafel, name='plot_tafel'),
    path('fit_summary', views.fit_summary, name='fit_summary'),
    path('docs', views.docs, name='docs'),
]
