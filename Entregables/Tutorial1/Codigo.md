CODIGO DE services.py

from .domain.logic import CalculadorImpuestos
from .models import Inventario, Libro, Orden


class CompraRapidaService:
    def __init__(self, procesador_pago):
        # Recibimos el procesador por inyección de dependencias
        self.procesador_pago = procesador_pago

    def procesar(self, libro_id: int):
        try:
            libro = Libro.objects.get(id=libro_id)
            inv = Inventario.objects.get(libro=libro)
        except (Libro.DoesNotExist, Inventario.DoesNotExist):
            raise ValueError("El libro o el inventario no existen.")

        if inv.cantidad <= 0:
            raise ValueError("No hay existencias.")

        # Calculamos total mediante la clase de dominio
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)

        # Delegamos la ejecución del pago a la abstracción de infraestructura
        if self.procesador_pago.pagar(total):
            inv.cantidad -= 1
            inv.save()
            Orden.objects.create(libro=libro, total=total)
            return total
        return None

#============================================================================================0

CODIGO DE views.py


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