# 🚀 Verificador de Notas UNETI

¡Mantente al tanto de tus calificaciones de la UNETI con notificaciones automáticas!

## 📝 Descripción

Este proyecto es una herramienta útil para los estudiantes de la UNETI que desean monitorear sus calificaciones. El programa se conecta a tu cuenta de la universidad y verifica si hay cambios en tus notas con un sistema de instalación completamente renovado y almacenamiento seguro de credenciales.

## ✨ Características principales

- **Monitoreo Automático**: Verifica tu cuenta cada 30 minutos (configurable), en el horario de tu elección.
- **Notificaciones Instantáneas**: Recibe notificaciones en tu escritorio cuando una calificación cambie o se publique una nueva.
- **Almacenamiento Seguro**: Las credenciales se almacenan de forma segura usando el gestor de credenciales de Windows.
- **Ejecución Silenciosa**: Las tareas automáticas se ejecutan en segundo plano sin mostrar ventanas.
- **Instalación Inteligente**: Proceso de configuración completamente automatizado con verificación de dependencias.
- **Historial Detallado**: Mantiene un registro de todos los cambios de notas en `grade_history.txt`.

## ⚙️ Instalación y Configuración

### 📅 Descarga:

1. Ve a la página de [Releases](https://github.com/unibend/verificador-de-notas/releases) y descarga el archivo `.zip` de la última versión.
2. Extrae todo el contenido del archivo `.zip` en una carpeta de tu elección.

⚡ **Importante:** Una vez hayas configurado el verificador, **no debes mover la carpeta ni sus archivos a otra ubicación**, ya que esto hará que dejen de funcionar correctamente la automatización y las rutas de configuración.

### 🚀 Instalación Automática (Recomendada):

#### Para Windows 10/11:

1. **Abre PowerShell como administrador** (recomendado para automatización completa):

   - Busca "PowerShell" en el menú Inicio
   - Haz clic derecho y selecciona "Ejecutar como administrador"

2. **Navega a la carpeta del proyecto**. Algunas formas de hacerlo:

   - Si ya estás dentro del explorador de archivos, mantén presionada la tecla Shift, haz clic derecho en la carpeta y selecciona "Copiar como ruta". Luego en PowerShell escribe:
     ```powershell
     cd "Pega-aquí-la-ruta"
     ```
     Asegúrate de mantener las comillas.
   - O simplemente arrastra la carpeta dentro de la ventana de PowerShell después de escribir `cd `.

3. **Ejecuta el lanzador inteligente**:

   ```powershell
   python run.py
   ```

4. **Sigue las instrucciones en pantalla**:

   - El programa verificará automáticamente las dependencias
   - Te guiará a través de la configuración paso a paso
   - Instalará las dependencias necesarias si no están presentes
   - Configurará la automatización (si tienes permisos de administrador)

#### Opciones de Instalación:

**Con permisos de administrador (recomendado):**

- ✅ Instalación automática de dependencias
- ✅ Configuración completa de tareas programadas
- ✅ Ejecución automática en segundo plano
- ✅ Modo silencioso (sin ventanas)

**Sin permisos de administrador:**

- ✅ Instalación manual de dependencias
- ✅ Configuración básica
- ⚠️ Ejecución manual únicamente
- ⚠️ Sin automatización

## 🛡️ Seguridad:

- **Almacenamiento Seguro**: Tu token de API se almacena de forma segura en el gestor de credenciales de Windows (keyring)
- **Cifrado Automático**: Windows cifra automáticamente las credenciales almacenadas
- **Sin Archivos de Texto Plano**: No se guardan credenciales en archivos de texto plano
- **Gestión Centralizada**: Todas las credenciales se gestionan desde el Administrador de credenciales de Windows

## 💡 Funcionamiento Interno

### 🔐 Gestión de Credenciales:

1. **Configuración Inicial**: El `configurador.py` solicita tus credenciales UNETI
2. **Obtención de Token**: Se conecta a los servidores Moodle para obtener un token de API
3. **Almacenamiento Seguro**: El token se almacena en el gestor de credenciales de Windows usando keyring
4. **Archivo de Configuración**: Se crea un `config.json` con información básica (sin credenciales)

### 📊 Verificación de Notas:

- **Conexión Segura**: Utiliza el token almacenado para conectarse a UNETI
- **Comparación Inteligente**: Compara las notas actuales con las anteriores, que están almacenadas en `previous_grades.json`
- **Notificaciones Contextuales**: Muestra notificaciones detalladas sobre los cambios
- **Historial Completo**: Registra todos los cambios en `grade_history.txt`

### ⏰ Automatización:

- **Tareas Programadas**: Crea tareas en el Programador de tareas de Windows
- **Horario Personalizable**: Configura el horario de funcionamiento (por defecto: 8:00 AM - 10:00 PM)
- **Intervalos Ajustables**: Elige entre 15, 30, 45 o 60 minutos
- **Ejecución Silenciosa**: Las tareas automáticas no muestran ventanas

### 🔇 Modo Silencioso:

- **Ejecución en Segundo Plano**: Las tareas automáticas no muestran ventanas
- **Notificaciones Únicamente**: Solo verás las notificaciones cuando haya cambios
- **Dos Archivos Batch**: `verificador_notas.bat` (manual con ventana) y `verificador_notas_silent.bat` (automático sin ventana)

## 📁 Archivos Creados

Después de la instalación, encontrarás estos archivos:

```
📂 Carpeta del verificador/
📄 config.json - Configuración básica (sin credenciales)
📄 previous_grades.json - Datos de notas anteriores
📄 grade_history.txt - Historial completo de cambios
📄 verificador_notas.bat - Ejecución manual (con ventana)
📄 verificador_notas_silent.bat - Ejecución automática (silenciosa)
🐍 run.py - Lanzador inteligente
🐍 configurador.py - Configurador del sistema
🐍 grade_checker.py - Verificador principal
🐍 uninstall.py - Desinstalador
```

## 🔧 Uso Diario

### 🚀 Ejecución Manual:

```bash
python run.py
```

#### Usando el archivo batch

Haz doble click en `verificador_notas.bat`

### 🔄 Reconfiguración:

```bash
python run.py
# Seleccionar opción 2: Configurar/Reconfigurar
```

### 🗑️ Desinstalación:

```bash
python run.py
# Seleccionar opción 4: Desinstalar
```

Alternativemente, puedes ejecutar el archivo `uninstall.py` directamente, con permisos de administrador.

## 🛠️ Dependencias

El sistema instalará automáticamente estas dependencias:

- **requests**: Para conexiones HTTP a los servidores UNETI
- **keyring**: Para almacenamiento seguro de credenciales

## 🔒 Seguridad y Privacidad

### ✅ Características de Seguridad:

- **Cifrado por Windows**: Las credenciales se cifran automáticamente
- **Gestión Centralizada**: Acceso a credenciales desde el Administrador de credenciales
- **Sin Archivos Sensibles**: No se almacenan credenciales en archivos de texto
- **Conexiones Seguras**: Todas las conexiones usan HTTPS con verificación SSL

### 🔑 Gestión de Credenciales:

- **Ubicación**: `Panel de Control > Administrador de credenciales > Credenciales de Windows`
- **Servicio**: Buscar "UNETI-Grade-Checker"
- **Eliminación**: Eliminar directamente desde el Administrador de credenciales
- **Actualización**: Ejecutar el configurador nuevamente

### ⚠️ Recomendaciones de Seguridad:

- **Protege tu Carpeta**: Mantén los archivos en una ubicación segura
- **Cambio de Contraseña**: Si cambias tu contraseña UNETI, reconfigura el verificador
- **Acceso Limitado**: Solo tú debes tener acceso a la carpeta del verificador

## 📱 Notificaciones

Recibirás notificaciones automáticas cuando:

- 🆕 Se publique una nueva calificación
- 🔄 Se actualice una calificación existente
- 📚 Se agregue una nueva materia
- 📊 Se modifique el promedio de una materia

## 🤝 Soporte

Si encuentras problemas:

- **Issues en GitHub**: Utiliza la sección de [Issues](https://github.com/unibend/verificador-de-notas/issues)
- **Contacto directo**: [cyclic-pogo-shack@duck.com](mailto\:cyclic-pogo-shack@duck.com)

---

**Nota**: Este proyecto está en constante desarrollo. Las nuevas versiones pueden incluir funcionalidades adicionales y mejoras de seguridad.

