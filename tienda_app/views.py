from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View

from .models import Libro
from .domain.logic import CalculadorImpuestos
from .infra.gateways import BancoNacionalProcesador
from .services import CompraRapidaService


class CompraRapidaView(View):
    template_name = 'tienda_app/compra_rapida.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        # Instanciamos el gateway y se lo inyectamos al servicio
        procesador = BancoNacionalProcesador()
        self.service = CompraRapidaService(procesador_pago=procesador)

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return render(request, self.template_name, {
            'libro': libro,
            'total': total
        })

    def post(self, request, libro_id):
        try:
            total = self.service.procesar(libro_id)
            if total:
                return HttpResponse(f"Compra exitosa vía Service Layer: ${total}")
            return HttpResponse("Error en el pago", status=400)
        except ValueError as e:
            return HttpResponse(str(e), status=400)