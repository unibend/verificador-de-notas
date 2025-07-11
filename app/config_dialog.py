from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, 
                             QSpinBox, QTimeEdit, QMessageBox)
from PySide6.QtCore import Qt

class ConfigDialog(QDialog):
    def __init__(self, checker, parent=None):
        super().__init__(parent)
        self.checker = checker
        self.setWindowTitle("Configuración")
        
        layout = QVBoxLayout(self)
        
        # Login section
        login_group = QVBoxLayout()
        
        if self.checker.has_stored_credentials():
            logout_btn = QPushButton("Cerrar Sesión")
            logout_btn.clicked.connect(self.logout)
            login_group.addWidget(logout_btn)
        else:
            # Username field
            username_layout = QHBoxLayout()
            username_layout.addWidget(QLabel("Usuario:"))
            self.username_input = QLineEdit()
            username_layout.addWidget(self.username_input)
            login_group.addLayout(username_layout)
            
            # Password field
            password_layout = QHBoxLayout()
            password_layout.addWidget(QLabel("Contraseña:"))
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            password_layout.addWidget(self.password_input)
            login_group.addLayout(password_layout)
            
            # Login button
            login_btn = QPushButton("Iniciar Sesión")
            login_btn.clicked.connect(self.login)
            login_group.addWidget(login_btn)
        
        layout.addLayout(login_group)
        
        # Automation section
        automation_group = QVBoxLayout()
        
        if self.checker.is_automation_enabled():
            stop_auto_btn = QPushButton("Detener Automatización")
            stop_auto_btn.clicked.connect(self.stop_automation)
            automation_group.addWidget(stop_auto_btn)
        else:
            # Interval selection
            interval_layout = QHBoxLayout()
            interval_layout.addWidget(QLabel("Intervalo (minutos):"))
            self.interval_input = QSpinBox()
            self.interval_input.setRange(1, 1440)  # 1 minute to 24 hours
            self.interval_input.setValue(30)  # Default 30 minutes
            interval_layout.addWidget(self.interval_input)
            automation_group.addLayout(interval_layout)
            
            # Start automation button
            auto_btn = QPushButton("Automatizar")
            auto_btn.clicked.connect(self.start_automation)
            automation_group.addWidget(auto_btn)
        
        layout.addLayout(automation_group)
        
        # Uninstall button
        uninstall_btn = QPushButton("Desinstalar")
        uninstall_btn.clicked.connect(self.uninstall)
        layout.addWidget(uninstall_btn)
    
    def login(self):
        """Handle login attempt"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        if self.checker.store_credentials(username, password):
            QMessageBox.information(self, "Éxito", "Sesión iniciada correctamente")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Error al iniciar sesión")
    
    def logout(self):
        """Handle logout"""
        self.checker.clear_credentials()
        QMessageBox.information(self, "Éxito", "Sesión cerrada")
        self.accept()
    
    def start_automation(self):
        """Enable automated checking"""
        interval = self.interval_input.value()
        self.checker.enable_automation(interval)
        QMessageBox.information(self, "Éxito", 
                              "Automatización activada. La aplicación "
                              "se ejecutará en segundo plano.")
        self.accept()
    
    def stop_automation(self):
        """Disable automated checking"""
        self.checker.disable_automation()
        QMessageBox.information(self, "Éxito", "Automatización desactivada")
        self.accept()
    
    def uninstall(self):
        """Handle uninstall request"""
        reply = QMessageBox.question(
            self, "Confirmar Desinstalación",
            "¿Está seguro que desea eliminar toda la configuración? "
            "Esto eliminará sus credenciales y detendrá la automatización.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.checker.uninstall()
            QMessageBox.information(self, "Éxito", 
                                  "Configuración eliminada exitosamente")
            self.accept()