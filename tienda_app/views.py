from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View

from .models import Inventario, Libro
from .domain.logic import CalculadorImpuestos
from .infra.factories import PaymentFactory
from .services import CompraRapidaService, CompraService


def inventario_view(request):
    inventarios = Inventario.objects.select_related('libro').order_by('libro__id')
    return render(
        request,
        'tienda_app/inventario.html',
        {'inventarios': inventarios},
    )


def compra_rapida_fbv(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)

    if request.method == 'POST':
        try:
            total = CompraRapidaService(
                procesador_pago=PaymentFactory.get_processor()
            ).procesar(libro_id)
        except ValueError as error:
            return HttpResponse(str(error), status=400)

        if total:
            return HttpResponse(f"Compra exitosa: {libro.titulo}")
        return HttpResponse("Error en el pago", status=400)

    total_estimado = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
    return render(
        request,
        'tienda_app/compra_rapida.html',
        {'libro': libro, 'total': total_estimado},
    )


class CompraView(View):
    template_name = 'tienda_app/compra.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.service = self.setup_service()

    def setup_service(self):
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return render(
            request,
            self.template_name,
            {'libro': libro, 'total': total},
        )

    def post(self, request, libro_id):
        try:
            resultado = self.service.ejecutar_compra(
                libro_id=libro_id,
                cantidad=1,
                direccion="",
                usuario=request.user if request.user.is_authenticated else None,
            )
            return HttpResponse(f"Orden creada. Total: {resultado}")
        except ValueError as error:
            return HttpResponse(str(error), status=400)


class CompraRapidaView(View):
    template_name = 'tienda_app/compra_rapida.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        procesador = PaymentFactory.get_processor()
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