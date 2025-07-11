from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, QThread, Signal
import os

class AutoCheckThread(QThread):
    finished = Signal(list)

    def __init__(self, checker):
        super().__init__()
        self.checker = checker

    def run(self):
        changes = self.checker.check_grades()
        self.finished.emit(changes)

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, checker, main_window, parent=None):
        super().__init__(parent)
        self.checker = checker
        self.main_window = main_window
        self.setToolTip("Verificador de Notas")
        
        # Set the tray icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # Fallback to a system icon if our icon is not found
            self.setIcon(QIcon.fromTheme('application-x-executable'))
        
        # Initialize checker thread
        self.checker_thread = None
        
        # Create context menu
        menu = QMenu()
        
        self.show_action = menu.addAction("Mostrar Ventana")
        self.show_action.triggered.connect(self.show_window)
        
        self.check_action = menu.addAction("Verificar Notas")
        self.check_action.triggered.connect(self.check_grades)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("Salir")
        quit_action.triggered.connect(self.quit_app)
        
        self.setContextMenu(menu)
        
        # Connect activated signal for tray icon clicks
        self.activated.connect(self.tray_icon_activated)
        
        # Set up automation timer if enabled
        if self.checker.is_automation_enabled():
            self.setup_automation()

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.show_window()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Middle click
            self.check_grades()
    
    def setup_automation(self):
        """Set up automated grade checking"""
        interval = self.checker.get_automation_interval()
        if interval:
            self.timer = QTimer()
            self.timer.timeout.connect(self.automated_check)
            self.timer.start(interval * 60 * 1000)  # Convert minutes to milliseconds
    
    def automated_check(self):
        """Perform automated grade check"""
        if self.checker_thread is None or not self.checker_thread.isRunning():
            self.checker_thread = AutoCheckThread(self.checker)
            self.checker_thread.finished.connect(self.on_auto_check_completed)
            self.checker_thread.start()

    def on_auto_check_completed(self, changes):
        """Handle completion of automated check"""
        if changes:
            for change in changes:
                self.showMessage(
                    "Cambio en Calificaciones",
                    change,
                    QSystemTrayIcon.Information,
                    10000  # Show for 10 seconds
                )
        
        # Clean up thread
        self.checker_thread.deleteLater()
        self.checker_thread = None
    
    def show_window(self):
        """Show the main window"""
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.raise_()  # Bring window to front
    
    def check_grades(self):
        """Manual grade check from tray"""
        self.show_window()
        self.main_window.check_grades()
    
    def quit_app(self):
        """Quit the application"""
        QApplication.instance().quit()