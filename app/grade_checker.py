import requests
import json
import os
import hashlib
from datetime import datetime
import platform
import sys
import keyring
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox
import winsound

class MoodleGradeChecker:
    def __init__(self):
        self.base_url = "https://www.uneti.edu.ve/campus/"  # Fixed URL from CLI version
        self.api_url = f"{self.base_url}/webservice/rest/server.php"
        self.max_grade = 20
        
        # File paths
        self.data_dir = os.path.expanduser("~/.verificador-notas")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.grades_file = os.path.join(self.data_dir, "previous_grades.json")
        self.current_grades_file = os.path.join(self.data_dir, "notas_actuales.txt")
        self.history_file = os.path.join(self.data_dir, "grade_history.txt")
        
        # Settings
        self.settings = QSettings("VerificadorNotas", "Settings")
        
        # Get stored token if available
        self.token = self.get_token_from_keyring()

    def is_configured(self):
        """Check if the app is configured"""
        return bool(self.token)
    
    def has_stored_credentials(self):
        """Check if credentials are stored"""
        return bool(self.get_token_from_keyring())
    
    def is_automation_enabled(self):
        """Check if automation is enabled"""
        return self.settings.value("automation/enabled", False, type=bool)
    
    def get_automation_interval(self):
        """Get automation interval in minutes"""
        return self.settings.value("automation/interval", 30, type=int)

    def get_token_from_keyring(self):
        """Retrieve API token from keyring"""
        try:
            username = self.settings.value("credentials/username")
            if username:
                return keyring.get_password("verificador-notas", username)
        except Exception as e:
            print(f"Error retrieving token: {e}")
        return None

    def store_credentials(self, username, password):
        """Store user credentials securely"""
        try:
            # Get token from Moodle
            token = self.get_token(username, password)
            if token:
                # Store token in keyring
                keyring.set_password("verificador-notas", username, token)
                self.settings.setValue("credentials/username", username)
                self.token = token
                return True
            return False
        except Exception as e:
            print(f"Error storing credentials: {e}")
            return False

    def get_token(self, username, password):
        """Get token from Moodle"""
        data = {
            'username': username,
            'password': password,
            'service': 'moodle_mobile_app'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/login/token.php",
                data=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if 'token' in result:
                return result['token']
            return None
            
        except Exception as e:
            print(f"Error getting token: {e}")
            return None

    def clear_credentials(self):
        """Remove stored credentials"""
        try:
            username = self.settings.value("credentials/username")
            if username:
                keyring.delete_password("verificador-notas", username)
            self.settings.remove("credentials/username")
            self.token = None
        except:
            pass

    def enable_automation(self, interval):
        """Enable automated grade checking"""
        self.settings.setValue("automation/enabled", True)
        self.settings.setValue("automation/interval", interval)

    def disable_automation(self):
        """Disable automated grade checking"""
        self.settings.setValue("automation/enabled", False)

    def validate_token(self):
        """Validate that the token works"""
        if not self.token:
            return False
        try:
            user_info = self.get_user_info()
            return bool(user_info and 'userid' in user_info)
        except Exception as e:
            print(f"Error validating token: {e}")
            return False

    def make_api_call(self, function, params=None):
        """Make a call to Moodle API"""
        if not self.token:
            return None

        data = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json'
        }
        if params:
            data.update(params)

        try:
            response = requests.post(self.api_url, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, dict) and 'exception' in result:
                return None
                
            return result
        except Exception as e:
            print(f"API call error: {e}")
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

    def send_notification(self, title, message, grade_details=None):
        """Send a desktop notification"""
        try:
            if platform.system() == "Windows":
                # Play Windows notification sound
                winsound.MessageBeep(winsound.MB_OK)
                
                if grade_details:
                    course_name = grade_details.get('course', 'Curso Desconocido')
                    assignment_name = grade_details.get('assignment', 'Tarea Desconocida')
                    new_grade = grade_details.get('new_grade', 'Desconocido')
                    old_grade = grade_details.get('old_grade', None)
                    
                    if old_grade:
                        dialog_message = f"Tu calificación en '{course_name}' para la tarea '{assignment_name}' ha sido actualizada.\n\nCalificación anterior: {old_grade}\nNueva calificación: {new_grade}"
                    else:
                        dialog_message = f"Has recibido una nueva calificación en '{course_name}' para la tarea '{assignment_name}'.\n\nTu calificación: {new_grade}"
                    
                    QMessageBox.information(None, "🎓 Actualización de Calificación", dialog_message)
                else:
                    QMessageBox.information(None, title, message)
        except Exception as e:
            print(f"Error sending notification: {e}")

    def extract_grade_items(self, grades_data):
        """Extract individual grade items from the nested structure"""
        grade_items = []
        
        if not grades_data or 'usergrades' not in grades_data:
            return grade_items
        
        for user_grade in grades_data['usergrades']:
            if 'gradeitems' in user_grade:
                for item in user_grade['gradeitems']:
                    item_name = item.get('itemname')
                    
                    if not item_name or item_name.lower() in ['none', 'null', '']:
                        continue
                    
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

    def get_all_grades(self):
        """Get all grades from all enrolled courses"""
        courses = self.get_enrolled_courses()
        if not courses:
            return None

        all_grades = {}
        
        for course in courses:
            course_id = course['id']
            course_name = course['fullname']
            
            grades_data = self.get_grades_for_course(course_id)
            grade_items = self.extract_grade_items(grades_data)
            
            if grade_items:
                percentage, achieved, possible, graded_count = self.calculate_course_percentage(grade_items)
                
                all_grades[course_name] = {
                    'course_id': course_id,
                    'grades': grade_items,
                    'percentage': percentage,
                    'total_achieved': achieved,
                    'total_possible': possible,
                    'graded_assignments': graded_count
                }
        
        return all_grades

    def calculate_course_percentage(self, grade_items):
        """Calculate the percentage of maximum course grade achieved"""
        total_achieved = 0
        graded_count = 0
        
        for item in grade_items:
            if item.get('graderaw') is not None:
                graded_count += 1
                total_achieved += item.get('graderaw', 0)
        
        if graded_count == 0:
            return 0, 0, self.max_grade, 0
        
        percentage = (total_achieved / self.max_grade) * 100
        percentage = min(percentage, 100)
        
        return percentage, total_achieved, self.max_grade, graded_count

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

    def write_current_grades_to_file(self, current_grades):
        """Write the current grades to notas_actuales.txt"""
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
        except Exception as e:
            print(f"Error writing current grades to file: {e}")

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

    def compare_grades(self, current_grades, previous_grades):
        """Compare current grades with previous grades"""
        changes = []
        notification_messages = []
        
        if not previous_grades or 'grades' not in previous_grades:
            # First run - log all courses
            self.log_to_history("PRIMERA EJECUCIÓN - Estableciendo calificaciones base")
            for course_name, course_data in current_grades.items():
                self.log_to_history("Nuevo curso descubierto", course_name=course_name)
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
                changes.append(f"Nuevo curso detectado: {course_name}")
                notification_messages.append(f"🎓 Nuevo curso inscrito: {course_name}")
                self.log_to_history("Nuevo curso inscrito", course_name=course_name)
                continue
            
            previous_items = prev_grades[course_name].get('grades', [])
            prev_percentage = prev_grades[course_name].get('percentage', 0)
            prev_achieved = prev_grades[course_name].get('total_achieved', 0)
            current_percentage = course_data.get('percentage', 0)
            current_achieved = course_data.get('total_achieved', 0)
            
            for current_item in current_items:
                item_name = current_item.get('itemname', 'Desconocido')
                item_id = current_item.get('id')
                current_grade = current_item.get('graderaw')
                
                previous_item = next((item for item in previous_items 
                                    if item.get('id') == item_id or 
                                    item.get('itemname') == item_name), None)
                
                if previous_item:
                    prev_grade = previous_item.get('graderaw')
                    if current_grade != prev_grade:
                        prev_display = f"{prev_grade} puntos" if prev_grade is not None else "Sin calificación"
                        current_display = f"{current_grade} puntos" if current_grade is not None else "Sin calificación"
                        
                        change_msg = f"Calificación cambiada en {course_name} - {item_name}: {prev_display} → {current_display}"
                        changes.append(change_msg)
                        
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
                    if current_grade is not None:
                        grade_display = f"{current_grade} puntos"
                        change_msg = f"Nuevo elemento de calificación en {course_name}: {item_name} - {grade_display}"
                        changes.append(change_msg)
                        
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
        
        return changes, notification_messages

    def check_grades(self):
        """Check for grade changes and return list of changes"""
        if not self.validate_token():
            return ["❌ Error: Token inválido o faltante"]
        
        try:
            current_grades = self.get_all_grades()
            if not current_grades:
                return ["❌ Error al recuperar calificaciones"]
            
            previous_grades = self.load_previous_grades()
            
            changes, _ = self.compare_grades(current_grades, previous_grades)
            
            self.save_current_grades(current_grades)
            self.write_current_grades_to_file(current_grades)
            
            return changes if changes else []
            
        except Exception as e:
            return [f"❌ Error: {str(e)}"]
            
    def get_current_grades_display(self):
        """Get formatted string of current grades"""
        if not self.is_configured():
            return "No hay calificaciones disponibles.\nPor favor, configure sus credenciales primero."
            
        if os.path.exists(self.current_grades_file):
            try:
                with open(self.current_grades_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        return content
                    return "No hay calificaciones disponibles aún.\nUse el botón 'Verificar Notas Ahora' para obtener sus calificaciones."
            except Exception as e:
                print(f"Error reading grades file: {e}")
        return "No hay calificaciones disponibles.\nUse el botón 'Verificar Notas Ahora' para obtener sus calificaciones."