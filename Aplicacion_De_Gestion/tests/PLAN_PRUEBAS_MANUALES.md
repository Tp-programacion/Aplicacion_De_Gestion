# Plan de pruebas manuales — Gestión de Estacionamiento

Complementa a `test_database.py` (que cubre la capa de datos). Acá se cubre lo que
solo se puede validar mirando la interfaz: navegación, mensajes, colores y flujos.

## Antes de empezar

- Empezá con una base limpia (borrá el `.db` y abrí la app para que `init_db()` la regenere).
- Tené dos usuarios a mano: **admin / admin123** y un conductor que crees en RG-01.
- Para los casos de dos conductores (CO-05) abrí dos instancias de la app.
- Resultado: marcá **OK** o **FALLA** y anotá lo que viste en "Observado".

---

## 1. Login

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| LG-01 | Ingresar `admin` / `admin123` → Ingresar | Va a "Elegí un estacionamiento — Administrador" | | |
| LG-02 | Usuario correcto, contraseña incorrecta | Snack rojo "Usuario o contraseña incorrectos"; sigue en login | | |
| LG-03 | Usuario inexistente | Mismo snack rojo | | |
| LG-04 | Dejar ambos campos vacíos → Ingresar | Snack rojo de error (no debe romperse la app) | | |
| LG-05 | Escribir ` admin ` (con espacios) + contraseña correcta | Ingresa (el usuario se recorta con `strip`) | | |
| LG-06 | Contraseña con espacios al final (`admin123 `) | Debe **fallar** (la contraseña no se recorta) | | |
| LG-07 | Usuario `' OR '1'='1' --` y cualquier clave | Snack rojo; no ingresa | | |
| LG-08 | Ícono del ojo en contraseña | Muestra/oculta el texto | | |
| LG-09 | Escribir credenciales y presionar **Enter** | Observación: hoy no hay `on_submit`; anotar si ingresa o no | | |

## 2. Registro

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| RG-01 | "Crear cuenta de conductor" → completar los 3 campos → Registrarme | Snack verde y vuelve al login; puede ingresar como conductor | | |
| RG-02 | Dejar algún campo vacío | Snack rojo "Completá todos los campos" | | |
| RG-03 | Registrar un usuario ya existente | Snack rojo con el mensaje de la base; no vuelve al login | | |
| RG-04 | Poner solo espacios (`   `) en **Usuario** | Debe rechazarse. **Posible bug:** la UI chequea "vacío" antes del `strip()`, así que puede llegar `""` a la base | | |
| RG-05 | Poner solo espacios en **Nombre** | Ídem RG-04 | | |
| RG-06 | Registrar `juan` y luego `Juan` | Anotar si los trata como distintos (decidir si es lo deseado) | | |
| RG-07 | "Volver al login" | Vuelve sin crear nada | | |
| RG-08 | Confirmar que el registro nunca permite elegir rol admin | No hay selector de rol; el usuario creado es conductor | | |

## 3. Navegación y control de acceso

> Las rutas se pueden tipear en la URL solo si corrés la app en modo web (`flet run --web`).

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| RT-01 | Sin sesión, abrir `/admin` | Muestra el login | | |
| RT-02 | Sin sesión, abrir `/estacionamientos` y `/conductor` | Muestra el login | | |
| RT-03 | Como conductor, abrir `/admin` | Muestra el login (no el panel admin) | | |
| RT-04 | Como admin, abrir `/conductor` | Muestra el login (no el panel conductor) | | |
| RT-05 | Abrir una ruta inventada (`/xyz`) | Muestra el login | | |
| RT-06 | Cerrar sesión desde cualquier vista | Vuelve al login; al ingresar con otro usuario no quedan datos del anterior | | |
| RT-07 | Tras cerrar sesión, usar "atrás" del navegador | No debe mostrar datos de la sesión anterior | | |
| RT-08 | Flecha "volver" en panel admin/conductor | Vuelve a la lista de estacionamientos y conserva la sesión | | |
| RT-09 | Cerrar y reabrir la app | Pide login de nuevo (la sesión no persiste) | | |

## 4. Lista de estacionamientos

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| ES-01 | Ver la lista | Cada tarjeta muestra nombre, dirección y "X de Y lugares disponibles" | | |
| ES-02 | Estacionamiento sin dirección | Muestra "Sin dirección cargada" | | |
| ES-03 | Estacionamiento con 0 disponibles | Texto en rojo; con ≥1 disponible, en verde | | |
| ES-04 | Clic en una tarjeta como admin | Abre `/admin` de ese estacionamiento | | |
| ES-05 | Clic en una tarjeta como conductor | Abre `/conductor` de ese estacionamiento | | |
| ES-06 | Volver a la lista tras reservar/cancelar | Los contadores reflejan el cambio | | |
| ES-07 | Base sin estacionamientos | Mensaje "No hay estacionamientos cargados todavía." | | |

## 5. Panel administrador

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| AD-01 | Número `901`, tipo `auto`, precio `100` → Guardar | Snack verde; aparece "Lugar #901 — auto, $100.00 / hora" y el formulario se limpia | | |
| AD-02 | Dejar algún campo vacío → Guardar | Snack rojo "Completá número, tipo y precio" | | |
| AD-03 | Número `abc` o precio `xyz` | Snack rojo "Número y precio deben ser numéricos" | | |
| AD-04 | Precio con coma (`12,5`) | Hoy da error de "numéricos". **Probable queja de usuarios en Argentina**: decidir si se acepta la coma | | |
| AD-05 | Número duplicado en el mismo estacionamiento | Debe rechazarse con mensaje | | |
| AD-06 | Precio `-50` y precio `0` | Deberían rechazarse | | |
| AD-07 | Número `0` y `-3` | Deberían rechazarse | | |
| AD-08 | Precio `nan` o `inf` | Deberían rechazarse (Python los convierte a `float` sin error) | | |
| AD-09 | Número decimal (`3.5`) | Snack rojo "deben ser numéricos" (`int()` falla) | | |
| AD-10 | Lápiz en un lugar | El formulario se llena con sus datos | | |
| AD-11 | Editar precio y guardar | Se actualiza la fila y se limpia el formulario | | |
| AD-12 | Editar y luego "Cancelar edición" | Formulario limpio; al guardar de nuevo **crea** un lugar nuevo (no edita) | | |
| AD-13 | Papelera en un lugar | Snack "Lugar #N eliminado" y desaparece de la lista | | |
| AD-14 | **Bug conocido:** un conductor reserva el lugar #901; el admin lo edita (p. ej. cambia el precio) y guarda | El lugar debería seguir **Ocupado**. El código llama `modificar_lugar(..., True)` siempre, así que probablemente pasa a **Disponible** y se podría reservar dos veces | | |
| AD-15 | Borrar un lugar con reserva activa | Definir comportamiento esperado; verificar que "Mis reservas" del conductor no se rompa | | |
| AD-16 | Admin en el estacionamiento A | Solo ve lugares de A, no los de B | | |
| AD-17 | Lista vacía | Mensaje "No hay lugares cargados todavía." | | |

**Arreglo sugerido para AD-14:** guardar el estado actual al editar y reenviarlo.

```python
editando_id = {"id": None, "disponible": True}
# en cargar_para_editar:  editando_id["disponible"] = bool(lugar["disponible"])
# en guardar:             db.modificar_lugar(editando_id["id"], numero, tipo_dropdown.value, precio, editando_id["disponible"])
# en limpiar_formulario:  editando_id["disponible"] = True
```

## 6. Panel conductor

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| CO-01 | Entrar a un estacionamiento con lugares libres | Lista solo los disponibles, con número, tipo y precio | | |
| CO-02 | Filtrar por `auto` → Buscar | Solo lugares tipo auto | | |
| CO-03 | Filtro sin resultados | "No hay lugares disponibles con ese filtro." | | |
| CO-04 | Volver a `todos` → Buscar | Vuelven todos los disponibles | | |
| CO-05 | **Concurrencia:** con dos conductores (dos ventanas) tener abierta la misma lista y reservar el mismo lugar | El segundo recibe snack rojo; el lugar no queda reservado dos veces | | |
| CO-06 | Reservar un lugar | Snack verde; el lugar sale de "disponibles" y aparece en "Mis reservas" como **Activa** (verde) | | |
| CO-07 | Cancelar una reserva activa | Snack; el estado pasa a **Cancelada** (rojo), sin botón Cancelar, y el lugar vuelve a estar disponible | | |
| CO-08 | Reservas en estacionamientos distintos | "Mis reservas" muestra todas, cada una con el nombre de su estacionamiento | | |
| CO-09 | Un conductor nuevo | "Todavía no hiciste ninguna reserva." | | |
| CO-10 | El filtro elegido, después de reservar | Anotar si se conserva o se resetea | | |
| CO-11 | Un conductor no ve reservas de otro | "Mis reservas" solo muestra las propias | | |

## 7. Persistencia y seguridad

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| PE-01 | Crear datos, cerrar la app y reabrirla | Usuarios, lugares y reservas siguen ahí | | |
| PE-02 | Abrir el `.db` con DB Browser for SQLite y mirar la tabla de usuarios | Las contraseñas deben estar **hasheadas**, no legibles | | |
| SG-01 | Mirar la pantalla de login | Hoy muestra el usuario/clave del admin. Aceptable en desarrollo; **quitar antes de entregar/producción** | | |
| SG-02 | Cambiar la contraseña del admin por defecto | Hoy no hay pantalla para hacerlo: anotar como mejora | | |

## 8. Interfaz

| ID | Pasos | Resultado esperado | Estado | Observado |
|----|-------|--------------------|--------|-----------|
| UI-01 | Achicar/agrandar la ventana | Sin textos cortados ni solapados; la lista hace scroll | | |
| UI-02 | Nombre de estacionamiento o usuario muy largo | No rompe el AppBar ni las tarjetas | | |
| UI-03 | Muchos lugares (50+) | La lista hace scroll y sigue fluida | | |
| UI-04 | Tildes, eñes y emojis en nombre/usuario | Se guardan y muestran bien | | |

---

## Registro de fallas encontradas

| # | ID del caso | Descripción | Severidad (alta/media/baja) | Estado |
|---|-------------|-------------|-----------------------------|--------|
| 1 | | | | |
