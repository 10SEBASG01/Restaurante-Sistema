from django.urls import path
from . import views

# Definimos el namespace (espacio de nombres) para no chocar con otras apps
app_name = 'reportes'

urlpatterns = [
    # La ruta será: midominio.com/reportes/dashboard/
    path('dashboard/', views.dashboard_reportes, name='dashboard'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
]