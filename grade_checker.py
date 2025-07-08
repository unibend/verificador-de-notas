import requests
import json
import os
from datetime import datetime
import hashlib
import platform
import sys
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
    print("⚠️  Desktop notifications not available.")

class MoodleGradeChecker:
    def __init__(self, base_url, token, max_grade=20):
        self.base_url = base_url
        self.token = token
        self.max_grade = max_grade  # Maximum grade for the entire course
        self.api_url = f"{base_url}/webservice/rest/server.php"
        self.grades_file = "previous_grades.json"
        self.history_file = "grade_history.txt"
    
    def send_notification(self, title, message, grade_details=None):
        """Send a desktop notification or dialog"""
        if not NOTIFICATIONS_AVAILABLE:
            print(f"🔔 Notification: {title} - {message}")
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
                    print(f"Warning: Could not play sound: {sound_e}")
                
                # Show dialog box
                if grade_details:
                    course_name = grade_details.get('course', 'Unknown Course')
                    assignment_name = grade_details.get('assignment', 'Unknown Assignment')
                    new_grade = grade_details.get('new_grade', 'Unknown')
                    old_grade = grade_details.get('old_grade', None)
                    
                    if old_grade:
                        dialog_message = f"Your grade in '{course_name}' for assignment '{assignment_name}' has been updated.\n\nPrevious grade: {old_grade}\nNew grade: {new_grade}"
                    else:
                        dialog_message = f"You have received a new grade in '{course_name}' for assignment '{assignment_name}'.\n\nYour grade: {new_grade}"
                    
                    messagebox.showinfo("🎓 Grade Update", dialog_message)
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
            print(f"Failed to send notification: {e}")
            print(f"🔔 Notification: {title} - {message}")
    
    def make_api_call(self, function, params=None):
        """Make a call to Moodle API"""
        data = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json'
        }
        
        if params:
            data.update(params)
        
        print(f"  Making API call: {function}")
        
        try:
            response = requests.post(self.api_url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Check for Moodle API errors
            if isinstance(result, dict) and 'exception' in result:
                print(f"  Moodle API Error: {result.get('message', 'Unknown error')}")
                return None
            
            print(f"  API call successful")
            return result
            
        except requests.exceptions.Timeout:
            print(f"  API call timed out after 30 seconds")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"  Failed to parse JSON response: {e}")
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
                        print(f"    Skipping course total item: {item_name}")
                        continue
                    
                    # Extract relevant information
                    grade_item = {
                        'id': item.get('id'),
                        'itemname': item_name,
                        'graderaw': item.get('graderaw'),
                        'gradeformatted': item.get('gradeformatted', 'No grade'),
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
        print("  Getting enrolled courses...")
        courses = self.get_enrolled_courses()
        if not courses:
            print("  Failed to get courses")
            return None
        
        print(f"  Found {len(courses)} enrolled courses")
        all_grades = {}
        
        for i, course in enumerate(courses, 1):
            course_id = course['id']
            course_name = course['fullname']
            
            print(f"  Processing course {i}/{len(courses)}: {course_name}")
            
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
                print(f"    Retrieved {len(grade_items)} grade items ({graded_count} graded)")
                if graded_count > 0:
                    print(f"    Course grade: {achieved:.2f}/{possible} ({percentage:.2f}%)")
            else:
                print(f"    No grades found for this course")
        
        print(f"  Total courses with grades: {len(all_grades)}")
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
                f.write("MOODLE GRADE HISTORY LOG\n")
                f.write("=" * 80 + "\n")
                f.write(f"Log started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Maximum course grade: {self.max_grade}\n")
                f.write("=" * 80 + "\n\n")
    
    def log_to_history(self, message, course_name=None, grade_item=None, old_grade=None, new_grade=None):
        """Log a message to the history file"""
        self.init_history_file()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
            if course_name:
                f.write(f"    Course: {course_name}\n")
            
            if grade_item:
                f.write(f"    Assignment: {grade_item}\n")
            
            if old_grade is not None and new_grade is not None:
                f.write(f"    Grade Change: {old_grade} → {new_grade}\n")
            elif new_grade is not None:
                f.write(f"    Grade: {new_grade}\n")
            
            f.write("\n")
    
    def format_grade_display(self, grade_item):
        """Format grade for display"""
        item_name = grade_item.get('itemname', 'Unknown')
        grade_raw = grade_item.get('graderaw')
        
        if grade_raw is not None:
            return f"{item_name}: {grade_raw} points"
        else:
            return f"{item_name}: No grade"
    
    def log_course_summary(self, course_name, course_data):
        """Log a complete course summary to history"""
        self.init_history_file()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        grade_items = course_data.get('grades', [])
        
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] COURSE SUMMARY: {course_name}\n")
            f.write("-" * 60 + "\n")
            
            # Course statistics
            percentage = course_data.get('percentage', 0)
            achieved = course_data.get('total_achieved', 0)
            possible = course_data.get('total_possible', 0)
            graded_count = course_data.get('graded_assignments', 0)
            
            f.write(f"    Course Grade: {achieved:.2f}/{possible} ({percentage:.2f}%)\n")
            f.write(f"    Graded Assignments: {graded_count}/{len(grade_items)}\n")
            f.write(f"    Maximum Course Grade: {self.max_grade}\n")
            f.write("-" * 60 + "\n")
            
            if not grade_items:
                f.write("    No grade items found\n")
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
            self.log_to_history("FIRST RUN - Establishing baseline grades")
            
            for course_name, course_data in current_grades.items():
                self.log_to_history("New course discovered", course_name=course_name)
                self.log_course_summary(course_name, course_data)
                
                graded_count = course_data.get('graded_assignments', 0)
                percentage = course_data.get('percentage', 0)
                achieved = course_data.get('total_achieved', 0)
                
                if graded_count > 0:
                    changes.append(f"Baseline established for {course_name} ({achieved:.2f}/{self.max_grade}, {percentage:.2f}%)")
                else:
                    changes.append(f"Baseline established for {course_name} (no grades yet)")
            
            return changes, notification_messages
        
        prev_grades = previous_grades['grades']
        
        # Check each current course
        for course_name, course_data in current_grades.items():
            current_items = course_data.get('grades', [])
            
            if course_name not in prev_grades:
                # New course
                changes.append(f"New course detected: {course_name}")
                notification_messages.append(f"🎓 New course enrolled: {course_name}")
                self.log_to_history("New course enrolled", course_name=course_name)
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
                item_name = current_item.get('itemname', 'Unknown')
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
                        prev_display = f"{prev_grade} points" if prev_grade is not None else "No grade"
                        current_display = f"{current_grade} points" if current_grade is not None else "No grade"
                        
                        change_msg = f"Grade changed in {course_name} - {item_name}: {prev_display} → {current_display}"
                        changes.append(change_msg)
                        grade_changes_in_course.append(f"{item_name}: {prev_display} → {current_display}")
                        
                        # Send individual notification for this grade change
                        grade_details = {
                            'course': course_name,
                            'assignment': item_name,
                            'old_grade': prev_display,
                            'new_grade': current_display
                        }
                        self.send_notification("🎓 Grade Update", "", grade_details)
                        
                        self.log_to_history("Grade updated", 
                                          course_name=course_name, 
                                          grade_item=item_name,
                                          old_grade=prev_display, 
                                          new_grade=current_display)
                else:
                    # New grade item
                    if current_grade is not None:  # Only notify if there's actually a grade
                        grade_display = f"{current_grade} points"
                        change_msg = f"New grade item in {course_name}: {item_name} - {grade_display}"
                        changes.append(change_msg)
                        grade_changes_in_course.append(f"New: {item_name} - {grade_display}")
                        
                        # Send individual notification for this new grade
                        grade_details = {
                            'course': course_name,
                            'assignment': item_name,
                            'old_grade': None,
                            'new_grade': grade_display
                        }
                        self.send_notification("🎓 New Grade", "", grade_details)
                        
                        self.log_to_history("New grade item", 
                                          course_name=course_name, 
                                          grade_item=item_name,
                                          new_grade=grade_display)
            
            # Check for total grade changes
            if abs(current_achieved - prev_achieved) > 0.01:  # More than 0.01 point change
                grade_change = current_achieved - prev_achieved
                sign = "+" if grade_change > 0 else ""
                changes.append(f"Total grade changed for {course_name}: {prev_achieved:.2f} → {current_achieved:.2f} ({sign}{grade_change:.2f} points)")
                
                self.log_to_history(f"Course total updated: {prev_achieved:.2f} → {current_achieved:.2f} points", 
                                  course_name=course_name)
            
            # Check for percentage changes
            if abs(current_percentage - prev_percentage) > 0.01:  # More than 0.01% change
                percentage_change = current_percentage - prev_percentage
                sign = "+" if percentage_change > 0 else ""
                changes.append(f"Course percentage changed for {course_name}: {prev_percentage:.2f}% → {current_percentage:.2f}% ({sign}{percentage_change:.2f}%)")
                
                self.log_to_history(f"Course percentage updated: {prev_percentage:.2f}% → {current_percentage:.2f}%", 
                                  course_name=course_name)
            
            # Create summary notification for course if there were changes
            if grade_changes_in_course:
                # Don't send the old bulk notification since we're sending individual ones
                pass
        
        # Check for courses that were dropped
        for course_name in prev_grades:
            if course_name not in current_grades:
                changes.append(f"Course no longer enrolled: {course_name}")
                self.log_to_history("Course dropped", course_name=course_name)
        
        return changes, notification_messages
    
    def check_grades(self):
        """Main function to check for grade changes"""
        print("Checking grades...")
        
        # Log the check attempt
        self.log_to_history("Grade check initiated")
        
        # Get current grades
        print("Retrieving current grades from Moodle...")
        current_grades = self.get_all_grades()
        if not current_grades:
            print("❌ Failed to retrieve grades")
            self.log_to_history("ERROR: Failed to retrieve grades from Moodle")
            return
        
        print("✅ Successfully retrieved grades")
        
        # Load previous grades
        print("Loading previous grades...")
        previous_grades = self.load_previous_grades()
        
        # Compare grades
        print("Comparing grades...")
        changes, notification_messages = self.compare_grades(current_grades, previous_grades)
        
        # Save current grades
        print("Saving current grades...")
        self.save_current_grades(current_grades)
        
        # Send notifications if there are changes - now handled individually
        # No bulk notifications needed since we send individual dialogs
        
        # Report changes
        print("\n" + "="*70)
        if changes:
            print(f"🎯 Found {len(changes)} grade changes:")
            for change in changes:
                print(f"  • {change}")
            
            self.log_to_history(f"Grade check completed - {len(changes)} changes detected")
        else:
            print("✅ No grade changes detected")
            self.log_to_history("Grade check completed - No changes detected")
        
        print("="*70)
        print(f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"History log: {self.history_file}")
        print(f"Data file: {self.grades_file}")
        
        # Show summary
        total_courses = len(current_grades)
        total_items = sum(len(course['grades']) for course in current_grades.values())
        graded_items = sum(course.get('graded_assignments', 0) for course in current_grades.values())
        
        print(f"Monitoring: {total_courses} courses, {total_items} grade items ({graded_items} with grades)")
        
        # Show course grades (corrected calculation)
        print("\nCourse Progress:")
        for course_name, course_data in current_grades.items():
            percentage = course_data.get('percentage', 0)
            achieved = course_data.get('total_achieved', 0)
            possible = course_data.get('total_possible', 0)
            graded_count = course_data.get('graded_assignments', 0)
            total_assignments = len(course_data.get('grades', []))
            
            print(f"  📚 {course_name}")
            print(f"      Grade: {achieved:.2f}/{possible} ({percentage:.2f}%)")
            print(f"      Assignments: {graded_count}/{total_assignments} graded")

# Usage example
if __name__ == "__main__":
    # You'll need to replace these with your actual values
    MOODLE_URL = "https://www.uneti.edu.ve/campus/"
    API_TOKEN = "placeholder"
    
    # Create checker with max grade of 20 (for entire course, not per assignment)
    checker = MoodleGradeChecker(MOODLE_URL, API_TOKEN, max_grade=20)
    checker.check_grades()
