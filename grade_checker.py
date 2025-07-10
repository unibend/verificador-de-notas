import requests
import json
import os
from datetime import datetime
import hashlib
import platform
import sys
import getpass
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Cross-platform notification support
try:
    if platform.system() == "Windows":
        import tkinter as tk
        from tkinter import messagebox
        import winsound # Import winsound here
        NOTIFICATIONS_AVAILABLE = True
    elif platform.system() == "Darwin":  # macOS
        import pync
        NOTIFICATIONS_AVAILABLE = True
    else:  # Linux
        import subprocess
        NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("⚠️  Notificaciones de escritorio no disponibles.")

# Keyring support for secure token storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    print("⚠️  Keyring no disponible. Almacenamiento seguro de tokens deshabilitado.")

class MoodleGradeChecker:
    def __init__(self, base_url, token=None, max_grade=20):
        self.base_url = base_url
        self.max_grade = max_grade  # Maximum grade for the entire course
        self.api_url = f"{base_url}/webservice/rest/server.php"
        self.grades_file = "previous_grades.json"
        self.history_file = "grade_history.txt"
        self.current_grades_file = "notas_actuales.txt"
        self.config_file = "config.json"
        self.service_name = "UNETI-Grade-Checker"
        
        # Get token from keyring or use provided token
        if token:
            self.token = token
        else:
            self.token = self.get_token_from_keyring()
    
    def load_config(self):
        """Load configuration from config.json"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"❌ Error al cargar configuración: {e}")
            return None
    
    def get_token_from_keyring(self):
        """Retrieve API token from keyring using config file"""
        if not KEYRING_AVAILABLE:
            print("❌ Keyring no disponible. No se puede recuperar el token almacenado.")
            return None
        
        try:
            # Load username from config file
            config = self.load_config()
            if not config or 'username' not in config:
                print("❌ No se encontró configuración.")
                print("Por favor, ejecuta el configurador primero para configurar tus credenciales.")
                return None
            
            username = config['username']
            service_name = config.get('service_name', self.service_name)
            
            token = keyring.get_password(service_name, username)
            if not token:
                print(f"❌ No se encontró token para el usuario: {username}")
                print("Por favor, ejecuta el configurador para configurar tus credenciales.")
                return None
            
            print(f"✅ Token recuperado del keyring para el usuario: {username}")
            return token
            
        except Exception as e:
            print(f"❌ Error al recuperar token del keyring: {e}")
            return None
    
    def get_stored_username(self):
        """Get the stored username from config file"""
        config = self.load_config()
        if config and 'username' in config:
            return config['username']
        return None
    
    def validate_token(self):
        """Validate that the token works"""
        if not self.token:
            return False
        
        try:
            user_info = self.get_user_info()
            if user_info and 'userid' in user_info:
                print(f"✅ Validación de token exitosa. ID de usuario: {user_info['userid']}")
                return True
            else:
                print("❌ Validación de token falló.")
                return False
        except Exception as e:
            print(f"❌ Error al validar token: {e}")
            return False
    
    def send_notification(self, title, message, grade_details=None):
        """Send a desktop notification or dialog"""
        if not NOTIFICATIONS_AVAILABLE:
            print(f"🔔 Notificación: {title} - {message}")
            return
        
        try:
            system = platform.system()
            if system == "Windows":
                # Create a proper Windows dialog box
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                root.attributes('-topmost', True)  # Keep on top
                
                # Play Windows notification sound
                try:
                    # Use MB_OK for a general notification sound
                    winsound.MessageBeep(winsound.MB_OK) 
                except Exception as sound_e:
                    print(f"Advertencia: No se pudo reproducir sonido: {sound_e}")
                
                # Show dialog box
                if grade_details:
                    course_name = grade_details.get('course', 'Curso Desconocido')
                    assignment_name = grade_details.get('assignment', 'Tarea Desconocida')
                    new_grade = grade_details.get('new_grade', 'Desconocido')
                    old_grade = grade_details.get('old_grade', None)
                    
                    if old_grade:
                        dialog_message = f"Tu calificación en '{course_name}' para la tarea '{assignment_name}' ha sido actualizada.\n\nCalificación anterior: {old_grade}\nNueva calificación: {new_grade}"
                    else:
                        dialog_message = f"Has recibido una nueva calificación en '{course_name}' para la tarea '{assignment_name}'.\n\nTu calificación: {new_grade}"
                    
                    messagebox.showinfo("🎓 Actualización de Calificación", dialog_message)
                else:
                    messagebox.showinfo(title, message)
                
                root.destroy()
                
            elif system == "Darwin":  # macOS
                pync.notify(message, title=title, timeout=10, sound='default')
            else:  # Linux
                subprocess.run([
                    'notify-send', 
                    '--expire-time', '10000',
                    '--urgency', 'normal',
                    title, 
                    message
                ], check=False)
        except Exception as e:
            print(f"Error al enviar notificación: {e}")
            print(f"🔔 Notificación: {title} - {message}")
    
    def make_api_call(self, function, params=None):
        """Make a call to Moodle API"""
        if not self.token:
            print("❌ No hay token de API disponible")
            return None
        
        data = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json'
        }
        
        if params:
            data.update(params)
        
        print(f"  Realizando llamada a API: {function}")
        
        try:
            response = requests.post(self.api_url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Check for Moodle API errors
            if isinstance(result, dict) and 'exception' in result:
                print(f"  Error de API de Moodle: {result.get('message', 'Error desconocido')}")
                return None
            
            print(f"  Llamada a API exitosa")
            return result
            
        except requests.exceptions.Timeout:
            print(f"  Tiempo de espera agotado después de 30 segundos")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  Solicitud de API falló: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"  Error al analizar respuesta JSON: {e}")
            return None
    
    def get_user_info(self):
        """Get current user information"""
        return self.make_api_call('core_webservice_get_site_info')
    
    def get_enrolled_courses(self):
        """Get courses the user is enrolled in"""
        user_info = self.get_user_info()
        if not user_info or 'userid' not in user_info:
            return None
        
        return self.make_api_call('core_enrol_get_users_courses', 
                                {'userid': user_info['userid']})
    
    def get_grades_for_course(self, course_id):
        """Get grades for a specific course"""
        user_info = self.get_user_info()
        if not user_info or 'userid' not in user_info:
            return None
        
        return self.make_api_call('gradereport_user_get_grade_items',
                                {'courseid': course_id, 'userid': user_info['userid']})
    
    def extract_grade_items(self, grades_data):
        """Extract individual grade items from the nested structure"""
        grade_items = []
        
        if not grades_data or 'usergrades' not in grades_data:
            return grade_items
        
        for user_grade in grades_data['usergrades']:
            if 'gradeitems' in user_grade:
                for item in user_grade['gradeitems']:
                    item_name = item.get('itemname')
                    
                    # Skip items with null/empty itemname or 'none' (these are course totals)
                    if not item_name or item_name.lower() in ['none', 'null', '']:
                        print(f"    Omitiendo elemento total del curso: {item_name}")
                        continue
                    
                    # Extract relevant information
                    grade_item = {
                        'id': item.get('id'),
                        'itemname': item_name,
                        'graderaw': item.get('graderaw'),
                        'gradeformatted': item.get('gradeformatted', 'Sin calificación'),
                        'grademax': item.get('grademax'),
                        'grademin': item.get('grademin'),
                        'percentageformatted': item.get('percentageformatted', 'N/A'),
                        'gradedategraded': item.get('gradedategraded')
                    }
                    grade_items.append(grade_item)
        
        return grade_items
    
    def calculate_course_percentage(self, grade_items):
        """Calculate the percentage of maximum course grade achieved"""
        total_achieved = 0
        graded_count = 0
        
        for item in grade_items:
            # Only count items that have been graded
            if item.get('graderaw') is not None:
                graded_count += 1
                total_achieved += item.get('graderaw', 0)
        
        if graded_count == 0:
            return 0, 0, self.max_grade, 0  # percentage, achieved, possible, graded_count
        
        # Calculate percentage based on course maximum (20), not per assignment
        percentage = (total_achieved / self.max_grade) * 100
        
        # Cap at 100% in case total exceeds maximum
        percentage = min(percentage, 100)
        
        return percentage, total_achieved, self.max_grade, graded_count
    
    def get_all_grades(self):
        """Get all grades from all enrolled courses"""
        print("  Obteniendo cursos inscritos...")
        courses = self.get_enrolled_courses()
        if not courses:
            print("  Error al obtener cursos")
            return None
        
        print(f"  Encontrados {len(courses)} cursos inscritos")
        all_grades = {}
        
        for i, course in enumerate(courses, 1):
            course_id = course['id']
            course_name = course['fullname']
            
            print(f"  Procesando curso {i}/{len(courses)}: {course_name}")
            
            grades_data = self.get_grades_for_course(course_id)
            grade_items = self.extract_grade_items(grades_data)
            
            if grade_items:
                # Calculate course percentage
                percentage, achieved, possible, graded_count = self.calculate_course_percentage(grade_items)
                
                all_grades[course_name] = {
                    'course_id': course_id,
                    'grades': grade_items,
                    'percentage': percentage,
                    'total_achieved': achieved,
                    'total_possible': possible,
                    'graded_assignments': graded_count
                }
                print(f"    Recuperados {len(grade_items)} elementos de calificación ({graded_count} calificados)")
                if graded_count > 0:
                    print(f"    Calificación del curso: {achieved:.2f}/{possible} ({percentage:.2f}%)")
            else:
                print(f"    No se encontraron calificaciones para este curso")
        
        print(f"  Total de cursos con calificaciones: {len(all_grades)}")
        return all_grades
    
    def load_previous_grades(self):
        """Load previously saved grades"""
        if os.path.exists(self.grades_file):
            try:
                with open(self.grades_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_current_grades(self, grades):
        """Save current grades to file"""
        with open(self.grades_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'grades': grades
            }, f, indent=2)
    
    def init_history_file(self):
        """Initialize the history file with headers if it doesn't exist"""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("REGISTRO DE HISTORIAL DE CALIFICACIONES MOODLE\n")
                f.write("=" * 80 + "\n")
                f.write(f"Registro iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Calificación máxima del curso: {self.max_grade}\n")
                f.write("=" * 80 + "\n\n")
    
    def log_to_history(self, message, course_name=None, grade_item=None, old_grade=None, new_grade=None):
        """Log a message to the history file"""
        self.init_history_file()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
            if course_name:
                f.write(f"    Curso: {course_name}\n")
            
            if grade_item:
                f.write(f"    Tarea: {grade_item}\n")
            
            if old_grade is not None and new_grade is not None:
                f.write(f"    Cambio de Calificación: {old_grade} → {new_grade}\n")
            elif new_grade is not None:
                f.write(f"    Calificación: {new_grade}\n")
            
            f.write("\n")
    
    def write_current_grades_to_file(self, current_grades):
        """Write the current grades to notas_actuales.txt"""
        print(f"Escribiendo calificaciones actuales a {self.current_grades_file}...")
        try:
            with open(self.current_grades_file, 'w', encoding='utf-8') as f:
                f.write(f"Calificaciones Actuales - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                for course_name, course_data in current_grades.items():
                    percentage = course_data.get('percentage', 0)
                    achieved = course_data.get('total_achieved', 0)
                    possible = course_data.get('total_possible', 0)
                    graded_count = course_data.get('graded_assignments', 0)
                    total_assignments = len(course_data.get('grades', []))
                    
                    f.write(f"📚 Curso: {course_name}\n")
                    f.write(f"    Calificación: {achieved:.2f}/{possible} ({percentage:.2f}%)\n")
                    f.write(f"    Tareas Calificadas: {graded_count}/{total_assignments}\n\n")
            print(f"✅ Calificaciones actuales guardadas en {self.current_grades_file}")
        except Exception as e:
            print(f"❌ Error al escribir calificaciones actuales a archivo: {e}")
            
    def format_grade_display(self, grade_item):
        """Format grade for display"""
        item_name = grade_item.get('itemname', 'Desconocido')
        grade_raw = grade_item.get('graderaw')
        
        if grade_raw is not None:
            return f"{item_name}: {grade_raw} puntos"
        else:
            return f"{item_name}: Sin calificación"
    
    def log_course_summary(self, course_name, course_data):
        """Log a complete course summary to history"""
        self.init_history_file()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        grade_items = course_data.get('grades', [])
        
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] RESUMEN DEL CURSO: {course_name}\n")
            f.write("-" * 60 + "\n")
            
            # Course statistics
            percentage = course_data.get('percentage', 0)
            achieved = course_data.get('total_achieved', 0)
            possible = course_data.get('total_possible', 0)
            graded_count = course_data.get('graded_assignments', 0)
            
            f.write(f"    Calificación del Curso: {achieved:.2f}/{possible} ({percentage:.2f}%)\n")
            f.write(f"    Tareas Calificadas: {graded_count}/{len(grade_items)}\n")
            f.write(f"    Calificación Máxima del Curso: {self.max_grade}\n")
            f.write("-" * 60 + "\n")
            
            if not grade_items:
                f.write("    No se encontraron elementos de calificación\n")
            else:
                for item in grade_items:
                    f.write(f"    {self.format_grade_display(item)}\n")
            
            f.write("\n")
    
    def compare_grades(self, current_grades, previous_grades):
        """Compare current grades with previous grades and log changes"""
        changes = []
        notification_messages = []
        
        if not previous_grades or 'grades' not in previous_grades:
            # First run - log all courses and grades
            self.log_to_history("PRIMERA EJECUCIÓN - Estableciendo calificaciones base")
            
            for course_name, course_data in current_grades.items():
                self.log_to_history("Nuevo curso descubierto", course_name=course_name)
                self.log_course_summary(course_name, course_data)
                
                graded_count = course_data.get('graded_assignments', 0)
                percentage = course_data.get('percentage', 0)
                achieved = course_data.get('total_achieved', 0)
                
                if graded_count > 0:
                    changes.append(f"Línea base establecida para {course_name} ({achieved:.2f}/{self.max_grade}, {percentage:.2f}%)")
                else:
                    changes.append(f"Línea base establecida para {course_name} (sin calificaciones aún)")
            
            return changes, notification_messages
        
        prev_grades = previous_grades['grades']
        
        # Check each current course
        for course_name, course_data in current_grades.items():
            current_items = course_data.get('grades', [])
            
            if course_name not in prev_grades:
                # New course
                changes.append(f"Nuevo curso detectado: {course_name}")
                notification_messages.append(f"🎓 Nuevo curso inscrito: {course_name}")
                self.log_to_history("Nuevo curso inscrito", course_name=course_name)
                self.log_course_summary(course_name, course_data)
                continue
            
            # Compare individual grade items
            previous_items = prev_grades[course_name].get('grades', [])
            prev_percentage = prev_grades[course_name].get('percentage', 0)
            prev_achieved = prev_grades[course_name].get('total_achieved', 0)
            current_percentage = course_data.get('percentage', 0)
            current_achieved = course_data.get('total_achieved', 0)
            
            grade_changes_in_course = []
            
            for current_item in current_items:
                item_name = current_item.get('itemname', 'Desconocido')
                item_id = current_item.get('id')
                current_grade = current_item.get('graderaw')
                
                # Find corresponding previous item by ID or name
                previous_item = None
                for prev_item in previous_items:
                    if (prev_item.get('id') == item_id or 
                        prev_item.get('itemname') == item_name):
                        previous_item = prev_item
                        break
                
                if previous_item:
                    prev_grade = previous_item.get('graderaw')
                    if current_grade != prev_grade:
                        prev_display = f"{prev_grade} puntos" if prev_grade is not None else "Sin calificación"
                        current_display = f"{current_grade} puntos" if current_grade is not None else "Sin calificación"
                        
                        change_msg = f"Calificación cambiada en {course_name} - {item_name}: {prev_display} → {current_display}"
                        changes.append(change_msg)
                        grade_changes_in_course.append(f"{item_name}: {prev_display} → {current_display}")
                        
                        # Send individual notification for this grade change
                        grade_details = {
                            'course': course_name,
                            'assignment': item_name,
                            'old_grade': prev_display,
                            'new_grade': current_display
                        }
                        self.send_notification("🎓 Actualización de Calificación", "", grade_details)
                        
                        self.log_to_history("Calificación actualizada", 
                                          course_name=course_name, 
                                          grade_item=item_name,
                                          old_grade=prev_display, 
                                          new_grade=current_display)
                else:
                    # New grade item
                    if current_grade is not None:  # Only notify if there's actually a grade
                        grade_display = f"{current_grade} puntos"
                        change_msg = f"Nuevo elemento de calificación en {course_name}: {item_name} - {grade_display}"
                        changes.append(change_msg)
                        grade_changes_in_course.append(f"Nuevo: {item_name} - {grade_display}")
                        
                        # Send individual notification for this new grade
                        grade_details = {
                            'course': course_name,
                            'assignment': item_name,
                            'old_grade': None,
                            'new_grade': grade_display
                        }
                        self.send_notification("🎓 Nueva Calificación", "", grade_details)
                        
                        self.log_to_history("Nuevo elemento de calificación", 
                                          course_name=course_name, 
                                          grade_item=item_name,
                                          new_grade=grade_display)
            
            # Check for total grade changes
            if abs(current_achieved - prev_achieved) > 0.01:  # More than 0.01 point change
                grade_change = current_achieved - prev_achieved
                sign = "+" if grade_change > 0 else ""
                changes.append(f"Calificación total cambiada para {course_name}: {prev_achieved:.2f} → {current_achieved:.2f} ({sign}{grade_change:.2f} puntos)")
                
                self.log_to_history(f"Total del curso actualizado: {prev_achieved:.2f} → {current_achieved:.2f} puntos", 
                                  course_name=course_name)
            
            # Check for percentage changes
            if abs(current_percentage - prev_percentage) > 0.01:  # More than 0.01% change
                percentage_change = current_percentage - prev_percentage
                sign = "+" if percentage_change > 0 else ""
                changes.append(f"Porcentaje del curso cambiado para {course_name}: {prev_percentage:.2f}% → {current_percentage:.2f}% ({sign}{percentage_change:.2f}%)")
                
                self.log_to_history(f"Porcentaje del curso actualizado: {prev_percentage:.2f}% → {current_percentage:.2f}%", 
                                  course_name=course_name)
            
            # Create summary notification for course if there were changes
            if grade_changes_in_course:
                # Don't send the old bulk notification since we're sending individual ones
                pass
        
        # Check for courses that were dropped
        for course_name in prev_grades:
            if course_name not in current_grades:
                changes.append(f"Curso ya no inscrito: {course_name}")
                self.log_to_history("Curso abandonado", course_name=course_name)
        
        return changes, notification_messages
    
    def check_grades(self):
        """Main function to check for grade changes"""
        print("Verificando calificaciones...")
        
        # Validate token first
        if not self.validate_token():
            print("❌ Token de API inválido o faltante.")
            if KEYRING_AVAILABLE:
                print("Por favor, ejecuta el configurador para configurar tus credenciales.")
            else:
                print("Por favor, instala keyring y ejecuta el configurador: pip install keyring")
            return
        
        # Log the check attempt
        self.log_to_history("Verificación de calificaciones iniciada")
        
        # Get current grades
        print("Recuperando calificaciones actuales de Moodle...")
        current_grades = self.get_all_grades()
        if not current_grades:
            print("❌ Error al recuperar calificaciones")
            self.log_to_history("ERROR: Error al recuperar calificaciones de Moodle")
            return
        
        print("✅ Calificaciones recuperadas exitosamente")
        
        # Load previous grades
        print("Cargando calificaciones anteriores...")
        previous_grades = self.load_previous_grades()
        
        # Compare grades
        print("Comparando calificaciones...")
        changes, notification_messages = self.compare_grades(current_grades, previous_grades)
        
        # Save current grades
        print("Guardando calificaciones actuales...")
        self.save_current_grades(current_grades)
        
        # Write current grades to the new file
        self.write_current_grades_to_file(current_grades)
        
        # Send notifications if there are changes - now handled individually
        # No bulk notifications needed since we send individual dialogs
        
        # Report changes
        print("\n" + "="*70)
        if changes:
            print(f"🎯 Se encontraron {len(changes)} cambios en las calificaciones:")
            for change in changes:
                print(f"  • {change}")
            
            self.log_to_history(f"Verificación de calificaciones completada - {len(changes)} cambios detectados")
        else:
            print("✅ No se detectaron cambios en las calificaciones")
            self.log_to_history("Verificación de calificaciones completada - No se detectaron cambios")
        
        print("="*70)
        print(f"Última verificación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Registro de historial: {self.history_file}")
        print(f"Archivo de datos: {self.grades_file}")
        
        # Show summary
        total_courses = len(current_grades)
        total_items = sum(len(course['grades']) for course in current_grades.values())
        graded_items = sum(course.get('graded_assignments', 0) for course in current_grades.values())
        
        print(f"Monitoreando: {total_courses} cursos, {total_items} elementos de calificación ({graded_items} con calificaciones)")
        
        # Show course grades (corrected calculation)
        print("\nProgreso de Cursos:")
        for course_name, course_data in current_grades.items():
            percentage = course_data.get('percentage', 0)
            achieved = course_data.get('total_achieved', 0)
            possible = course_data.get('total_possible', 0)
            graded_count = course_data.get('graded_assignments', 0)
            total_assignments = len(course_data.get('grades', []))
            
            print(f"  📚 {course_name}")
            print(f"      Calificación: {achieved:.2f}/{possible} ({percentage:.2f}%)")
            print(f"      Tareas: {graded_count}/{total_assignments} calificadas")

# Usage example
if __name__ == "__main__":
    # Moodle URL - this should remain constant
    MOODLE_URL = "https://www.uneti.edu.ve/campus/"
    
    # Create checker - token will be retrieved from keyring
    checker = MoodleGradeChecker(MOODLE_URL, max_grade=20)
    
    # Check if we have a valid token
    if checker.token:
        checker.check_grades()
    else:
        print("❌ No hay token de API disponible.")
        print("Por favor, ejecuta el configurador primero para configurar tus credenciales.")
        print("Ejecuta: python configurador.py")
