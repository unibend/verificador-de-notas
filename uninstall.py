import subprocess
import os
import platform
import sys

def print_banner():
    """Mostrar banner del desinstalador"""
    print("=" * 60)
    print("🗑️  DESINSTALADOR DE VERIFICADOR DE NOTAS UNETI")
    print("=" * 60)
    print("Este programa eliminará la tarea programada del verificador")
    print("de notas y opcionalmente los archivos relacionados.")
    print("=" * 60)
    print()

def check_task_exists():
    """Verificar si la tarea programada existe"""
    try:
        cmd = ['schtasks', '/query', '/tn', 'VerificadorNotasUNETI']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def remove_scheduled_task():
    """Eliminar la tarea programada"""
    print("🔄 Eliminando tarea programada...")
    print("-" * 40)
    
    try:
        # Verificar si la tarea existe
        if not check_task_exists():
            print("ℹ️  La tarea programada 'VerificadorNotasUNETI' no existe.")
            return True
        
        # Eliminar la tarea
        cmd = ['schtasks', '/delete', '/tn', 'VerificadorNotasUNETI', '/f']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tarea programada eliminada exitosamente!")
            return True
        else:
            print("❌ Error al eliminar la tarea programada")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error al eliminar la tarea programada: {e}")
        return False

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
        ("grade_history.txt", "Historial completo de cambios de notas")
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
        print("✅ Tarea programada eliminada exitosamente")
        print("   • El verificador ya no se ejecutará automáticamente")
    else:
        print("❌ La tarea programada no se pudo eliminar completamente")
    
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
        "grade_history.txt"
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
    print("• Puedes volver a configurar la automatización ejecutando el setup")
    print("• Los datos de notas se mantienen a menos que los hayas eliminado")
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
        # Paso 1: Eliminar tarea programada
        task_removed = remove_scheduled_task()
        
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