#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNETI Grade Checker Setup Script
Este script configura el verificador de notas UNETI
"""

import os
import sys
import subprocess
import platform
import ctypes
from pathlib import Path

def print_banner():
    """Mostrar banner del programa"""
    print("=" * 70)
    print("🚀 CONFIGURADOR DEL VERIFICADOR DE NOTAS UNETI")
    print("=" * 70)
    print("Este programa te ayudará a configurar el verificador automático")
    print("de notas para que recibas notificaciones cuando cambien tus calificaciones.")
    print("=" * 70)
    print()

def check_admin_privileges():
    """Verificar si el script se está ejecutando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def is_windows():
    """Verificar si estamos en Windows"""
    return platform.system() == "Windows"

def get_script_directory():
    """Obtener el directorio donde está ubicado el script"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def check_python_version():
    """Verificar versión de Python"""
    if sys.version_info < (3, 6):
        print("❌ Este script requiere Python 3.6 o superior")
        print(f"Tu versión actual es: {sys.version}")
        return False
    return True

def check_required_files():
    """Verificar que los archivos necesarios existen"""
    script_dir = get_script_directory()
    required_files = [
        "configurador.py",
        "grade_checker.py",
        "uninstall.py"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(script_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   • {file}")
        print(f"\nAsegúrate de que todos los archivos estén en: {script_dir}")
        return False
    
    return True

def install_dependencies():
    """Instalar dependencias necesarias"""
    print("📦 Instalando dependencias necesarias...")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], 
                      check=True, capture_output=True)
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print("⚠️  No se pudieron instalar algunas dependencias automáticamente")
        print("El programa intentará continuar de todas formas")
        return False

def show_menu():
    """Mostrar menú principal"""
    print("¿Qué deseas hacer?")
    print()
    print("[1] 📦 Instalar el verificador de notas")
    print("[2] 🗑️  Desinstalar el verificador de notas")
    print("[3] ❌ Cancelar")
    print()

def get_user_choice():
    """Obtener elección del usuario"""
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

def run_configurador(skip_automation=False):
    """Ejecutar el configurador"""
    print("🔧 Iniciando configuración...")
    print("-" * 50)
    
    script_dir = get_script_directory()
    configurador_path = os.path.join(script_dir, "configurador.py")
    
    try:
        cmd = [sys.executable, configurador_path]
        if skip_automation:
            cmd.append("--skip-automation")
        
        # Ejecutar en el mismo directorio
        result = subprocess.run(cmd, cwd=script_dir)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error al ejecutar el configurador: {e}")
        return False

def run_uninstaller():
    """Ejecutar el desinstalador"""
    print("🗑️  Iniciando desinstalación...")
    print("-" * 50)
    
    script_dir = get_script_directory()
    uninstaller_path = os.path.join(script_dir, "uninstall.py")
    
    try:
        result = subprocess.run([sys.executable, uninstaller_path], cwd=script_dir)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error al ejecutar el desinstalador: {e}")
        return False

def ask_for_admin_restart():
    """Preguntar si quiere reiniciar como administrador"""
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

def restart_as_admin():
    """Reiniciar el script como administrador"""
    try:
        script_path = os.path.abspath(__file__)
        print(f"🔄 Reiniciando como administrador...")
        print("(Se abrirá una nueva ventana de PowerShell)")
        
        # Usar PowerShell para reiniciar como administrador
        powershell_cmd = f'Start-Process python -ArgumentList "{script_path}" -Verb RunAs'
        subprocess.run(["powershell", "-Command", powershell_cmd])
        return True
    except Exception as e:
        print(f"❌ Error al reiniciar como administrador: {e}")
        return False

def show_final_message(success, operation):
    """Mostrar mensaje final"""
    print("\n" + "=" * 70)
    if success:
        if operation == "install":
            print("🎉 ¡INSTALACIÓN COMPLETADA!")
            print()
            print("📋 El verificador de notas ha sido configurado correctamente.")
            print("• Recibirás notificaciones cuando cambien tus calificaciones")
            print("• Puedes ejecutar manualmente con 'verificador_notas.bat'")
            print("• Para gestionar la automatización, busca 'VerificadorNotasUNETI'")
            print("  en el Programador de tareas de Windows")
        else:
            print("🗑️  ¡DESINSTALACIÓN COMPLETADA!")
            print()
            print("📋 El verificador de notas ha sido desinstalado.")
            print("• La tarea programada fue eliminada")
            print("• Los archivos fueron gestionados según tu elección")
    else:
        print("❌ OPERACIÓN INCOMPLETA")
        print()
        print("Hubo algunos problemas durante la operación.")
        print("Revisa los mensajes anteriores para más detalles.")
    
    print("=" * 70)

def main():
    """Función principal"""
    print_banner()
    
    # Verificaciones iniciales
    if not is_windows():
        print("❌ Este script está diseñado para Windows únicamente.")
        print("Para otros sistemas operativos, configura manualmente.")
        input("\nPresiona Enter para salir...")
        return
    
    if not check_python_version():
        input("\nPresiona Enter para salir...")
        return
    
    if not check_required_files():
        input("\nPresiona Enter para salir...")
        return
    
    # Mostrar información del sistema
    print(f"🖥️  Sistema: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    is_admin = check_admin_privileges()
    print(f"👑 Administrador: {'Sí' if is_admin else 'No'}")
    print(f"📂 Directorio: {get_script_directory()}")
    print()
    
    try:
        # Mostrar menú y obtener elección
        show_menu()
        choice = get_user_choice()
        
        if choice == '3':
            print("❌ Operación cancelada.")
            return
        
        # Instalar dependencias
        install_dependencies()
        
        if choice == '1':  # Instalar
            if not is_admin:
                admin_choice = ask_for_admin_restart()
                if admin_choice == '1':
                    if restart_as_admin():
                        return  # El nuevo proceso se encargará
                    else:
                        print("❌ No se pudo reiniciar como administrador.")
                        return
                elif admin_choice == '3':
                    print("❌ Instalación cancelada.")
                    return
                # Si eligió continuar sin admin (opción 2), continúa abajo
            
            # Ejecutar configurador
            skip_automation = not is_admin
            success = run_configurador(skip_automation)
            show_final_message(success, "install")
            
        elif choice == '2':  # Desinstalar
            if not is_admin:
                print("⚠️  Se recomienda ejecutar la desinstalación como administrador")
                print("para eliminar completamente las tareas programadas.")
                print()
                admin_choice = ask_for_admin_restart()
                if admin_choice == '1':
                    if restart_as_admin():
                        return
                    else:
                        print("❌ No se pudo reiniciar como administrador.")
                        print("Continuando con la desinstalación...")
                elif admin_choice == '3':
                    print("❌ Desinstalación cancelada.")
                    return
            
            # Ejecutar desinstalador
            success = run_uninstaller()
            show_final_message(success, "uninstall")
    
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()