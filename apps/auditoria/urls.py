from django.urls import path
from . import views

urlpatterns = [
    # La ruta vacía '' significa que entrar a /auditoria/ cargará esta vista
    path('', views.auditoria_lista, name='auditoria_lista'),
]