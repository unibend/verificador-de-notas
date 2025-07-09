import requests
import json
import os
import sys
import subprocess
import shutil
from datetime import datetime
import platform
import re
import argparse

def print_banner():
    """Mostrar banner del programa"""
    print("=" * 60)
    print("🎓 CONFIGURADOR DE VERIFICADOR DE NOTAS UNETI")
    print("=" * 60)
    print("Este programa te ayudará a configurar el verificador automático")
    print("de notas para que recibas notificaciones cuando cambien tus calificaciones.")
    print("=" * 60)
    print()

def validate_username(username):
    """Validar formato de nombre de usuario"""
    if not username:
        return False, "El nombre de usuario no puede estar vacío"
    
    # Permitir solo números, letras y algunos caracteres especiales comunes
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos"
    
    if len(username) < 3 or len(username) > 50:
        return False, "El nombre de usuario debe tener entre 3 y 50 caracteres"
    
    return True, ""

def validate_time(time_str):
    """Validar formato de hora HH:MM"""
    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
        return False, "Formato de hora inválido. Use HH:MM (ejemplo: 08:30)"
    
    hour, minute = map(int, time_str.split(':'))
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return False, "Hora inválida. Use formato 24 horas (00:00 a 23:59)"
    
    return True, ""

def get_time_schedule():
    """Obtener horario de funcionamiento del usuario"""
    print("\n⏰ CONFIGURACIÓN DE HORARIO")
    print("-" * 40)
    print("Configura el horario en que quieres que funcione el verificador.")
    print("El verificador se ejecutará cada 30 minutos durante todo el día.")
    print()
    
    # Hora de inicio
    while True:
        start_time = input("🌅 Hora de inicio (formato HH:MM, ejemplo: 08:00): ").strip()
        
        valid, error_msg = validate_time(start_time)
        if valid:
            break
        else:
            print(f"❌ {error_msg}")
    
    # Hora de fin
    while True:
        end_time = input("🌙 Hora de fin (formato HH:MM, ejemplo: 22:00): ").strip()
        
        valid, error_msg = validate_time(end_time)
        if not valid:
            print(f"❌ {error_msg}")
            continue
        
        # Validar que la hora de fin sea posterior a la de inicio
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))
        
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        if end_minutes <= start_minutes:
            print("❌ La hora de fin debe ser posterior a la hora de inicio")
            continue
        
        # Validar que haya al menos 30 minutos de diferencia
        if end_minutes - start_minutes < 30:
            print("❌ Debe haber al menos 30 minutos entre la hora de inicio y fin")
            continue
        
        break
    
    # Intervalo de ejecución
    print("\n📅 INTERVALO DE EJECUCIÓN")
    print("¿Cada cuántos minutos quieres que se ejecute el verificador?")
    print("Opciones disponibles: 15, 30, 45, 60 minutos")
    
    while True:
        interval_input = input("⏱️  Intervalo en minutos (recomendado: 30): ").strip()
        
        if not interval_input:
            interval = 30
            break
        
        try:
            interval = int(interval_input)
            if interval not in [15, 30, 45, 60]:
                print("❌ Intervalo inválido. Opciones: 15, 30, 45, 60 minutos")
                continue
            break
        except ValueError:
            print("❌ Ingresa un número válido")
    
    print(f"\n✅ Horario configurado:")
    print(f"   🌅 Inicio: {start_time}")
    print(f"   🌙 Fin: {end_time}")
    print(f"   ⏱️  Intervalo: cada {interval} minutos")
    
    return start_time, end_time, interval

def get_user_credentials():
    """Obtener credenciales del usuario"""
    print("📝 PASO 1: Configuración de credenciales")
    print("-" * 40)
    
    while True:
        username = input("👤 Ingresa tu nombre de usuario (Por lo general es tu número de cédula, solo el número): ").strip()
        
        valid, error_msg = validate_username(username)
        if valid:
            break
        else:
            print(f"❌ {error_msg}")
            print("Por favor, intenta de nuevo.")
    
    # Importar getpass para ocultar la contraseña
    import getpass
    print("\n⚠️  IMPORTANTE: Al escribir tu contraseña, NO VERÁS los caracteres en pantalla.")
    print("Esto es normal y es una medida de seguridad. Tu contraseña se está escribiendo,")
    print("aunque no puedas verla. Escribe tu contraseña completa y presiona Enter.")
    print()
    
    while True:
        password = getpass.getpass("🔒 Ingresa tu contraseña (no verás los caracteres): ").strip()
        
        if not password:
            print("❌ La contraseña no puede estar vacía.")
            print("Recuerda: aunque no veas los caracteres, tu contraseña se está escribiendo.")
            continue
        
        if len(password) < 4:
            print("❌ La contraseña debe tener al menos 4 caracteres.")
            continue
        
        break
    
    return username, password

def get_api_token(username, password):
    """Obtener token de API desde Moodle usando POST request"""
    print("\n🔄 PASO 2: Obteniendo token de API...")
    print("-" * 40)
    
    url = "https://www.uneti.edu.ve/campus/login/token.php"
    
    # Datos para enviar via POST (más seguro que GET)
    payload = {
        'username': username,
        'password': password,
        'service': 'moodle_mobile_app'
    }
    
    try:
        print("⏳ Conectando con el servidor de UNETI...")
        
        # Usar POST request con verificación SSL
        response = requests.post(
            url, 
            data=payload, 
            timeout=30,
            verify=True,  # Verificar certificado SSL
            headers={
                'User-Agent': 'UNETI-Grade-Checker/1.0'
            }
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'token' in data:
            print("✅ Token obtenido exitosamente!")
            return data['token']
        elif 'error' in data:
            print(f"❌ Error del servidor: {data['error']}")
            return None
        else:
            print("❌ Respuesta inesperada del servidor")
            print(f"Respuesta: {data}")
            return None
            
    except requests.exceptions.SSLError:
        print("❌ Error de certificado SSL. Esto podría indicar un problema de seguridad.")
        print("No se pudo verificar la identidad del servidor.")
        return None
    except requests.exceptions.Timeout:
        print("❌ Tiempo de espera agotado. Verifica tu conexión a internet.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None
    except json.JSONDecodeError:
        print("❌ Error al procesar la respuesta del servidor")
        return None

def get_script_directory():
    """Obtener el directorio donde está ubicado el script"""
    # Si el script está siendo ejecutado como .exe compilado
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def store_api_token(api_token, username):
    """Almacenar el token de API en el gestor de credenciales del sistema"""
    print("\n🔧 PASO 3: Almacenando token de API en el gestor de credenciales...")
    print("-" * 40)
    
    try:
        import keyring
        
        # Información de seguridad actualizada
        print("🔒 INFORMACIÓN DE SEGURIDAD:")
        print("Tu token de API se almacenará de forma segura en el gestor de credenciales del sistema.")
        print("Esto es más seguro que almacenarlo en texto plano.")
        print("El token se cifrará automáticamente por Windows.")
        print()
        
        # Confirmación del usuario
        while True:
            response = input("¿Continuar con el almacenamiento seguro del token? (s/n): ").strip().lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                break
            elif response in ['n', 'no']:
                print("❌ Configuración cancelada por el usuario.")
                return False
            else:
                print("Por favor, responde 's' para sí o 'n' para no.")
        
        # Almacenar el token en el keyring
        service_name = "UNETI-Grade-Checker"
        keyring.set_password(service_name, username, api_token)
        
        print("✅ Token almacenado exitosamente en el gestor de credenciales del sistema")
        print(f"🔑 Servicio: {service_name}")
        print(f"👤 Usuario: {username}")
        print("🔒 El token está ahora cifrado y protegido por Windows.")
        return True
        
    except ImportError:
        print("❌ Error: La librería 'keyring' no está instalada.")
        print("Instálala con: pip install keyring")
        return False
    except Exception as e:
        print(f"❌ Error al almacenar el token: {e}")
        return False

def save_username_config(username):
    """Save username to config file for later credential management"""
    try:
        script_dir = get_script_directory()
        config_path = os.path.join(script_dir, "config.json")
        
        config = {
            "username": username,
            "configured_date": datetime.now().isoformat(),
            "service_name": "UNETI-Grade-Checker"
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuración guardada en: config.json")
        return True
        
    except Exception as e:
        print(f"⚠️ Error al guardar configuración: {e}")
        return False

def ask_for_automation():
    """Preguntar si quiere automatización"""
    print("\n⚙️ PASO 4: Configuración de automatización")
    print("-" * 40)
    print("¿Quieres que el verificador se ejecute automáticamente cada 30 minutos?")
    print("Esto te permitirá recibir notificaciones cuando cambien tus notas.")
    print()
    
    while True:
        response = input("👉 Configurar automatización? (s/n): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Por favor, responde 's' para sí o 'n' para no.")

def create_batch_files():
    """Crear archivos batch para ejecutar el script manual y automáticamente"""
    try:
        # Obtener rutas absolutas y validarlas
        script_dir = get_script_directory()
        python_exe = sys.executable
        script_path = os.path.join(script_dir, "grade_checker.py")
        
        # Archivos batch
        manual_batch_path = os.path.join(script_dir, "verificador_notas.bat")
        silent_batch_path = os.path.join(script_dir, "verificador_notas_silent.bat")
        
        print(f"📂 Creando archivos batch en: {script_dir}")
        
        # Validar que las rutas son seguras
        if not os.path.exists(python_exe):
            print(f"❌ No se encontró Python en: {python_exe}")
            return None, None
        
        if not os.path.exists(script_path):
            print(f"❌ No se encontró el script en: {script_path}")
            return None, None
        
        # Crear contenido del archivo batch manual (con pausa)
        manual_batch_content = f'''@echo off
cd /d "{script_dir}"
echo Ejecutando verificador de notas...
echo.
"{python_exe}" "{script_path}"
echo.
echo Verificacion completada.
pause
'''
        
        # Crear contenido del archivo batch silencioso (sin ventana)
        silent_batch_content = f'''@echo off
cd /d "{script_dir}"
"{python_exe}" "{script_path}" > nul 2>&1
'''
        
        # Escribir archivo batch manual
        with open(manual_batch_path, 'w', encoding='utf-8') as f:
            f.write(manual_batch_content)
        
        # Escribir archivo batch silencioso
        with open(silent_batch_path, 'w', encoding='utf-8') as f:
            f.write(silent_batch_content)
        
        print(f"✅ Archivo batch manual creado: {manual_batch_path}")
        print(f"✅ Archivo batch silencioso creado: {silent_batch_path}")
        
        return manual_batch_path, silent_batch_path
        
    except Exception as e:
        print(f"❌ Error al crear archivos batch: {e}")
        return None, None

def add_to_task_scheduler(silent_batch_path, start_time, end_time, interval):
    """Agregar tareas al programador de tareas de Windows usando el archivo batch silencioso"""
    print("\n📅 Configurando tareas programadas...")
    print("-" * 40)
    
    try:
        # Nombres de las tareas
        daily_task_name = "VerificadorNotasUNETI_Daily"
        interval_task_name = "VerificadorNotasUNETI_Interval"
        
        # Validar que el archivo batch existe
        if not os.path.exists(silent_batch_path):
            print(f"❌ El archivo batch silencioso no existe: {silent_batch_path}")
            return False
        
        print("⏳ Creando tarea programada diaria...")
        
        # Comando para crear la tarea diaria (ejecuta sin mostrar ventana)
        daily_task_cmd = [
            'schtasks', '/create',
            '/tn', daily_task_name,
            '/tr', f'"{silent_batch_path}"',
            '/sc', 'daily',
            '/st', start_time,
            '/ru', 'SYSTEM',  # Ejecutar como sistema para evitar ventanas
            '/rl', 'HIGHEST',  # Nivel más alto para evitar problemas de permisos
            '/f'  # Forzar creación (sobrescribir si existe)
        ]
        
        result = subprocess.run(daily_task_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Error al crear la tarea programada diaria")
            print(f"Error: {result.stderr}")
            return False
        
        print("✅ Tarea diaria creada exitosamente!")
        
        print("⏳ Creando tarea programada por intervalos...")
        
        # Comando para crear la tarea que se ejecuta cada intervalo especificado
        interval_task_cmd = [
            'schtasks', '/create',
            '/tn', interval_task_name,
            '/tr', f'"{silent_batch_path}"',
            '/sc', 'minute',
            '/mo', str(interval),
            '/st', start_time,
            '/et', end_time,
            '/ru', 'SYSTEM',  # Ejecutar como sistema
            '/rl', 'HIGHEST',  # Nivel más alto
            '/f'  # Forzar creación
        ]
        
        result = subprocess.run(interval_task_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Error al crear la tarea programada por intervalos")
            print(f"Error: {result.stderr}")
            # Eliminar la tarea diaria si falló la de intervalos
            subprocess.run(['schtasks', '/delete', '/tn', daily_task_name, '/f'], 
                          capture_output=True, text=True)
            return False
        
        print("✅ Tarea por intervalos creada exitosamente!")
        print(f"📋 Tareas creadas:")
        print(f"   • {daily_task_name} - Se ejecuta diariamente a las {start_time} (silenciosamente)")
        print(f"   • {interval_task_name} - Se ejecuta cada {interval} minutos entre {start_time} y {end_time} (silenciosamente)")
        print("\n🔇 MODO SILENCIOSO:")
        print("• Las tareas programadas se ejecutarán en segundo plano sin mostrar ventanas")
        print("• Solo verás las notificaciones cuando haya cambios en las notas")
        print("• Para ver el progreso manualmente, usa 'verificador_notas.bat'")
        print("\nPara gestionar las tareas puedes:")
        print("• Abrir 'Programador de tareas' en Windows")
        print(f"• Buscar las tareas '{daily_task_name}' y '{interval_task_name}'")
        print("• Desde ahí puedes habilitarlas, deshabilitarlas o eliminarlas")
        return True
        
    except Exception as e:
        print(f"❌ Error al configurar las tareas programadas: {e}")
        return False

def run_grade_checker():
    """Ejecutar el verificador de notas por primera vez"""
    print("\n🚀 PASO 5: Ejecutando verificador por primera vez...")
    print("-" * 40)
    
    script_dir = get_script_directory()
    script_path = os.path.join(script_dir, "grade_checker.py")
    
    try:
        print("⏳ Ejecutando verificador de notas...")
        print("(Esto puede tomar unos minutos la primera vez)")
        print()
        
        # Cambiar al directorio del script antes de ejecutar
        original_dir = os.getcwd()
        os.chdir(script_dir)
        
        # Ejecutar el script con encoding='utf-8' and errors='replace' for stdout/stderr
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, 
                              text=True, 
                              encoding='utf-8',
                              errors='replace')
        
        # Restaurar directorio original
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print("✅ Verificador ejecutado exitosamente!")
            print("\nSalida del verificador:")
            print("-" * 30)
            print(result.stdout)
            return True
        else:
            print("❌ Error al ejecutar el verificador")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error al ejecutar el verificador: {e}")
        return False

def show_final_instructions(automation_enabled):
    """Mostrar instrucciones finales"""
    print("\n🎉 ¡CONFIGURACIÓN COMPLETADA!")
    print("=" * 60)
    print("El verificador de notas ha sido configurado correctamente.")
    print()
    print("📋 RESUMEN DE CONFIGURACIÓN:")
    print("• ✅ Token de API obtenido y almacenado de forma segura")
    print("• ✅ Credenciales guardadas en el gestor de credenciales del sistema")
    print("• ✅ Verificación inicial completada")
    if automation_enabled:
        print("• ✅ Tarea programada configurada (modo silencioso)")
        print("  - Se ejecutará automáticamente en segundo plano")
        print("  - No mostrará ventanas durante la ejecución automática")
    else:
        print("• ⚠️  Automatización omitida")
    print()
    print("🔒 INFORMACIÓN DE SEGURIDAD:")
    print("• Tu token de API está almacenado de forma segura en el gestor de credenciales")
    print("• El token está cifrado por Windows automáticamente")
    print("• No hay archivos con información sensible en texto plano")
    print("• Si cambias tu contraseña en UNETI, deberás reconfigurar el verificador")
    print()
    print("📝 ARCHIVOS CREADOS:")
    print("• verificador_notas.bat - Para ejecutar manualmente (muestra ventana)")
    print("• verificador_notas_silent.bat - Para ejecución automática (silencioso)")
    print("• previous_grades.json - Datos de notas anteriores")
    print("• grade_history.txt - Historial de cambios")
    print()
    print("🔔 NOTIFICACIONES:")
    print("Ahora recibirás notificaciones cuando:")
    print("• Recibas una nueva calificación")
    print("• Se actualice una calificación existente")
    print("• Se agregue una nueva materia")
    if automation_enabled:
        print("• Las notificaciones aparecerán automáticamente sin mostrar ventanas de comandos")
    print()
    print("⚙️ GESTIÓN:")
    print("• Para ejecutar manualmente: doble clic en 'verificador_notas.bat'")
    print("• Para ver el historial: abrir 'grade_history.txt'")
    if automation_enabled:
        print("• Para gestionar la automatización: buscar 'VerificadorNotasUNETI' en el Programador de tareas")
        print("• Para detener la automatización: deshabilitar la tarea en el Programador de tareas")
        print("• Las tareas programadas se ejecutan silenciosamente en segundo plano")
    else:
        print("• Para configurar automatización: ejecutar este configurador nuevamente")
    print()
    print("🔇 MODO SILENCIOSO:")
    if automation_enabled:
        print("• Las tareas automáticas no mostrarán ventanas de comandos")
        print("• Solo verás las notificaciones emergentes cuando haya cambios")
        print("• Para ver el progreso en tiempo real, ejecuta manualmente 'verificador_notas.bat'")
    else:
        print("• Disponible para cuando configures la automatización")
    print()
    print("🔑 GESTIÓN DE CREDENCIALES:")
    print("• Las credenciales se almacenan en el 'Administrador de credenciales' de Windows")
    print("• Para eliminar las credenciales: buscar 'UNETI-Grade-Checker' en el Administrador de credenciales")
    print("• Para reconfigurar: ejecutar este configurador nuevamente")
    print()
    print("🆘 SOPORTE:")
    print("Si tienes problemas, revisa los archivos de log o contacta al creador del script.")
    print("=" * 60)

def main():
    """Función principal"""
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Configurador de verificador de notas UNETI')
    parser.add_argument('--skip-automation', action='store_true', 
                       help='Omitir configuración de automatización')
    args = parser.parse_args()
    
    print_banner()
    
    # Verificar que keyring está instalado
    try:
        import keyring
        print("✅ Librería keyring detectada - Almacenamiento seguro disponible")
    except ImportError:
        print("❌ ERROR: La librería 'keyring' no está instalada.")
        print("Instálala con: pip install keyring")
        print("Esta librería es necesaria para el almacenamiento seguro de credenciales.")
        input("\nPresiona Enter para salir...")
        return
    
    # Advertencia de seguridad inicial actualizada
    print("\n🔒 INFORMACIÓN DE SEGURIDAD:")
    print("Este script almacenará tu token de API de forma segura en el gestor de credenciales del sistema.")
    print("El token será cifrado automáticamente por Windows y no se guardará en texto plano.")
    print("Esto proporciona mayor seguridad para tus credenciales.")
    print("=" * 60)
    print()
    
    # Verificar que estamos en Windows
    if platform.system() != "Windows":
        print("❌ Este configurador está diseñado para Windows únicamente.")
        print("Para otros sistemas operativos, configura manualmente.")
        return
    
    # Obtener directorio del script
    script_dir = get_script_directory()
    grade_checker_path = os.path.join(script_dir, "grade_checker.py")
    
    print(f"📂 Directorio de trabajo: {script_dir}")
    
    # Verificar que el script original existe
    if not os.path.exists(grade_checker_path):
        print(f"❌ No se encontró el archivo 'grade_checker.py' en {script_dir}")
        print("Asegúrate de que esté en la misma carpeta que este configurador.")
        input("\nPresiona Enter para salir...")
        return
    
    try:
        # Paso 1: Obtener credenciales
        username, password = get_user_credentials()
        if not username or not password:
            print("❌ No se pudieron obtener las credenciales.")
            input("\nPresiona Enter para salir...")
            return
        
        # Paso 2: Obtener token de API
        api_token = get_api_token(username, password)
        if not api_token:
            print("❌ No se pudo obtener el token de API.")
            print("Verifica tus credenciales y tu conexión a internet.")
            input("\nPresiona Enter para salir...")
            return
        
        # Paso 3: Almacenar token en keyring
        if not store_api_token(api_token, username):
            print("❌ No se pudo almacenar el token de API.")
            input("\nPresiona Enter para salir...")
            return
        
        # Guardar username en config para gestión posterior
        save_username_config(username)
        
        # Paso 4: Configurar automatización (si no se omite)
        automation_enabled = False
        
        if args.skip_automation:
            print("\n⚠️  Omitiendo configuración de automatización")
            automate = False
            # Valores por defecto para cuando se omite la automatización
            start_time, end_time, interval = "08:00", "22:00", 30
        else:
            automate = ask_for_automation()
            if automate:
                # Obtener horario solo si se va a automatizar
                start_time, end_time, interval = get_time_schedule()
            else:
                # Valores por defecto para cuando no se automatiza
                start_time, end_time, interval = "08:00", "22:00", 30
        
        # Crear archivos batch (manual y silencioso)
        manual_batch_path, silent_batch_path = create_batch_files()
        
        if not manual_batch_path or not silent_batch_path:
            print("⚠️  No se pudieron crear los archivos batch.")
            input("\nPresiona Enter para salir...")
            return
        
        # Configurar automatización si se solicitó
        if automate:
            if add_to_task_scheduler(silent_batch_path, start_time, end_time, interval):
                automation_enabled = True
            else:
                print("⚠️  La tarea programada no se pudo crear, pero puedes ejecutar manualmente.")
        
        # Paso 5: Ejecutar por primera vez
        if run_grade_checker():
            show_final_instructions(automation_enabled)
        else:
            print("⚠️  Hubo un problema en la primera ejecución, pero la configuración está completa.")
            print("Puedes intentar ejecutar 'verificador_notas.bat' manualmente.")
            show_final_instructions(automation_enabled)
        
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()