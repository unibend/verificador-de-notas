#!/usr/bin/env python3
"""
Smart Launcher for UNETI Grade Checker
Frontend for running, configuring, and managing the grade checker program.
"""

import os
import sys
import json
import subprocess
import platform
import ctypes
from datetime import datetime
from pathlib import Path

def print_banner():
    """Display program banner"""
    print("=" * 60)
    print("🚀 LANZADOR INTELIGENTE - VERIFICADOR DE NOTAS UNETI")
    print("=" * 60)
    print("Detectando configuración...")
    print()

def get_script_directory():
    """Get the directory where the script is located"""
    # If the script is being executed as a compiled .exe
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def check_admin_privileges():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def is_windows():
    """Check if we're on Windows"""
    return platform.system() == "Windows"

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 6):
        print("❌ Este programa requiere Python 3.6 o superior")
        print(f"Tu versión actual es: {sys.version}")
        return False
    return True

def check_keyring_available():
    """Check if keyring library is available"""
    try:
        import keyring
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install necessary dependencies"""
    print("📦 Verificando e instalando dependencias...")
    print("-" * 50)
    
    dependencies = ['requests', 'keyring']
    installed = []
    failed = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - ya instalado")
            installed.append(dep)
        except ImportError:
            print(f"📦 Instalando {dep}...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                              check=True, capture_output=True)
                print(f"✅ {dep} - instalado correctamente")
                installed.append(dep)
            except subprocess.CalledProcessError:
                print(f"❌ {dep} - error en la instalación")
                failed.append(dep)
    
    print("-" * 50)
    if failed:
        print("⚠️  Algunas dependencias no se pudieron instalar automáticamente:")
        for dep in failed:
            print(f"   • {dep}")
        print("Instálalas manualmente con: pip install " + " ".join(failed))
        return False
    else:
        print("✅ Todas las dependencias están disponibles")
        return True

def check_configuration_status():
    """Check the configuration status using keyring and config file"""
    script_dir = get_script_directory()
    config_path = os.path.join(script_dir, "config.json")
    
    print("🔍 Verificando configuración...")
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print("❌ Archivo de configuración no encontrado")
        return "not_configured", None
    
    try:
        # Read config file
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        username = config.get('username')
        service_name = config.get('service_name', 'UNETI-Grade-Checker')
        
        if not username:
            print("❌ Configuración incompleta: falta nombre de usuario")
            return "incomplete_config", None
        
        # Check if keyring is available
        if not check_keyring_available():
            print("❌ Keyring no disponible")
            return "keyring_unavailable", username
        
        # Check if token exists in keyring
        import keyring
        token = keyring.get_password(service_name, username)
        
        if not token:
            print("❌ Token no encontrado en keyring")
            return "token_missing", username
        
        if len(token) < 10:
            print("❌ Token inválido")
            return "token_invalid", username
        
        print("✅ Configuración válida encontrada")
        return "configured", username
        
    except json.JSONDecodeError:
        print("❌ Archivo de configuración corrupto")
        return "config_corrupted", None
    except Exception as e:
        print(f"❌ Error al verificar configuración: {e}")
        return "error", None

def check_required_files():
    """Check if all required files exist"""
    script_dir = get_script_directory()
    
    files_to_check = {
        'grade_checker.py': 'Verificador principal',
        'configurador.py': 'Configurador',
        'uninstall.py': 'Desinstalador'
    }
    
    missing_files = []
    existing_files = {}
    
    for filename, description in files_to_check.items():
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            existing_files[filename] = filepath
        else:
            missing_files.append((filename, description))
    
    return existing_files, missing_files

def run_script(script_path, script_name, args=None):
    """Run a Python script"""
    try:
        print(f"🚀 Ejecutando {script_name}...")
        print("-" * 40)
        
        # Change to script directory
        original_dir = os.getcwd()
        script_dir = os.path.dirname(script_path)
        os.chdir(script_dir)
        
        # Prepare command
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        # Execute the script
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        # Restore original directory
        os.chdir(original_dir)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error al ejecutar {script_name}: {e}")
        return False

def restart_as_admin():
    """Restart the script as administrator"""
    try:
        script_path = os.path.abspath(__file__)
        print(f"🔄 Reiniciando como administrador...")
        print("(Se abrirá una nueva ventana)")
        
        # Use PowerShell to restart as administrator
        powershell_cmd = f'Start-Process python -ArgumentList "{script_path}" -Verb RunAs'
        subprocess.run(["powershell", "-Command", powershell_cmd])
        return True
    except Exception as e:
        print(f"❌ Error al reiniciar como administrador: {e}")
        return False

def ask_for_admin_restart():
    """Ask if user wants to restart as administrator"""
    print("\n⚠️  PERMISOS DE ADMINISTRADOR")
    print("-" * 50)
    print("Para configurar la ejecución automática (tareas programadas),")
    print("se necesitan permisos de administrador.")
    print()
    print("Opciones:")
    print("[1] 🔄 Reiniciar como administrador (recomendado)")
    print("[2] ⏭️  Continuar sin automatización")
    print("[3] ❌ Cancelar")
    print()
    
    while True:
        try:
            choice = input("Selecciona una opción (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            else:
                print("❌ Opción no válida. Por favor selecciona 1, 2 o 3.")
        except KeyboardInterrupt:
            print("\n❌ Operación cancelada por el usuario.")
            return '3'

def show_status_info(status, username):
    """Show detailed status information"""
    print("📋 ESTADO DE CONFIGURACIÓN:")
    print("-" * 40)
    
    if status == "not_configured":
        print("❌ NO CONFIGURADO")
        print("• No se encontró archivo de configuración")
        print("• Es necesario ejecutar el configurador")
        
    elif status == "incomplete_config":
        print("❌ CONFIGURACIÓN INCOMPLETA")
        print("• Archivo de configuración existe pero está incompleto")
        print("• Es necesario reconfigurar")
        
    elif status == "keyring_unavailable":
        print("❌ KEYRING NO DISPONIBLE")
        print("• La librería keyring no está instalada")
        print("• Instalar con: pip install keyring")
        
    elif status == "token_missing":
        print("❌ TOKEN FALTANTE")
        print(f"• Usuario configurado: {username}")
        print("• Token no encontrado en keyring")
        print("• Es necesario reconfigurar")
        
    elif status == "token_invalid":
        print("❌ TOKEN INVÁLIDO")
        print(f"• Usuario configurado: {username}")
        print("• Token existe pero parece inválido")
        print("• Es necesario reconfigurar")
        
    elif status == "configured":
        print("✅ CONFIGURADO CORRECTAMENTE")
        print(f"• Usuario: {username}")
        print("• Token válido encontrado en keyring")
        print("• Listo para ejecutar")
        
    elif status == "config_corrupted":
        print("❌ CONFIGURACIÓN CORRUPTA")
        print("• Archivo de configuración dañado")
        print("• Es necesario reconfigurar")
        
    elif status == "error":
        print("❌ ERROR")
        print("• Error al verificar configuración")
        print("• Revisar permisos y archivos")
    
    print()

def show_system_info():
    """Show system information"""
    print("🖥️  INFORMACIÓN DEL SISTEMA:")
    print("-" * 40)
    print(f"• Sistema: {platform.system()} {platform.release()}")
    print(f"• Python: {sys.version.split()[0]}")
    is_admin = check_admin_privileges() if is_windows() else False
    print(f"• Administrador: {'Sí' if is_admin else 'No'}")
    print(f"• Directorio: {get_script_directory()}")
    print()

def show_menu():
    """Show the main menu"""
    print("🎯 OPCIONES DISPONIBLES:")
    print("-" * 40)
    print("1. 🚀 Ejecutar verificador de notas")
    print("2. ⚙️  Configurar/Reconfigurar")
    print("3. 📦 Instalar dependencias")
    print("4. 🗑️  Desinstalar")
    print("5. ❌ Salir")
    print()

def get_user_choice():
    """Get user's menu choice"""
    while True:
        choice = input("👉 Selecciona una opción (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        print("❌ Opción inválida. Selecciona 1, 2, 3, 4 o 5.")

def main():
    """Main function"""
    print_banner()
    
    # Initial checks
    if not check_python_version():
        input("\nPresiona Enter para salir...")
        return
    
    # Show system information
    show_system_info()
    
    # Check if we're on Windows
    if not is_windows():
        print("⚠️ Este programa está optimizado para Windows.")
        print("Algunas funciones podrían no funcionar correctamente en otros sistemas.")
        print()
    
    # Check required files
    existing_files, missing_files = check_required_files()
    
    if missing_files:
        print("❌ ARCHIVOS FALTANTES:")
        print("-" * 40)
        for filename, description in missing_files:
            print(f"• {filename} - {description}")
        print()
        print("🔧 SOLUCIÓN:")
        print("• Descargar todos los archivos del verificador")
        print("• Asegurarse de que estén en la misma carpeta")
        print("• Ejecutar este lanzador nuevamente")
        print()
        input("Presiona Enter para salir...")
        return
    
    # Check configuration status
    status, username = check_configuration_status()
    show_status_info(status, username)
    
    # Show menu and get user choice
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == '1':  # Run grade checker
            if status == "configured":
                print("\n" + "=" * 60)
                if run_script(existing_files['grade_checker.py'], "verificador de notas"):
                    print("✅ Verificación completada!")
                else:
                    print("❌ Error durante la verificación.")
                    print("Verifica tu conexión a internet y credenciales.")
            else:
                print("\n❌ No se puede ejecutar el verificador.")
                print("Es necesario configurar el programa primero.")
                print("Selecciona la opción 2 para configurar.")
            
        elif choice == '2':  # Configure
            print("\n" + "=" * 60)
            
            # Check if admin privileges are needed and available
            is_admin = check_admin_privileges() if is_windows() else True
            skip_automation = False
            
            if is_windows() and not is_admin:
                admin_choice = ask_for_admin_restart()
                if admin_choice == '1':
                    if restart_as_admin():
                        return  # New process will handle it
                    else:
                        print("❌ No se pudo reiniciar como administrador.")
                        print("Continuando sin automatización...")
                        skip_automation = True
                elif admin_choice == '3':
                    print("❌ Configuración cancelada.")
                    continue
                else:  # Choice 2 - continue without automation
                    skip_automation = True
            
            # Run configurator
            args = ["--skip-automation"] if skip_automation else []
            if run_script(existing_files['configurador.py'], "configurador", args):
                print("✅ Configuración completada!")
                print("Actualizando estado...")
                # Recheck configuration
                status, username = check_configuration_status()
                show_status_info(status, username)
            else:
                print("❌ Error durante la configuración.")
            
        elif choice == '3':  # Install dependencies
            print("\n" + "=" * 60)
            if install_dependencies():
                print("✅ Dependencias instaladas correctamente!")
                # Recheck configuration to update keyring status
                status, username = check_configuration_status()
                show_status_info(status, username)
            else:
                print("❌ Error al instalar algunas dependencias.")
                print("Revisa los mensajes anteriores e instala manualmente si es necesario.")
        
        elif choice == '4':  # Uninstall
            print("\n" + "=" * 60)
            
            # Check if admin privileges are recommended
            is_admin = check_admin_privileges() if is_windows() else True
            
            if is_windows() and not is_admin:
                print("⚠️  Se recomienda ejecutar la desinstalación como administrador")
                print("para eliminar completamente las tareas programadas.")
                print()
                admin_choice = ask_for_admin_restart()
                if admin_choice == '1':
                    if restart_as_admin():
                        return  # New process will handle it
                    else:
                        print("❌ No se pudo reiniciar como administrador.")
                        print("Continuando con la desinstalación...")
                elif admin_choice == '3':
                    print("❌ Desinstalación cancelada.")
                    continue
                # If choice 2, continue with uninstall
            
            print("⚠️ ADVERTENCIA: Esta acción eliminará toda la configuración.")
            while True:
                confirm = input("¿Estás seguro de que quieres desinstalar? (s/n): ").strip().lower()
                if confirm in ['s', 'si', 'sí', 'y', 'yes']:
                    if run_script(existing_files['uninstall.py'], "desinstalador"):
                        print("✅ Desinstalación completada!")
                        # Recheck configuration
                        status, username = check_configuration_status()
                        show_status_info(status, username)
                    else:
                        print("❌ Error durante la desinstalación.")
                    break
                elif confirm in ['n', 'no']:
                    print("❌ Desinstalación cancelada.")
                    break
                else:
                    print("Por favor, responde 's' para sí o 'n' para no.")
            
        elif choice == '5':  # Exit
            print("\n👋 ¡Hasta luego!")
            break
        
        print("\n" + "=" * 60)
        input("Presiona Enter para continuar...")
        print()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL:")
    print(f"• Sistema: {platform.system()} {platform.release()}")
    print(f"• Python: {sys.version.split()[0]}")
    print(f"• Directorio: {get_script_directory()}")
    print(f"• Estado: {status}")
    print(f"• Usuario: {username if username else 'N/A'}")
    print(f"• Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario.")
        input("\nPresiona Enter para salir...")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")