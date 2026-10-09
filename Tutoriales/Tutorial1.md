# Tutorial01: Evolución de Arquitectura en Django

## De Spaghetti Code a Grado Empresarial

**Prof. Nicolás Ramírez Vélez - TEIS / AdS 2026**

---

# 1. Objetivo

Transformar una funcionalidad crítica de negocio desde una función desordenada hasta una arquitectura desacoplada utilizando CBVs, SOLID y Service Layer.

---

# 2. Paso 0: Preparación del Entorno

Antes de comenzar, debemos clonar el repositorio base que contiene la estructura de capas (domain, infra, models) que servirá como nuestro estándar de calidad.

Analicen bien este código y entiendan dónde va qué dentro de la arquitectura MVT que propone Django y los principios SOLID que ya le hemos aplicado.

## Terminal - Configuración Inicial

```bash
# 1. Clonar el repositorio profesional
git clone https://github.com/Nram94/TEIS-DjangoSOLID
cd directorio-de-su-aplicacion

# 2. Configurar entorno virtual e instalar dependencias
# (solo si NO USA UN GESTOR COMO ANACONDA)

python -m venv venv
source venv/bin/activate

# Windows:
venv\Scripts\activate

pip install django

# 3. Preparar base de datos y datos de prueba

python manage.py migrate
python manage.py shell
```

## 2.1. Configuración de Datos de Prueba

Dentro del shell de Django, ejecute lo siguiente para asegurarse de tener un producto con stock:

```python
from tienda_app.models import Libro, Inventario

l = Libro.objects.create(
    titulo="Clean Code en Python",
    precio=150.0
)
```

```python
Inventario.objects.create(libro=l, cantidad=10)
```

---

# 3. Paso 1: El Punto de Partida (FBV Spaghetti)

Implementaremos una funcionalidad de "Compra Rápida". Esta vista tiene múltiples responsabilidades: gestiona inventario, calcula impuestos y realiza procesos de infraestructura.

## 3.1. Actualización de views.py

Añada esta función al final de su archivo de vistas. Observe los comentarios que señalan la deuda técnica.

```python
import datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Libro, Inventario, Orden

def compra_rapida_fbv(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)

    if request.method == 'POST':

        # VIOLACION SRP: Logica de inventario en la vista
        inventario = Inventario.objects.get(libro=libro)

        if inventario.cantidad > 0:

            # VIOLACION OCP: Calculo de negocio hardcoded
            total = float(libro.precio) * 1.19

            # VIOLACION DIP: Proceso de pago acoplado al file system
            with open("pagos_manuales.log", "a") as f:
                f.write(
                    f"[{datetime.datetime.now()}] Pago FBV: ${total}\n"
                )

            inventario.cantidad -= 1
            inventario.save()

            Orden.objects.create(
                libro=libro,
                total=total
            )

            return HttpResponse(
                f"Compra exitosa: {libro.titulo}"
            )

        else:
            return HttpResponse(
                "Sin stock",
                status=400
            )

    total_estimado = float(libro.precio) * 1.19

    return render(
        request,
        'tienda_app/compra_rapida.html',
        {
            'libro': libro,
            'total': total_estimado
        }
    )
```

## 3.2. Template tienda_app/compra_rapida.html

```html
<!DOCTYPE html>
<html>
<body>

<h1>Compra Rapida (Modo Spaghetti)</h1>

<p>
    Libro: <strong>{{ libro.titulo }}</strong>
</p>

<p>
    Precio Final (IVA): ${{ total }}
</p>

<form method="post">
    {% csrf_token %}
    <button
        type="submit"
        style="background: orange;"
    >
        Comprar Ya
    </button>
</form>

</body>
</html>
```

---

# 4. Paso 2: Migración a Class-Based View (CBV)

El primer paso para el orden es separar los verbos HTTP. Al usar clases, eliminamos condicionales innecesarios y preparamos la vista para la inyección de dependencias.

```python
from django.views import View

class CompraRapidaView(View):

    template_name = 'tienda_app/compra_rapida.html'

    def get(self, request, libro_id):

        libro = get_object_or_404(
            Libro,
            id=libro_id
        )

        total = float(libro.precio) * 1.19

        return render(
            request,
            self.template_name,
            {
                'libro': libro,
                'total': total
            }
        )

    def post(self, request, libro_id):

        # La logica de negocio aun reside aqui,
        # pero separada del GET

        libro = get_object_or_404(
            Libro,
            id=libro_id
        )

        inv = Inventario.objects.get(libro=libro)

        if inv.cantidad > 0:
            total = float(libro.precio) * 1.19

            # ... proceso de compra ...

            return HttpResponse(
                "Comprado via CBV"
            )

        return HttpResponse(
            "Error",
            status=400
        )
```

---

# 5. Paso 3: La Capa de Servicio (Service Layer)

Finalmente, extraemos la lógica de orquestación. La vista solo debe ser un puente entre la web y el servicio de negocio.

## 5.1. Definición del Servicio en services.py

```python
class CompraRapidaService:

    def __init__(self, procesador_pago):
        self.procesador_pago = procesador_pago

    def procesar(self, libro_id):

        libro = Libro.objects.get(
            id=libro_id
        )

        inv = Inventario.objects.get(
            libro=libro
        )

        if inv.cantidad <= 0:
            raise ValueError(
                "No hay existencias."
            )

        total = (
            CalculadorImpuestos
            .obtener_total_con_iva(
                libro.precio
            )
        )

        if self.procesador_pago.pagar(total):

            inv.cantidad -= 1
            inv.save()

            return total

        return None
```

---

# 6. Paso 4: Evidencia de Ejecución (Log de Auditoría)

Para validar que la arquitectura funciona y que cada componente está cumpliendo su rol, utilizaremos un sistema de trazabilidad personalizado.

El éxito del tutorial se demostrará mediante la generación de un archivo de log específico.

## 6.1. Modificación del Gateway

En su archivo `infra/gateways.py`, asegúrese de que el nombre del archivo incluya su identidad. Esto garantiza que la prueba de ejecución sea única.

```python
import datetime
from ..domain.interfaces import ProcesadorPago

class BancoNacionalProcesador(ProcesadorPago):

    def pagar(self, monto: float) -> bool:

        # SUSTITUYA "SU_NOMBRE"
        # por su nombre y apellido real

        archivo_log = (
            "pagos_locales_JUAN_PEREZ.log"
        )

        with open(archivo_log, "a") as f:
            f.write(
                f"[{datetime.datetime.now()}] "
                f"Transaccion exitosa por: "
                f"${monto}\n"
            )

        return True
```

## 6.2. Instrucciones de Verificación

1. Reinicie su servidor de Django:

```bash
python manage.py runserver
```

2. Realice al menos tres compras de diferentes libros usando la nueva vista de Compra Rápida.

3. Localice en la raíz de su proyecto el archivo generado:

```text
pagos_locales_SU_NOMBRE.log
```

---

# 7. Entrega de Resultados

## Evidencia Requerida

Para la calificación de este tutorial, el estudiante debe cargar en la plataforma:

- Archivo de Log: El archivo `.log` generado con su nombre, conteniendo al menos 3 registros de transacciones.
- Resumen de Código: Un documento con el código de su `services.py` y `views.py` para validar que la lógica fue extraída correctamente de la capa de presentación.
- Entrega: Suba ambos archivos a la Asignación "tutorial01-DjangoSOLID".

---

# 8. Conclusión

Al finalizar este tutorial, la vista del estudiante debe tener menos de 10 líneas de código, delegando toda la complejidad al `CompraRapidaService`.

Esto permite que el código sea testeable, mantenible y escalable.