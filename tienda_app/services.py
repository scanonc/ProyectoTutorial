from .domain.logic import CalculadorImpuestos
from .domain.builders import OrdenBuilder
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


class CompraService:
    def __init__(self, procesador_pago):
        self.procesador = procesador_pago
        self.builder = OrdenBuilder()

    def ejecutar_compra(self, libro_id, cantidad, direccion, usuario=None):
        try:
            libro = Libro.objects.get(id=libro_id)
            inventario = Inventario.objects.get(libro=libro)
        except (Libro.DoesNotExist, Inventario.DoesNotExist):
            raise ValueError("El libro o el inventario no existen.")

        if inventario.cantidad < cantidad:
            raise ValueError("No hay existencias suficientes.")

        orden = (
            self.builder
            .con_usuario(usuario)
            .con_libro(libro)
            .con_cantidad(cantidad)
            .para_envio(direccion)
            .build()
        )

        if self.procesador.pagar(orden.total):
            inventario.cantidad -= cantidad
            inventario.save()
            return orden.total

        orden.delete()
        raise Exception("Error en la pasarela de pagos.")