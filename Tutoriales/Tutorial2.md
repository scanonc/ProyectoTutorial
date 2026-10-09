# Tutorial 02: Patrones Creacionales en Django

## Factory Method y Builder para Sistemas Escalables

**Prof. Nicolás Ramírez Vélez - TEIS / AdS 2026**

---

# 1. Objetivo

Optimizar la creación de objetos en nuestra arquitectura. Implementaremos el patrón **Factory Method** para desacoplar la infraestructura mediante variables de entorno y el patrón **Builder** para gestionar la construcción de objetos de dominio complejos.

---

# 2. Paso 1: Factory Method (Desacoplando Infraestructura)

El problema actual es que la vista decide qué procesador de pago usar. Si queremos cambiar a PayPal o a un Mock de pruebas, debemos editar el código. La Fábrica centralizará esta decisión basándose en la configuración del sistema.

## 2.1. Creación de la Fábrica en `infra/factories.py`

Este componente permite que nuestra aplicación sea "Docker-Ready", inyectando dependencias desde el entorno.

```python
import os
from .gateways import BancoNacionalProcesador

# Implementacion ligera para pruebas (Mocking)
class MockPaymentProcessor:
    def pagar(self, monto: float) -> bool:
        print(f"[DEBUG] Mock Payment: Procesando pago de ${monto} sin cargo real.")
        return True

class PaymentFactory:
    @staticmethod
    def get_processor():
        # LECCION ARQUITECTURA: La configuracion viene del ambiente, no del codigo
        provider = os.getenv('PAYMENT_PROVIDER', 'BANCO')

        if provider == 'MOCK':
            return MockPaymentProcessor()

        # Por defecto usamos la infraestructura real
        return BancoNacionalProcesador()
```

## 2.2. Refactorización de la Vista (`views.py`)

La vista ahora es "agnóstica": no sabe qué banco se usa, solo sabe que la fábrica le entrega algo que funciona.

```python
from .infra.factories import PaymentFactory

class CompraView(View):
    def setup_service(self):
        # ANTES: gateway = BancoNacionalProcesador()
        # AHORA: Delegacion total a la Fabrica
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)
```

---

# 3. Paso 2: Patrón Builder (Construcción de Dominio)

Crear una Orden implica calcular totales, impuestos y validar estados. En lugar de un constructor gigante en el modelo, usaremos un Builder para ensamblar el objeto paso a paso.

## 3.1. Definición del Builder en `domain/builders.py`

```python
from .models import Orden

class OrdenBuilder:
    def __init__(self):
        self.reset()

    def reset(self):
        self._usuario = None
        self._items = []
        self._direccion = ""

    def con_usuario(self, usuario):
        self._usuario = usuario
        return self  # Permite Fluent Interface

    def con_productos(self, productos):
        self._items = productos
        return self

    def para_envio(self, direccion):
        self._direccion = direccion
        return self

    def build(self) -> Orden:
        if not self._usuario or not self._items:
            raise ValueError("Datos insuficientes para crear la orden.")

        # Encapsulamos la logica de calculo
        subtotal = sum(p.precio for p in self._items)
        total_con_iva = subtotal * 1.19

        orden = Orden.objects.create(
            usuario=self._usuario,
            total=total_con_iva,
            direccion_envio=self._direccion
        )

        self.reset()
        return orden
```

# 4. Paso 3: Integración en el Service Layer

Actualizaremos nuestro `services.py` para que la lógica de negocio se lea como un proceso secuencial limpio.

```python
from .domain.builders import OrdenBuilder

class CompraService:
    def __init__(self, procesador_pago):
        self.procesador = procesador_pago
        self.builder = OrdenBuilder()

    def ejecutar_proceso_compra(self, usuario, lista_productos, direccion):
        # Uso del Builder: Semantica clara y validacion interna
        orden = (self.builder
                 .con_usuario(usuario)
                 .con_productos(lista_productos)
                 .para_envio(direccion)
                 .build())

        # Uso del Factory (inyectado): Cambio de comportamiento sin cambio de codigo
        if self.procesador.pagar(orden.total):
            return f"Orden {orden.id} procesada exitosamente."

        orden.delete()
        raise Exception("Error en la pasarela de pagos.")
```

---

# 5. Paso 4: Verificación y Despliegue Configurable

Una ventaja clave de este diseño es que permite cambiar el comportamiento del software desde la terminal o desde un archivo de configuración de Docker.

### Terminal - Prueba de Modos

```bash
# Ejecucion en modo Produccion (Banco Real)
python manage.py runserver

# Ejecucion en modo Desarrollo/Test (Usando el Factory)

# Windows (PowerShell):
$env:PAYMENT_PROVIDER="MOCK"; python manage.py runserver

# Linux/Mac/GitBash:
PAYMENT_PROVIDER=MOCK python manage.py runserver
```

---

# 6. Entrega de Resultados

## Evidencia Requerida

Para validar el uso de patrones creacionales, suba:

- Captura de Pantalla: Consola de Django mostrando el mensaje "[DEBUG] Mock Payment..." al realizar una compra con la variable de entorno activada.
- Código Fuente: Los archivos `infra/factories.py` y `domain/builders.py`.
- Reflexión: Un párrafo breve explicando por qué el `OrdenBuilder` reduce el riesgo de errores en comparación con crear la orden directamente en la vista.