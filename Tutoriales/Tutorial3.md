# Tutorial 03: Introducción a APIs con DRF

## De Monolito HTML a Backend Headless

**Prof. Nicolás Ramírez Vélez - Arquitectura de Software 2026**

---

# 1. Objetivo

Implementar una capa de API REST utilizando Django Rest Framework (DRF).

El objetivo arquitectónico es demostrar la reutilización de la Capa de Servicio creada en sesiones anteriores, permitiendo que la lógica de negocio sirva tanto a vistas HTML como a clientes JSON.

---

# 2. Paso 1: Instalación y Configuración

Primero, debemos instalar la librería que actúa como estándar de la industria para APIs en Django.

## Terminal

```bash
# Desde su entorno virtual
pip install djangorestframework markdown django-filter

# O bien desde una terminal de Anaconda,
# ejecute los siguientes comandos

conda config --add channels conda-forge
conda config --set channel_priority strict
conda install djangorestframework
```

Añada `rest_framework` a su `INSTALLED_APPS` en `settings.py`.

---

# 3. Paso 2: El Adaptador (Serializer)

El Serializer es el patrón Adapter aplicado a datos.

Transformará nuestros modelos y objetos de dominio en JSON.

Cree el archivo `tienda_app/api/serializers.py`.

```python
from rest_framework import serializers
from tienda_app.models import Libro, Orden

class LibroSerializer(serializers.ModelSerializer):

    class Meta:
        model = Libro
        fields = [
            'id',
            'titulo',
            'precio',
            'stock_actual'
        ]
```

> Nota: `stock_actual` puede ser un campo calculado o propiedad del modelo.

```python
class OrdenInputSerializer(serializers.Serializer):
    """
    Serializer para VALIDAR la entrada de datos,
    no necesariamente ligado a un modelo.

    Actua como un DTO
    (Data Transfer Object).
    """

    libro_id = serializers.IntegerField()
    direccion_envio = serializers.CharField(
        max_length=200
    )

    # Validaciones extras aqui si fueran necesarias
```

---

# 4. Paso 3: La API View (El Controlador)

Aquí ocurre la magia de la arquitectura limpia.

En lugar de reescribir la lógica de compra, la API View simplemente actúa como un nuevo cliente para nuestro Servicio existente.

Cree o edite `tienda_app/api/views.py`:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import OrdenInputSerializer
from tienda_app.services import CompraService  # <-- REUTILIZACION
from tienda_app.infra.factories import PaymentFactory


class CompraAPIView(APIView):
    """
    Endpoint para procesar compras via JSON.

    POST /api/comprar/

    Payload:
    {
        "libro_id": 1,
        "direccion_envio": "Calle 123"
    }
    """

    def post(self, request):

        # 1. Validacion de datos de entrada (Adapter)
        serializer = OrdenInputSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        datos = serializer.validated_data

        try:

            # 2. Inyeccion de Dependencias (Factory)
            gateway = PaymentFactory.get_processor()

            # 3. Ejecucion de Logica de Negocio (Service Layer)
            servicio = CompraService(
                procesador_pago=gateway
            )

            # Noten como el servicio NO cambia,
            # solo cambia quien lo llama.

            resultado = servicio.ejecutar_compra(
                libro_id=datos['libro_id'],
                direccion=datos['direccion_envio'],
                usuario=request.user
                # Asumiendo autenticacion basica o sesion
            )

            return Response(
                {
                    "estado": "exito",
                    "mensaje": f"Orden creada. Total: {resultado}"
                },
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            # Errores de negocio (ej: Sin stock)

            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )

        except Exception as e:
            # Errores inesperados

            return Response(
                {"error": "Error interno"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

---

# 5. Paso 4: Enrutamiento (URLs)

Exponga el endpoint en `tienda_app/urls.py`.

```python
from django.urls import path
from tienda_app.api.views import CompraAPIView

urlpatterns = [

    # ... sus urls antiguas ...

    path(
        'api/v1/comprar/',
        CompraAPIView.as_view(),
        name='api_comprar'
    ),

]
```

---

# 6. Entrega de Resultados

## Evidencia Requerida

Para la calificación de este tutorial, el estudiante debe cargar en la plataforma:

### Archivo de Log

El sistema debe descontar inventario y generar el log de pagos (usando la Factory que configuró la semana pasada).

Muestre que al comprar por API, la vista HTML de inventario refleja el cambio.

Esto prueba que ambas "puertas" (HTML y API) conducen a la misma "habitación" (Lógica de Negocio).

### Prueba del Endpoint

Use Postman o la interfaz web de DRF para enviar un POST a:

```text
/api/v1/comprar/
```

Monte una captura de pantalla de esto.

### Entrega

Suba ambos archivos a la Asignación:

```text
tutorial0-3 DRF&API
```