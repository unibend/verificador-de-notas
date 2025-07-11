from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QMessageBox,
                             QApplication)
from PySide6.QtCore import QThread, Signal, Qt
from .config_dialog import ConfigDialog

class GradeCheckerThread(QThread):
    finished = Signal(list)  # Signal to emit when checking is done

    def __init__(self, checker):
        super().__init__()
        self.checker = checker

    def run(self):
        changes = self.checker.check_grades()
        self.finished.emit(changes)

class MainWindow(QMainWindow):
    def __init__(self, checker, parent=None):
        super().__init__(parent)
        self.checker = checker
        self.setWindowTitle("Verificador de Notas")
        self.setMinimumSize(600, 400)
        
        # Initialize checker thread
        self.checker_thread = None
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create top button layout
        top_button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("Verificar Notas")
        self.check_button.clicked.connect(self.check_grades)
        top_button_layout.addWidget(self.check_button)
        
        config_button = QPushButton("Configuración")
        config_button.clicked.connect(self.show_config)
        top_button_layout.addWidget(config_button)
        
        # Add minimize and quit buttons to the right
        top_button_layout.addStretch()  # This pushes the following buttons to the right
        
        minimize_button = QPushButton("Minimizar")
        minimize_button.clicked.connect(self.hide)
        top_button_layout.addWidget(minimize_button)
        
        quit_button = QPushButton("Salir")
        quit_button.clicked.connect(self.quit_app)
        top_button_layout.addWidget(quit_button)
        
        # Add top button layout to main layout
        layout.addLayout(top_button_layout)
        
        # Create grade display
        self.grade_display = QTextEdit()
        self.grade_display.setReadOnly(True)
        layout.addWidget(self.grade_display)
        
        # Create accept button layout (below grade display, aligned right)
        accept_layout = QHBoxLayout()
        accept_layout.addStretch()  # This pushes the button to the right
        
        self.accept_button = QPushButton("Aceptar")
        self.accept_button.clicked.connect(self.restore_grade_display)
        self.accept_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.accept_button.setFixedWidth(100)  # Set a fixed width for the button
        self.accept_button.hide()  # Initially hidden
        accept_layout.addWidget(self.accept_button)
        
        # Add accept button layout AFTER the grade display
        layout.addLayout(accept_layout)
        
        # Add app info at the bottom
        info_label = QLabel("Verificador de Notas UNETI v2.0")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # Show initial grades
        self.show_initial_display()

    def show_initial_display(self):
        """Show initial grades display"""
        if not self.checker.is_configured():
            self.show_config()
        else:
            self.display_current_grades()

    def display_current_grades(self):
        """Display current grades"""
        self.grade_display.clear()
        grades = self.checker.get_current_grades_display()
        self.grade_display.setPlainText(grades)

    def check_grades(self):
        """Run grade check and display results"""
        # Clear display and show checking message
        self.grade_display.clear()
        self.grade_display.append("Verificando calificaciones...\n")
        QApplication.processEvents()
        
        # Disable check button while checking
        self.check_button.setEnabled(False)
        
        # Create and start checker thread
        self.checker_thread = GradeCheckerThread(self.checker)
        self.checker_thread.finished.connect(self.on_check_completed)
        self.checker_thread.start()

    def on_check_completed(self, changes):
        """Handle completion of grade checking"""
        # Clear the "checking" message
        self.grade_display.clear()
        
        if changes:
            self.grade_display.append("Se encontraron cambios:\n")
            for change in changes:
                self.grade_display.append(f"• {change}")
        else:
            self.grade_display.append("No se encontraron cambios en las calificaciones.")
        
        # Show accept button
        self.accept_button.show()
        
        # Clean up thread
        if self.checker_thread:
            self.checker_thread.deleteLater()
            self.checker_thread = None

    def restore_grade_display(self):
        """Restore normal grade display"""
        self.accept_button.hide()
        self.check_button.setEnabled(True)  # Re-enable the check button
        self.display_current_grades()

    def show_config(self):
        """Show configuration dialog"""
        dialog = ConfigDialog(self.checker, self)
        if dialog.exec():
            self.display_current_grades()

    def closeEvent(self, event):
        """Handle window close event"""
        event.ignore()  # Prevent window from closing
        self.hide()     # Hide window instead
        
    def quit_app(self):
        """Quit the application completely"""
        QApplication.instance().quit()