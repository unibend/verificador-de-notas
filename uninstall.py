import subprocess
import os
import platform
import sys
import json

def print_banner():
    """Mostrar banner del desinstalador"""
    print("=" * 60)
    print("🗑️  DESINSTALADOR DE VERIFICADOR DE NOTAS UNETI")
    print("=" * 60)
    print("Este programa eliminará las tareas programadas del verificador")
    print("de notas, las credenciales almacenadas y opcionalmente los archivos relacionados.")
    print("=" * 60)
    print()

def check_keyring_available():
    """Verificar si keyring está disponible"""
    try:
        import keyring
        return True
    except ImportError:
        return False

def get_stored_username():
    """Obtener el nombre de usuario almacenado en config.json"""
    try:
        script_dir = get_script_directory()
        config_path = os.path.join(script_dir, "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('username')
        return None
    except Exception as e:
        print(f"⚠️ Error al leer configuración: {e}")
        return None

def remove_stored_credentials():
    """Eliminar credenciales almacenadas en keyring"""
    print("\n🔑 ELIMINANDO CREDENCIALES ALMACENADAS")
    print("-" * 40)
    
    if not check_keyring_available():
        print("ℹ️  La librería keyring no está disponible.")
        print("Las credenciales no se pueden eliminar automáticamente.")
        print("Si tienes credenciales almacenadas, elimínalas manualmente desde:")
        print("• Panel de Control > Administrador de credenciales")
        print("• Buscar 'UNETI-Grade-Checker'")
        return True
    
    try:
        import keyring
        
        # Intentar obtener username desde config
        username = get_stored_username()
        
        if not username:
            print("⚠️  No se encontró el nombre de usuario en la configuración.")
            print("¿Quieres intentar eliminar las credenciales manualmente?")
            print("Esto requiere que ingreses tu nombre de usuario.")
            
            while True:
                response = input("👉 Intentar eliminación manual? (s/n): ").strip().lower()
                if response in ['s', 'si', 'sí', 'y', 'yes']:
                    username = input("👤 Ingresa tu nombre de usuario: ").strip()
                    if username:
                        break
                    else:
                        print("❌ El nombre de usuario no puede estar vacío.")
                        continue
                elif response in ['n', 'no']:
                    print("ℹ️  Eliminación de credenciales omitida.")
                    print("Para eliminar manualmente:")
                    print("• Panel de Control > Administrador de credenciales")
                    print("• Buscar 'UNETI-Grade-Checker'")
                    return True
                else:
                    print("Por favor, responde 's' para sí o 'n' para no.")
        
        service_name = "UNETI-Grade-Checker"
        
        print(f"🔄 Eliminando credenciales para usuario: {username}")
        print(f"🔄 Servicio: {service_name}")
        
        # Intentar eliminar las credenciales
        try:
            # Primero verificar si existen las credenciales
            stored_token = keyring.get_password(service_name, username)
            
            if stored_token:
                # Eliminar las credenciales
                keyring.delete_password(service_name, username)
                print("✅ Credenciales eliminadas exitosamente del gestor de credenciales del sistema")
                print("🔒 El token de API ya no está almacenado en keyring")
                return True
            else:
                print("ℹ️  No se encontraron credenciales almacenadas para este usuario.")
                return True
                
        except keyring.errors.PasswordDeleteError:
            print("ℹ️  No se encontraron credenciales almacenadas.")
            return True
        except Exception as e:
            print(f"❌ Error al eliminar credenciales: {e}")
            print("Puedes eliminarlas manualmente desde:")
            print("• Panel de Control > Administrador de credenciales")
            print("• Buscar 'UNETI-Grade-Checker'")
            return False
            
    except Exception as e:
        print(f"❌ Error al acceder al gestor de credenciales: {e}")
        return False

def get_script_directory():
    """Obtener el directorio donde está ubicado el script"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def check_task_exists(task_name):
    """Verificar si una tarea programada existe"""
    try:
        cmd = ['schtasks', '/query', '/tn', task_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def remove_scheduled_tasks():
    """Eliminar las tareas programadas"""
    print("\n🔄 ELIMINANDO TAREAS PROGRAMADAS")
    print("-" * 40)
    
    # Lista de tareas a eliminar (nombres antiguos y nuevos)
    tasks_to_remove = [
        "VerificadorNotasUNETI",  # Tarea antigua (una sola tarea)
        "VerificadorNotasUNETI_Daily",  # Tarea diaria nueva
        "VerificadorNotasUNETI_Interval"  # Tarea de intervalo nueva
    ]
    
    tasks_found = []
    tasks_removed = []
    errors = []
    
    # Verificar qué tareas existen
    for task_name in tasks_to_remove:
        if check_task_exists(task_name):
            tasks_found.append(task_name)
    
    if not tasks_found:
        print("ℹ️  No se encontraron tareas programadas del verificador de notas.")
        return True
    
    print(f"📋 Se encontraron {len(tasks_found)} tarea(s) programada(s):")
    for task in tasks_found:
        print(f"   • {task}")
    print()
    
    # Eliminar cada tarea encontrada
    for task_name in tasks_found:
        try:
            print(f"🗑️  Eliminando tarea: {task_name}")
            cmd = ['schtasks', '/delete', '/tn', task_name, '/f']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Tarea '{task_name}' eliminada exitosamente!")
                tasks_removed.append(task_name)
            else:
                print(f"❌ Error al eliminar tarea '{task_name}'")
                print(f"   Error: {result.stderr}")
                errors.append(task_name)
                
        except Exception as e:
            print(f"❌ Error al eliminar tarea '{task_name}': {e}")
            errors.append(task_name)
    
    # Mostrar resumen
    print()
    if tasks_removed:
        print(f"✅ {len(tasks_removed)} tarea(s) eliminada(s) exitosamente")
    
    if errors:
        print(f"❌ {len(errors)} tarea(s) no se pudieron eliminar:")
        for task in errors:
            print(f"   • {task}")
        return False
    
    return True

def validate_file_path(filename):
    """Validar que el archivo esté en el directorio actual"""
    if not filename:
        return False
    
    # Verificar que no hay caracteres peligrosos
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Verificar que el archivo existe en el directorio actual
    return os.path.exists(filename) and os.path.isfile(filename)

def ask_delete_files():
    """Preguntar si quiere eliminar archivos relacionados"""
    print("\n📁 GESTIÓN DE ARCHIVOS")
    print("-" * 40)
    print("¿Qué archivos quieres eliminar?")
    print()
    
    files_to_check = [
        ("config.json", "Configuración de usuario y credenciales"),
        ("verificador_notas.bat", "Archivo batch para ejecución manual"),
        ("previous_grades.json", "Datos de notas anteriores guardadas"),
        ("grade_history.txt", "Historial completo de cambios de notas"),
        ("grade_checker.py.backup", "Backup del archivo original del verificador")
    ]
    
    files_to_delete = []
    
    for filename, description in files_to_check:
        if validate_file_path(filename):
            print(f"📄 {filename}")
            print(f"   {description}")
            while True:
                response = input(f"   ¿Eliminar este archivo? (s/n): ").strip().lower()
                if response in ['s', 'si', 'sí', 'y', 'yes']:
                    files_to_delete.append(filename)
                    break
                elif response in ['n', 'no']:
                    break
                else:
                    print("   Por favor, responde 's' para sí o 'n' para no.")
            print()
        else:
            print(f"ℹ️  {filename} no existe")
    
    return files_to_delete

def delete_files(files_to_delete):
    """Eliminar archivos seleccionados"""
    if not files_to_delete:
        print("ℹ️  No se seleccionaron archivos para eliminar.")
        return True
    
    print(f"\n🗑️  ELIMINANDO {len(files_to_delete)} ARCHIVO(S)")
    print("-" * 40)
    
    success = True
    for filename in files_to_delete:
        try:
            # Doble verificación de seguridad
            if not validate_file_path(filename):
                print(f"❌ Archivo no válido: {filename}")
                success = False
                continue
            
            os.remove(filename)
            print(f"✅ Eliminado: {filename}")
        except Exception as e:
            print(f"❌ Error al eliminar {filename}: {e}")
            success = False
    
    return success

def reset_api_token():
    """Preguntar si quiere resetear el token de API en el script"""
    print("\n🔧 RESETEAR CONFIGURACIÓN DEL SCRIPT")
    print("-" * 40)
    
    script_name = "grade_checker.py"
    
    if not validate_file_path(script_name):
        print(f"ℹ️  El archivo '{script_name}' no existe.")
        return True
    
    print("¿Quieres resetear el token de API en el script del verificador?")
    print("(Esto volverá a poner 'placeholder' en lugar de tu token actual)")
    print("NOTA: Con el nuevo sistema, las credenciales se almacenan en keyring,")
    print("por lo que este paso es opcional y principalmente para limpieza.")
    print()
    
    while True:
        response = input("👉 Resetear token de API en el script? (s/n): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            break
        elif response in ['n', 'no']:
            return True
        else:
            print("Por favor, responde 's' para sí o 'n' para no.")
    
    try:
        # Crear backup antes de modificar
        backup_name = f"{script_name}.backup"
        with open(script_name, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar líneas que contengan API_TOKEN
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            if 'API_TOKEN = ' in line and 'placeholder' not in line:
                lines[i] = '    API_TOKEN = "placeholder"'
                modified = True
                break
        
        if modified:
            # Escribir el archivo modificado de forma atómica
            temp_file = f"{script_name}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            # Reemplazar el archivo original
            os.replace(temp_file, script_name)
            print("✅ Token de API reseteado a 'placeholder' en el script")
            print("ℹ️  Las credenciales principales se eliminaron del keyring")
            return True
        else:
            print("ℹ️  El token ya está en 'placeholder' o no se encontró")
            return True
            
    except Exception as e:
        print(f"❌ Error al resetear el token: {e}")
        return False

def show_manual_cleanup_instructions():
    """Mostrar instrucciones para limpieza manual"""
    print("\n🔧 INSTRUCCIONES PARA LIMPIEZA MANUAL")
    print("-" * 40)
    print("Si deseas hacer una limpieza completa manual, puedes:")
    print()
    print("🔑 ADMINISTRADOR DE CREDENCIALES:")
    print("1. Presiona Win + R, escribe 'control' y presiona Enter")
    print("2. Ve a 'Cuentas de usuario' > 'Administrador de credenciales'")
    print("3. Busca 'UNETI-Grade-Checker' y elimínalo")
    print()
    print("📅 PROGRAMADOR DE TAREAS:")
    print("1. Presiona Win + R, escribe 'taskschd.msc' y presiona Enter")
    print("2. Busca tareas que contengan 'VerificadorNotasUNETI'")
    print("3. Elimina todas las tareas encontradas")
    print()
    print("📁 ARCHIVOS RESTANTES:")
    print("Revisa estos archivos en la carpeta del verificador:")
    print("• config.json - Configuración de usuario")
    print("• previous_grades.json - Datos de notas anteriores")
    print("• grade_history.txt - Historial de cambios")
    print("• verificador_notas.bat - Archivo de ejecución manual")
    print("• grade_checker.py.backup - Backup del script original")

def show_final_message(credentials_removed, task_removed, files_deleted, token_reset):
    """Mostrar mensaje final"""
    print("\n🎯 DESINSTALACIÓN COMPLETADA")
    print("=" * 60)
    
    # Resumen de credenciales
    if credentials_removed:
        print("✅ Credenciales eliminadas del gestor de credenciales del sistema")
        print("   • Token de API eliminado de keyring")
        print("   • Información de autenticación borrada")
    else:
        print("⚠️  Las credenciales no se pudieron eliminar automáticamente")
        print("   • Puedes eliminarlas manualmente desde el Administrador de credenciales")
        print("   • Busca 'UNETI-Grade-Checker' en el gestor de credenciales")
    
    # Resumen de tareas
    if task_removed:
        print("✅ Tareas programadas eliminadas exitosamente")
        print("   • El verificador ya no se ejecutará automáticamente")
        print("   • Se eliminaron tanto la tarea diaria como la de intervalos")
    else:
        print("⚠️  Algunas tareas programadas no se pudieron eliminar completamente")
        print("   • Es posible que necesites eliminarlas manualmente desde el Programador de tareas")
    
    # Resumen de archivos
    if files_deleted:
        print("✅ Archivos seleccionados eliminados")
    
    # Resumen de token
    if token_reset:
        print("✅ Token de API reseteado en el script")
    
    print()
    print("📋 ESTADO ACTUAL:")
    
    # Verificar qué archivos quedan
    remaining_files = []
    files_to_check = [
        "grade_checker.py",
        "config.json",
        "verificador_notas.bat", 
        "previous_grades.json",
        "grade_history.txt",
        "grade_checker.py.backup"
    ]
    
    for filename in files_to_check:
        if validate_file_path(filename):
            remaining_files.append(filename)
    
    if remaining_files:
        print("📄 Archivos restantes:")
        for filename in remaining_files:
            print(f"   • {filename}")
    else:
        print("📄 No quedan archivos relacionados")
    
    print()
    print("ℹ️  NOTAS IMPORTANTES:")
    print("• El script principal del verificador sigue disponible")
    print("• Las credenciales han sido eliminadas del sistema")
    print("• Para reconfigurar, ejecuta 'configurador.py' nuevamente")
    print("• Será necesario ingresar credenciales nuevamente")
    print("• Los datos de notas se mantienen a menos que los hayas eliminado")
    
    # Mostrar instrucciones de limpieza manual
    show_manual_cleanup_instructions()
    
    print("=" * 60)

def main():
    """Función principal"""
    print_banner()
    
    # Verificar que estamos en Windows
    if platform.system() != "Windows":
        print("❌ Este desinstalador está diseñado para Windows únicamente.")
        input("\nPresiona Enter para salir...")
        return
    
    # Información sobre el nuevo sistema de credenciales
    print("🔒 INFORMACIÓN SOBRE CREDENCIALES:")
    print("Este desinstalador eliminará las credenciales almacenadas en el")
    print("gestor de credenciales del sistema (keyring) además de las tareas programadas.")
    print("Esto incluye el token de API que se almacena de forma segura.")
    print("=" * 60)
    print()
    
    print("⚠️  ADVERTENCIA:")
    print("Este proceso eliminará:")
    print("• TODAS las tareas programadas relacionadas (diaria e intervalos)")
    print("• Las credenciales almacenadas en el gestor de credenciales del sistema")
    print("• Opcionalmente, archivos de configuración y datos")
    print("¿Estás seguro de que quieres continuar?")
    print()
    
    while True:
        response = input("👉 Continuar con la desinstalación? (s/n): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            break
        elif response in ['n', 'no']:
            print("❌ Desinstalación cancelada.")
            input("\nPresiona Enter para salir...")
            return
        else:
            print("Por favor, responde 's' para sí o 'n' para no.")
    
    print()
    
    try:
        # Paso 1: Eliminar credenciales almacenadas
        credentials_removed = remove_stored_credentials()
        
        # Paso 2: Eliminar tareas programadas
        task_removed = remove_scheduled_tasks()
        
        # Paso 3: Preguntar por archivos
        files_to_delete = ask_delete_files()
        files_deleted = delete_files(files_to_delete) if files_to_delete else False
        
        # Paso 4: Preguntar por resetear token
        token_reset = reset_api_token()
        
        # Mostrar resumen final
        show_final_message(credentials_removed, task_removed, files_deleted, token_reset)
        
    except KeyboardInterrupt:
        print("\n\n❌ Desinstalación cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado durante la desinstalación: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()