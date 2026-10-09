from django.urls import path
from .api.views import CompraAPIView
from .views import CompraView

from . import views

urlpatterns = [
    # Usamos .as_view() para habilitar la CBV
    path('compra/<int:libro_id>/', CompraView.as_view(), name='finalizar_compra'),
    path('api/v1/comprar/', CompraAPIView.as_view(), name='api_comprar'),

    path('compra-fbv/<int:libro_id>/', views.compra_rapida_fbv, name='compra_rapida_fbv'),

    path('compra-cbv/<int:libro_id>/', views.CompraRapidaView.as_view(), name='compra_rapida_cbv'),
]