# 🚀 Verificador de Notas UNETI

¡Mantente al tanto de tus calificaciones de la UNETI con notificaciones automáticas!

## 📝 Descripción

Este proyecto es una herramienta útil para los estudiantes de la UNETI que desean monitorear sus calificaciones. El programa se conecta a tu cuenta de la universidad y verifica si hay cambios en tus notas.

## ✨ Características principales

- **Monitoreo Automático**: Verifica tu cuenta cada 30 minutos, desde las 8:00 AM hasta las 10:00 PM.
- **Notificaciones Instantáneas**: Recibe una notificación en tu escritorio (a través de una ventana de diálogo en Windows, o notificaciones nativas en macOS/Linux) cada vez que una calificación cambie o se publique una nueva.
- **Historial Detallado**: Mantiene un registro de todos los cambios de notas en un archivo de texto (`grade_history.txt`) para que puedas revisarlos en cualquier momento.
- **Fácil de Usar**: Un proceso de configuración guiado te ayudará a ponerlo en marcha rápidamente.

## ⚙️ Cómo Usar

Sigue estos sencillos pasos para instalar y ejecutar el verificador de notas:

### Descarga:
1. Ve a la página de [Releases](https://github.com/unibend/verificador-de-notas/releases) y descarga el archivo `.zip` de la última versión.
2. Extrae todo el contenido del archivo `.zip` en una carpeta de tu elección.

### Ejecución (Windows):

#### Opción Recomendada (con automatización):
1. Abre el menú Inicio y busca "PowerShell".
2. Haz clic derecho en "Windows PowerShell" y selecciona "Ejecutar como administrador".
3. En la ventana de PowerShell, navega a la carpeta del proyecto:
   - Primero, encuentra la ruta completa de la carpeta donde extrajiste los archivos (puedes hacerlo abriendo la carpeta en el Explorador de Archivos y copiando la ruta desde la barra de direcciones).
   - Luego escribe en PowerShell: `cd "ruta\completa\a\la\carpeta"` (reemplaza con tu ruta real, manteniendo las comillas).
   - Ejemplo: `cd "C:\Users\TuUsuario\Documents\verificador-de-notas"`
4. Una vez en la carpeta correcta, escribe `python run.py` y presiona Enter.
5. El programa `setup.py` se iniciará automáticamente. Sigue las instrucciones en pantalla para configurar la automatización.

#### Opción Alternativa (sin administrador):
1. Abre la carpeta donde extrajiste los archivos.
2. Haz clic derecho en un espacio vacío mientras mantienes presionada la tecla Shift.
3. Selecciona "Abrir la ventana de PowerShell aquí".
4. Escribe `python run.py` y presiona Enter.
5. Sigue las instrucciones en pantalla. Nota: sin permisos de administrador, el programa no podrá configurar la ejecución automática.

#### Opción con Terminal Windows (Windows 10/11):
1. Abre la Terminal Windows (puedes buscarla en el menú Inicio).
2. Navega a la carpeta del proyecto usando: `cd "ruta\completa\a\la\carpeta"`
3. Ejecuta: `python run.py`
4. Sigue las instrucciones en pantalla.

#### Opción Manual:
Después de la instalación inicial, puedes ejecutar la aplicación manualmente en cualquier momento haciendo doble clic en el archivo `verificador_notas.bat` (este archivo se crea durante la instalación).

## 💡 Funcionamiento Interno (Diseño)

El programa está diseñado para ser lo más sencillo y eficiente posible:

- **Credenciales y Token**: Al iniciar por primera vez, el `configurador.py` te pedirá tus credenciales de la UNETI (usuario y contraseña). Utilizará estas credenciales para obtener un "token de aplicación móvil" de los servidores de Moodle de la UNETI. Este token es esencial, ya que permite al programa acceder a tus datos académicos sin necesidad de que ingreses tu contraseña cada vez.

- **Almacenamiento del Token**: El token obtenido se guarda en texto plano dentro del archivo `grade_checker.py`. Este archivo es el corazón del verificador.

- **Verificación Periódica**: Cada 30 minutos (si la automatización está configurada), el `grade_checker.py` se ejecuta:
  - Se conecta a los servidores de la UNETI usando tu token.
  - Descarga tus calificaciones actuales para todas tus asignaturas.
  - Compara estas calificaciones con las que guardó la última vez en el archivo `previous_grades.json`.

- **Notificaciones**: Si detecta algún cambio (por ejemplo, una nueva nota publicada, una nota existente actualizada, o una nueva materia inscrita), el programa te enviará una notificación a tu escritorio. En Windows, esto aparecerá como una ventana de diálogo informativa.

- **Registro de Historial**: Todos los cambios detectados, así como los resúmenes de verificación, se registran en el archivo `grade_history.txt`, proporcionando un historial completo de tus calificaciones.

## ⚠️ Seguridad

Actualmente, tu token de API se almacena en texto plano dentro del archivo `grade_checker.py`. Esto significa que cualquiera que tenga acceso a tus archivos podría potencialmente acceder a tus datos académicos de la UNETI.

**Recomendaciones de seguridad**:
- **Protege tus archivos**: Asegúrate de que los archivos del verificador (`grade_checker.py`, `previous_grades.json`, `grade_history.txt`, `verificador_notas.bat`, etc.) estén almacenados en un lugar seguro en tu computadora, donde solo tú tengas acceso.
- **No compartas**: Evita compartir esta carpeta o sus contenidos con otras personas.
- **Cambio de contraseña**: Si alguna vez sospechas que tu token ha sido comprometido, cambia inmediatamente tu contraseña en el campus virtual de la UNETI. Esto invalidará el token anterior.

Estoy considerando añadir medidas de seguridad adicionales en el futuro para proteger mejor el token.

## 🤝 Soporte

Este es un proyecto personal creado para mí y algunos compañeros. Si encuentras algún problema, por favor:

- **Abre un "Issue" en GitHub**: Utiliza la sección de "Issues" de este repositorio para reportar errores o sugerir mejoras.
- **Contáctame Directamente**: Si el problema es urgente o prefieres un contacto más directo, puedes contactarme a través de [cyclic-pogo-shack@duck.com](mailto:cyclic-pogo-shack@duck.com).

Agradezco cualquier comentario o contribución para mejorar este verificador.
