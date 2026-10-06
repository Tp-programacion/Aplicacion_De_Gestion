# Sistema de Gestión de Estacionamiento

**Trabajo Práctico Final - Programación I**

Este repositorio contiene el código fuente de una aplicación de gestión de estacionamientos desarrollada como trabajo práctico para la asignatura **Programación I**. El objetivo del proyecto es aplicar los conceptos de desarrollo de software aprendidos durante la cursada, desde la definición y diseño del sistema hasta su implementación funcional.

---

## Estructura de vistas

`main.py` inicializa la aplicación, mantiene la sesión y dirige la navegación. Las pantallas están separadas dentro de `views/`:

- `login.py`: inicio de sesión y registro.
- `estacionamientos.py`: selección de estacionamiento.
- `admin.py`: administración de lugares e historial de pagos.
- `conductor.py`: disponibilidad y reservas.

Cada vista recibe la página y el estado compartido desde `main.py`.

## Características y Funcionalidades

El sistema cuenta con un sistema de autenticación de usuarios basado en dos roles principales: **Administradores** y **Conductores**.

### Sistema de Login
- Validación de credenciales de usuario.
- Redirección automática según el rol del usuario (Administrador o Conductor).

### Panel de Administrador
Los administradores tienen control total sobre el inventario de lugares del estacionamiento:
- **Añadir nuevos lugares:** Permite registrar un lugar ingresando número, tipo de vehículo admitido, precio por hora y disponibilidad.
- **Modificar lugares existentes:** Actualización de tarifas, cambio de disponibilidad o tipos de vehículos.
- **Borrar lugares:** Eliminación de espacios que ya no estén operativos.

### Panel de Conductor
Los usuarios que utilizan el estacionamiento pueden realizar las siguientes acciones:
- **Buscar lugares:** Visualización de los espacios que se encuentran actualmente disponibles.
- **Ver detalles:** Consultar el precio por hora y el tipo de vehículo admitido en cada lugar.
- **Reservar lugar:** Seleccionar y reservar un espacio de estacionamiento para su uso.

---

## Tecnologías Utilizadas

* **Lenguaje:** [Python]
* **Entorno de desarrollo:** [Visual Studio Code]
* **Almacenamiento de datos:** [SQLite] 

---

## Cómo ejecutar el proyecto

Para correr este proyecto en tu computadora local, sigue estos pasos:

1. Clona este repositorio:
   ```bash
   git clone https://github.com/Jero-Matukynas1/Aplicacion_De_Gestion
