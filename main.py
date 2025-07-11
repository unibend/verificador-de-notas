import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PySide6.QtGui import QIcon
import os
from app.main_window import MainWindow
from app.grade_checker import MoodleGradeChecker
from app.tray_icon import SystemTrayIcon

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Don't quit when window is closed
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create the grade checker instance
    checker = MoodleGradeChecker()
    
    # Create main window
    window = MainWindow(checker)
    
    # Create system tray icon
    tray = SystemTrayIcon(checker, window)
    
    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Verificador de Notas",
                           "No se detectó la bandeja del sistema.\n"
                           "Esta aplicación requiere la bandeja del sistema para funcionar.")
        return 1
    
    # Show tray icon
    tray.show()
    
    # Show main window
    window.show()
    
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())