from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QStackedWidget, QWidget)
from PyQt6.QtCore import Qt
import requests
from src.client import get_info


class GmailDialog(QDialog):    
    def __init__(self):
        """Initialize the Gmail authentication dialog."""
        super().__init__()
        self._setup_window()
        self._create_interface()
        self.email = None
        
    def _setup_window(self):
        """Configure the main dialog window properties."""
        self.setWindowTitle("Gmail Authentication")
        self.setFixedSize(400, 250)
        self.setModal(True)
        
    def _create_interface(self):
        """Create the main interface with stacked pages."""
        main_layout = QVBoxLayout(self)
        
        # Stacked widget for switching between login and registration
        self.stacked_widget = QStackedWidget()
        
        # Create and add pages
        self.login_page = self._create_login_page()
        self.registration_page = self._create_registration_page()
        
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.registration_page)
        
        main_layout.addWidget(self.stacked_widget)
        
    def _create_login_page(self):
        """
        Create the login page interface.
        
        Returns:
            QWidget: The configured login page widget
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Page title
        title_label = QLabel("Login")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Email input section
        self.email_label = QLabel("Please enter your Gmail address:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@gmail.com")
        self.email_input.returnPressed.connect(self.validate_login)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.validate_login)
        self.login_button.setDefault(True)
        
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.show_registration)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        
        # Assemble layout
        layout.addWidget(title_label)
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return page
    
    def _create_registration_page(self):
        """
        Create the registration page interface.
        
        Returns:
            QWidget: The configured registration page widget
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Page title
        title_label = QLabel("Registration")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Email input section
        self.reg_email_label = QLabel("Gmail address:")
        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("example@gmail.com")
        
        # Verification code sending
        self.send_code_button = QPushButton("Send Verification Code")
        self.send_code_button.clicked.connect(self.send_verification_code)
        
        # Verification code input section
        self.code_label = QLabel("6-digit verification code:")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("123456")
        self.code_input.setMaxLength(6)
        self.code_input.returnPressed.connect(self.verify_registration)
        self.code_input.setEnabled(False)  # Initially disabled
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.verify_button = QPushButton("Verify & Register")
        self.verify_button.clicked.connect(self.verify_registration)
        self.verify_button.setEnabled(False)  # Initially disabled
        
        self.back_button = QPushButton("Back to Login")
        self.back_button.clicked.connect(self.show_login)
        
        button_layout.addWidget(self.verify_button)
        button_layout.addWidget(self.back_button)
        
        # Assemble layout
        layout.addWidget(title_label)
        layout.addWidget(self.reg_email_label)
        layout.addWidget(self.reg_email_input)
        layout.addWidget(self.send_code_button)
        layout.addWidget(self.code_label)
        layout.addWidget(self.code_input)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return page
    
    def validate_login(self):
        """
        Validate user login credentials against the server.
        
        Checks Gmail format, sends heartbeat to server, and handles authentication.
        """
        email_address = self.email_input.text().strip()
        
        # Validate email format
        if not self._is_valid_gmail(email_address):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid Gmail address.")
            self.email_input.setFocus()
            return
        
        # Prepare authentication request
        self.email = email_address
        url = "https://authen-traffic-api.onrender.com/heartbeat"
        payload = get_info()
        payload['email'] = self.email
        
        try:
            # Send authentication request
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and not data.get('banned'): 
                    self.accept()  # Login successful
                    return
            
            # Login failed
            QMessageBox.warning(self, "Login Failed", 
                              "Your Gmail address is banned, not registered, or there was an error. "
                              "Please try registering first.")
                              
        except requests.RequestException:
            QMessageBox.critical(self, "Connection Error", 
                               "Could not connect to the server. Please check your internet connection "
                               "or try again later.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def show_registration(self):
        """Switch to the registration page and transfer email if available."""
        # Transfer email from login to registration
        if self.email_input.text().strip():
            self.reg_email_input.setText(self.email_input.text().strip())
        
        self.stacked_widget.setCurrentWidget(self.registration_page)
        self.setWindowTitle("Gmail Registration")
        
    def show_login(self):
        """Switch to the login page and reset registration form."""
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.setWindowTitle("Gmail Authentication")
        self._reset_registration_form()
        
    def send_verification_code(self):
        """
        Send a 6-digit verification code to the user's email.
        
        Validates email format and communicates with the Flask API to send
        the verification email.
        """
        email_address = self.reg_email_input.text().strip()
        
        # Validate email format
        if not self._is_valid_gmail(email_address):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid Gmail address.")
            self.reg_email_input.setFocus()
            return
        
        try:
            # Send verification code request
            url = "https://authen-traffic-api.onrender.com/send_verification_code"
            payload = {"receiver_email": email_address}
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    # Success - show confirmation and enable code input
                    QMessageBox.information(self, "Code Sent", 
                                          f"A verification code has been sent to {email_address}.\n\n"
                                          "Please check your inbox and enter the 6-digit code below.\n"
                                          "The code will expire in 10 minutes.")
                    
                    self._enable_verification_input()
                else:
                    QMessageBox.warning(self, "Error", data.get('error', 'Failed to send verification code'))
            else:
                QMessageBox.warning(self, "Error", "Failed to send verification code. Please try again.")
                
        except requests.RequestException as e:
            QMessageBox.critical(self, "Connection Error", 
                               f"Could not connect to server: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def verify_registration(self):
        """
        Verify the entered 6-digit code and complete registration.
        
        Validates code format, sends verification request to server,
        and handles registration completion.
        """
        email_address = self.reg_email_input.text().strip()
        verification_code = self.code_input.text().strip()
        
        # Validate code format
        if not verification_code or len(verification_code) != 6 or not verification_code.isdigit():
            QMessageBox.warning(self, "Invalid Code", "Please enter a valid 6-digit code.")
            self.code_input.setFocus()
            return
        
        try:
            # Send verification request
            url = "https://authen-traffic-api.onrender.com/verify_code"
            payload = get_info()
            payload['receiver_email'] = email_address
            payload['verification_code'] = verification_code
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    # Registration successful
                    QMessageBox.information(self, "Registration Successful", 
                                          f"Successfully registered {email_address}!\n\n"
                                          "Your email has been verified. Please login with your Gmail address.")
                    
                    # Switch back to login with email pre-filled
                    self.email_input.setText(email_address)
                    self.show_login()
                else:
                    # Verification failed
                    QMessageBox.warning(self, "Verification Failed", 
                                      data.get('error', 'Invalid verification code'))
                    self.code_input.clear()
                    self.code_input.setFocus()
            else:
                # Handle server error
                try:
                    data = response.json()
                    error_msg = data.get('error', 'Verification failed')
                except:
                    error_msg = 'Verification failed'
                    
                QMessageBox.warning(self, "Verification Failed", error_msg)
                self.code_input.clear()
                self.code_input.setFocus()
                
        except requests.RequestException as e:
            QMessageBox.critical(self, "Connection Error", 
                               f"Could not connect to server: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def _is_valid_gmail(self, email):
        if not email or not email.endswith("@gmail.com"):
            return False
        username = email[:-10]  # Remove "@gmail.com"
        return bool(username and len(username) > 0)
    
    def _enable_verification_input(self):
        self.code_input.setEnabled(True)
        self.verify_button.setEnabled(True)
        self.send_code_button.setEnabled(False)  # Prevent multiple sends
        self.code_input.setFocus()
    
    def _reset_registration_form(self):
        self.reg_email_input.clear()
        self.code_input.clear()
        self.code_input.setEnabled(False)
        self.verify_button.setEnabled(False)
        self.send_code_button.setEnabled(True)