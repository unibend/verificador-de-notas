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

def update_grade_checker_script(api_token):
    """Actualizar el script del verificador de notas con el token"""
    print("\n🔧 PASO 3: Actualizando script del verificador...")
    print("-" * 40)
    
    # Advertencia de seguridad
    print("⚠️  ADVERTENCIA DE SEGURIDAD:")
    print("Tu token de API se almacenará en texto plano en el archivo 'grade_checker.py'.")
    print("Este token permite acceder a tus datos académicos de UNETI.")
    print("MANTÉN ESTOS ARCHIVOS EN UN LUGAR SEGURO y no los compartas con nadie.")
    print("Si crees que tu token ha sido comprometido, cambia tu contraseña en UNETI.")
    print()
    
    # Confirmación del usuario
    while True:
        response = input("¿Entiendes y aceptas continuar? (s/n): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            break
        elif response in ['n', 'no']:
            print("❌ Configuración cancelada por el usuario.")
            return False
        else:
            print("Por favor, responde 's' para sí o 'n' para no.")
    
    # Usar el directorio del script actual
    script_dir = get_script_directory()
    script_path = os.path.join(script_dir, "grade_checker.py")
    
    print(f"📂 Buscando script en: {script_path}")
    
    if not os.path.exists(script_path):
        print(f"❌ No se encontró el archivo 'grade_checker.py' en {script_dir}")
        print("Asegúrate de que el archivo esté en la misma carpeta que este configurador.")
        return False
    
    try:
        # Crear backup del archivo original
        backup_path = os.path.join(script_dir, "grade_checker.py.backup")
        shutil.copy2(script_path, backup_path)
        print(f"📋 Backup creado: {backup_path}")
        
        # Leer el archivo original
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que el placeholder existe
        if 'API_TOKEN = "placeholder"' not in content:
            print("⚠️  No se encontró el placeholder del token en el script")
            print("El token podría ya estar configurado o el archivo podría estar modificado")
            
            # Preguntar si continuar de todas formas
            while True:
                response = input("¿Continuar de todas formas? (s/n): ").strip().lower()
                if response in ['s', 'si', 'sí', 'y', 'yes']:
                    break
                elif response in ['n', 'no']:
                    return False
                else:
                    print("Por favor, responde 's' para sí o 'n' para no.")
        
        # Reemplazar el placeholder con el token real
        updated_content = content.replace('API_TOKEN = "placeholder"', f'API_TOKEN = "{api_token}"')
        
        # Escribir el archivo actualizado de forma atómica
        temp_file = os.path.join(script_dir, "grade_checker.py.tmp")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        # Reemplazar el archivo original
        os.replace(temp_file, script_path)
        
        print("✅ Script actualizado correctamente con tu token de API")
        print("🔒 Recuerda: mantén tus archivos seguros y no los compartas.")
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar el script: {e}")
        # Restaurar backup si existe
        if os.path.exists(backup_path):
            try:
                os.replace(backup_path, script_path)
                print("📋 Backup restaurado debido al error")
            except Exception:
                pass
        return False

def ask_for_automation():
    """Preguntar si quiere automatización"""
    print("\n⚙️ PASO 4: Configuración de automatización")
    print("-" * 40)
    print("¿Quieres que el verificador se ejecute automáticamente cada 30 minutos?")
    print("Esto te permitirá recibir notificaciones inmediatas cuando cambien tus notas.")
    print()
    
    while True:
        response = input("👉 Ejecutar automáticamente cada 30 minutos? (s/n): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Por favor, responde 's' para sí o 'n' para no.")

def create_batch_file():
    """Crear archivo batch para ejecutar el script"""
    try:
        # Obtener rutas absolutas y validarlas
        script_dir = get_script_directory()
        python_exe = sys.executable
        script_path = os.path.join(script_dir, "grade_checker.py")
        batch_path = os.path.join(script_dir, "verificador_notas.bat")
        
        print(f"📂 Creando archivo batch en: {batch_path}")
        
        # Validar que las rutas son seguras
        if not os.path.exists(python_exe):
            print(f"❌ No se encontró Python en: {python_exe}")
            return None
        
        if not os.path.exists(script_path):
            print(f"❌ No se encontró el script en: {script_path}")
            return None
        
        # Crear contenido del archivo batch con rutas escapadas
        batch_content = f'''@echo off
cd /d "{script_dir}"
"{python_exe}" "{script_path}"
pause
'''
        
        # Escribir archivo batch
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        print(f"✅ Archivo batch creado: {batch_path}")
        return batch_path
        
    except Exception as e:
        print(f"❌ Error al crear archivo batch: {e}")
        return None

def add_to_task_scheduler(batch_path):
    """Agregar tarea al programador de tareas de Windows"""
    print("\n📅 Configurando tarea programada...")
    print("-" * 40)
    
    try:
        # Nombre de la tarea
        task_name = "VerificadorNotasUNETI"
        
        # Validar que el archivo batch existe
        if not os.path.exists(batch_path):
            print(f"❌ El archivo batch no existe: {batch_path}")
            return False
        
        # Comando para crear la tarea programada
        cmd = [
            'schtasks', '/create',
            '/tn', task_name,
            '/tr', f'"{batch_path}"',
            '/sc', 'daily',      # Tarea diaria
            '/st', '08:00',      # Comienza a las 8:00 AM
            '/ri', '30',         # Repetir cada 30 minutos
            '/du', '840',        # Duración de 14 horas (8:00 AM a 10:00 PM)
            '/f'                # Forzar creación si ya existe
        ]
        
        print("⏳ Creando tarea programada...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tarea programada creada exitosamente!")
            print(f"📋 Nombre de la tarea: {task_name}")
            print("⏰ Se ejecutará diariamente de 8:00 AM a 10:00 PM, cada 30 minutos")
            print("\nPara gestionar la tarea puedes:")
            print("• Abrir 'Programador de tareas' en Windows")
            print(f"• Buscar la tarea llamada '{task_name}'")
            print("• Desde ahí puedes habilitarla, deshabilitarla o eliminarla")
            return True
        else:
            print("❌ Error al crear la tarea programada")
            print(f"Error: {result.stderr}")
            print("\n⚠️  Intentando configuración alternativa...")
            
            # Configuración alternativa sin /du
            alt_cmd = [
                'schtasks', '/create',
                '/tn', task_name,
                '/tr', f'"{batch_path}"',
                '/sc', 'minute',  # Ejecutar cada 30 minutos
                '/mo', '30',
                '/st', '08:00',   # Comenzar a las 8:00 AM
                '/et', '22:00',   # Terminar a las 10:00 PM
                '/f'
            ]
            
            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True)
            if alt_result.returncode == 0:
                print("✅ Configuración alternativa exitosa!")
                print("⏰ Se ejecutará cada 30 minutos de 8:00 AM a 10:00 PM")
                return True
            else:
                print("❌ Error en configuración alternativa")
                print(f"Error: {alt_result.stderr}")
                return False
            
    except Exception as e:
        print(f"❌ Error al configurar la tarea programada: {e}")
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
                              encoding='utf-8',  # Specify UTF-8 encoding for text streams
                              errors='replace') # Replace characters that can't be encoded/decoded
        
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
    print("• ✅ Token de API obtenido y configurado")
    print("• ✅ Script del verificador actualizado")
    print("• ✅ Verificación inicial completada")
    if automation_enabled:
        print("• ✅ Tarea programada configurada (cada 30 minutos)")
    else:
        print("• ⚠️  Tarea programada omitida (sin permisos de administrador)")
    print()
    print("🔒 RECORDATORIO DE SEGURIDAD:")
    print("• Tu token de API está almacenado en texto plano en 'grade_checker.py'")
    print("• MANTÉN ESTOS ARCHIVOS EN UN LUGAR SEGURO")
    print("• No compartas estos archivos con nadie")
    print("• Si crees que tu token fue comprometido, cambia tu contraseña en UNETI")
    print()
    print("📝 ARCHIVOS CREADOS:")
    print("• verificador_notas.bat - Para ejecutar manualmente")
    print("• previous_grades.json - Datos de notas anteriores")
    print("• grade_history.txt - Historial de cambios")
    print("• grade_checker.py.backup - Respaldo del archivo original")
    print()
    print("🔔 NOTIFICACIONES:")
    print("Ahora recibirás notificaciones cuando:")
    print("• Recibas una nueva calificación")
    print("• Se actualice una calificación existente")
    print("• Se agregue una nueva materia")
    print()
    print("⚙️ GESTIÓN:")
    print("• Para ejecutar manualmente: doble clic en 'verificador_notas.bat'")
    print("• Para ver el historial: abrir 'grade_history.txt'")
    if automation_enabled:
        print("• Para gestionar la automatización: buscar 'VerificadorNotasUNETI' en el Programador de tareas")
    else:
        print("• Para configurar automatización: ejecutar setup.bat como administrador")
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
    
    # Advertencia de seguridad inicial
    print("🔒 ADVERTENCIA DE SEGURIDAD IMPORTANTE:")
    print("Este script almacenará tu token de API en texto plano en tu computadora.")
    print("Mantén estos archivos en un lugar seguro y no los compartas con nadie.")
    print("Si alguien más accede a estos archivos, podría tener acceso copmleto a tu cuenta de UNETI.")
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
        
        # Paso 3: Actualizar script
        if not update_grade_checker_script(api_token):
            print("❌ No se pudo actualizar el script.")
            input("\nPresiona Enter para salir...")
            return
        
        # Paso 4: Configurar automatización (si no se omite)
        automation_enabled = False
        if args.skip_automation:
            print("\n⚠️  Omitiendo configuración de automatización (sin permisos de administrador)")
            automate = False
        else:
            automate = ask_for_automation()
        
        batch_path = None
        if automate:
            batch_path = create_batch_file()
            if batch_path:
                if add_to_task_scheduler(batch_path):
                    automation_enabled = True
                else:
                    print("⚠️  La tarea programada no se pudo crear, pero puedes ejecutar manualmente.")
            else:
                print("⚠️  No se pudo crear el archivo batch para la automatización.")
        else:
            # Crear archivo batch de todas formas para ejecución manual
            batch_path = create_batch_file()
        
        # Paso 5: Ejecutar por primera vez
        if run_grade_checker():
            show_final_instructions(automation_enabled)
        else:
            print("⚠️  Hubo un problema en la primera ejecución, pero la configuración está completa.")
            print("Puedes intentar ejecutar 'verificador_notas.bat' manualmente.")
        
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
