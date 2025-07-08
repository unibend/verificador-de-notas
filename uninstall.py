import subprocess
import os
import platform
import sys

def print_banner():
    """Mostrar banner del desinstalador"""
    print("=" * 60)
    print("🗑️  DESINSTALADOR DE VERIFICADOR DE NOTAS UNETI")
    print("=" * 60)
    print("Este programa eliminará las tareas programadas del verificador")
    print("de notas y opcionalmente los archivos relacionados.")
    print("=" * 60)
    print()

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
    print("🔄 Eliminando tareas programadas...")
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
    print("\n📁 Gestión de archivos")
    print("-" * 40)
    print("¿Qué archivos quieres eliminar?")
    print()
    
    files_to_check = [
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
    
    print(f"🗑️  Eliminando {len(files_to_delete)} archivo(s)...")
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
    print("\n🔧 Resetear configuración")
    print("-" * 40)
    
    script_name = "grade_checker.py"
    
    if not validate_file_path(script_name):
        print(f"ℹ️  El archivo '{script_name}' no existe.")
        return True
    
    print("¿Quieres resetear el token de API en el script del verificador?")
    print("(Esto volverá a poner 'placeholder' en lugar de tu token actual)")
    print()
    
    while True:
        response = input("👉 Resetear token de API? (s/n): ").strip().lower()
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
            print("✅ Token de API reseteado a 'placeholder'")
            return True
        else:
            print("ℹ️  El token ya está en 'placeholder' o no se encontró")
            return True
            
    except Exception as e:
        print(f"❌ Error al resetear el token: {e}")
        return False

def show_final_message(task_removed, files_deleted, token_reset):
    """Mostrar mensaje final"""
    print("\n🎯 DESINSTALACIÓN COMPLETADA")
    print("=" * 60)
    
    if task_removed:
        print("✅ Tareas programadas eliminadas exitosamente")
        print("   • El verificador ya no se ejecutará automáticamente")
        print("   • Se eliminaron tanto la tarea diaria como la de intervalos")
    else:
        print("❌ Algunas tareas programadas no se pudieron eliminar completamente")
        print("   • Es posible que necesites eliminarlas manualmente desde el Programador de tareas")
    
    if files_deleted:
        print("✅ Archivos seleccionados eliminados")
    
    if token_reset:
        print("✅ Token de API reseteado")
    
    print()
    print("📋 ESTADO ACTUAL:")
    
    # Verificar qué archivos quedan
    remaining_files = []
    files_to_check = [
        "grade_checker.py",
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
    print("• Puedes volver a configurar la automatización ejecutando el configurador")
    print("• Los datos de notas se mantienen a menos que los hayas eliminado")
    print("• Para reconfigurar, ejecuta 'configurador.py' nuevamente")
    print("=" * 60)

def main():
    """Función principal"""
    print_banner()
    
    # Verificar que estamos en Windows
    if platform.system() != "Windows":
        print("❌ Este desinstalador está diseñado para Windows únicamente.")
        input("\nPresiona Enter para salir...")
        return
    
    print("⚠️  ADVERTENCIA:")
    print("Este proceso eliminará la ejecución automática del verificador de notas.")
    print("Se eliminarán TODAS las tareas programadas relacionadas (diaria e intervalos).")
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
        # Paso 1: Eliminar tareas programadas
        task_removed = remove_scheduled_tasks()
        
        # Paso 2: Preguntar por archivos
        files_to_delete = ask_delete_files()
        files_deleted = delete_files(files_to_delete) if files_to_delete else False
        
        # Paso 3: Preguntar por resetear token
        token_reset = reset_api_token()
        
        # Mostrar resumen final
        show_final_message(task_removed, files_deleted, token_reset)
        
    except KeyboardInterrupt:
        print("\n\n❌ Desinstalación cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado durante la desinstalación: {e}")
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
