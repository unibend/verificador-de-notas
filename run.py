#!/usr/bin/env python3
"""
Smart Launcher for UNETI Grade Checker
Checks the configuration status and runs the appropriate script.
"""

import os
import sys
import re
import subprocess
import platform
from datetime import datetime

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

def check_grade_checker_file():
    """Check the grade_checker.py file and return its status"""
    script_dir = get_script_directory()
    grade_checker_path = os.path.join(script_dir, "grade_checker.py")
    
    print(f"📂 Buscando archivo en: {grade_checker_path}")
    
    # Check if file exists
    if not os.path.exists(grade_checker_path):
        return "missing", None, grade_checker_path
    
    try:
        # Read the file
        with open(grade_checker_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the API_TOKEN line
        token_match = re.search(r'API_TOKEN\s*=\s*["\']([^"\']+)["\']', content)
        
        if not token_match:
            return "malformed", None, grade_checker_path
        
        token_value = token_match.group(1)
        
        # Check token status
        if token_value == "placeholder":
            return "unconfigured", token_value, grade_checker_path
        elif len(token_value) < 10:
            return "invalid", token_value, grade_checker_path
        elif re.match(r'^[a-fA-F0-9]{32,}$', token_value):
            # Looks like a valid token (hex string, 32+ characters)
            return "configured", token_value, grade_checker_path
        else:
            return "unknown", token_value, grade_checker_path
            
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        return "error", None, grade_checker_path

def check_setup_file():
    """Check if setup.py exists"""
    script_dir = get_script_directory()
    setup_path = os.path.join(script_dir, "setup.py")

    if os.path.exists(setup_path):
        return True, setup_path
    else:
        return False, setup_path

def check_configurador_file():
    """Check if configurador.py exists"""
    script_dir = get_script_directory()
    configurador_path = os.path.join(script_dir, "configurador.py")
    
    if os.path.exists(configurador_path):
        return True, configurador_path
    else:
        return False, configurador_path

def run_script(script_path, script_name):
    """Run a Python script"""
    try:
        print(f"🚀 Ejecutando {script_name}...")
        print("-" * 40)
        
        # Change to script directory
        original_dir = os.getcwd()
        script_dir = os.path.dirname(script_path)
        os.chdir(script_dir)
        
        # Execute the script
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=False, text=True)
        
        # Restore original directory
        os.chdir(original_dir)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error al ejecutar {script_name}: {e}")
        return False

def show_help():
    """Show help information"""
    print("=" * 60)
    print("📖 AYUDA - VERIFICADOR DE NOTAS UNETI")
    print("=" * 60)
    print("Este lanzador detecta automáticamente qué hacer basándose en la configuración:")
    print()
    print("🔧 ESTADOS DETECTADOS:")
    print("• Sin configurar: Ejecuta el configurador automáticamente")
    print("• Configurado: Ejecuta el verificador de notas")
    print("• Error: Muestra información de diagnóstico")
    print()
    print("📁 ARCHIVOS NECESARIOS:")
    print("• grade_checker.py - Script principal del verificador")
    print("• configurador.py - Script de configuración inicial")
    print("• run.py - Este lanzador inteligente")
    print()
    print("🔍 DIAGNÓSTICO:")
    print("• Archivo faltante: Descargar archivos completos")
    print("• Token inválido: Ejecutar configurador nuevamente")
    print("• Error de conexión: Verificar internet y credenciales")
    print("=" * 60)

def main():
    """Main function"""
    print_banner()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            show_help()
            input("\nPresiona Enter para salir...")
            return
    
    # Check grade checker file status
    print("🔍 Verificando estado de configuración...")
    status, token_value, grade_checker_path = check_grade_checker_file()
    
    print(f"📋 Estado detectado: {status}")
    
    if status == "missing":
        print("❌ ARCHIVO FALTANTE")
        print("-" * 40)
        print(f"No se encontró el archivo 'grade_checker.py' en:")
        print(f"   {grade_checker_path}")
        print()
        print("🔧 SOLUCIÓN:")
        print("• Descargar todos los archivos del verificador")
        print("• Asegurarse de que estén en la misma carpeta")
        print("• Ejecutar este lanzador nuevamente")
        
    elif status == "unconfigured":
        print("⚙️ CONFIGURACIÓN REQUERIDA")
        print("-" * 40)
        print("El verificador no está configurado (token = 'placeholder')")
        print("Ejecutando configurador automáticamente...") # This line should ideally say "Ejecutando setup.py..."
        print()

        # Check if configurador exists
        # This part needs to be changed to check for setup.py instead of configurador.py
        setup_exists, setup_path = check_setup_file() # New function call
        
        if setup_exists:
            if run_script(setup_path, "setup"): # Run setup.py
                print("\n✅ Configuración completada!")
                print("El verificador ya está listo para usar.")
            else:
                print("\n❌ Error durante la configuración.")
        else:
            print(f"❌ No se encontró el archivo 'setup.py' en:") # Updated message
            print(f"   {setup_path}")
            print("Descarga todos los archivos del verificador.")
    
    elif status == "configured":
        print("✅ CONFIGURACIÓN VÁLIDA")
        print("-" * 40)
        print("Token de API configurado correctamente")
        print("Ejecutando verificador de notas...")
        print()
        
        if run_script(grade_checker_path, "verificador de notas"):
            print("\n✅ Verificación completada!")
        else:
            print("\n❌ Error durante la verificación.")
            print("Verifica tu conexión a internet y credenciales.")
    
    elif status == "invalid":
        print("❌ TOKEN INVÁLIDO")
        print("-" * 40)
        print(f"El token configurado parece ser inválido: '{token_value}'")
        print("Un token válido debería ser una cadena hexadecimal larga.")
        print()
        print("🔧 SOLUCIÓN:")
        print("• Ejecutar el configurador nuevamente")
        print("• Verificar credenciales de UNETI")
        print("• Verificar conexión a internet")
        
        # Ask if user wants to reconfigure
        print()
        while True:
            response = input("¿Quieres ejecutar el configurador ahora? (s/n): ").strip().lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                config_exists, configurador_path = check_configurador_file()
                if config_exists:
                    run_script(configurador_path, "configurador")
                else:
                    print("❌ No se encontró el configurador.")
                break
            elif response in ['n', 'no']:
                break
            else:
                print("Por favor, responde 's' para sí o 'n' para no.")
    
    elif status == "unknown":
        print("⚠️ TOKEN DESCONOCIDO")
        print("-" * 40)
        print(f"El token configurado tiene un formato inesperado: '{token_value[:20]}...'")
        print("Esto podría indicar:")
        print("• Un token válido con formato diferente")
        print("• Un token corrupto")
        print("• Modificación manual del archivo")
        print()
        print("🔧 RECOMENDACIÓN:")
        print("• Intentar ejecutar el verificador de todas formas")
        print("• Si falla, reconfigurar con el configurador")
        
        # Ask user what to do
        print()
        while True:
            response = input("¿Intentar ejecutar el verificador? (s/n): ").strip().lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                if run_script(grade_checker_path, "verificador de notas"):
                    print("\n✅ Verificación completada!")
                else:
                    print("\n❌ Error durante la verificación.")
                    print("Considera reconfigurar con el configurador.")
                break
            elif response in ['n', 'no']:
                break
            else:
                print("Por favor, responde 's' para sí o 'n' para no.")
    
    elif status == "malformed":
        print("❌ ARCHIVO CORRUPTO")
        print("-" * 40)
        print("No se pudo encontrar la línea API_TOKEN en el archivo.")
        print("El archivo podría estar corrupto o modificado incorrectamente.")
        print()
        print("🔧 SOLUCIÓN:")
        print("• Descargar una copia nueva del verificador")
        print("• Restaurar desde el backup (grade_checker.py.backup)")
        print("• Ejecutar el configurador nuevamente")
    
    elif status == "error":
        print("❌ ERROR DE LECTURA")
        print("-" * 40)
        print("No se pudo leer el archivo grade_checker.py")
        print("Verifica permisos de archivo y integridad.")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print(f"• Archivo principal: {grade_checker_path}")
    print(f"• Estado: {status}")
    print(f"• Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if status == "configured":
        print("• ✅ Listo para usar")
    elif status == "unconfigured":
        print("• ⚙️ Configuración requerida")
    else:
        print("• ❌ Requiere atención")
    
    print("=" * 60)
    
    # Keep window open
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