from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont


class LoginFrame(QWidget):
    def __init__(self, user="Tina514160", pw="514160", on_login_success=None):
        super().__init__()
        self.user = user
        self.pw = pw
        self.on_login_success = on_login_success

        self.init_ui()

    def init_ui(self):
        # 1. Layout chính của toàn bộ trang (Căn giữa bằng Stretch)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addStretch(1)  # Đẩy card xuống giữa theo chiều dọc

        # Layout ngang để căn giữa Card theo chiều ngang
        center_horizontal_layout = QHBoxLayout()
        center_horizontal_layout.addStretch(1)

        # 2. Tạo một QFrame đóng vai trò "Card Login" có nền trắng & bo góc
        card = QFrame()
        card.setFixedWidth(380)  # Cố định chiều rộng vừa vặn cho Card
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)

        # Tạo hiệu ứng đổ bóng (Drop Shadow) cho Card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        # 3. Layout bên trong Card Login
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 40, 35, 40)
        card_layout.setSpacing(18)

        # Title
        title = QLabel("Welcome Back")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1E293B;")

        subtitle = QLabel("Sign in to your E-wallet account")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #64748B; font-size: 13px; margin-bottom: 10px;")

        # Stylesheet chung cho ô nhập liệu QLineEdit
        input_style = """
            QLineEdit {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 14px;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 2px solid #2563EB;
                background-color: #FFFFFF;
            }
        """

        # Username Input
        self.user_name = QLineEdit()
        self.user_name.setPlaceholderText("Username")
        self.user_name.setFixedHeight(46)
        self.user_name.setStyleSheet(input_style)

        # Password Input
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setFixedHeight(46)
        self.password.setStyleSheet(input_style)

        # Login Button
        login_button = QPushButton("Sign In")
        login_button.setFixedHeight(46)
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
        """)

        # Label hiển thị thông báo lỗi/thành công
        self.msg_label = QLabel("")
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_label.setStyleSheet("font-size: 13px; font-weight: 500;")

        # Thêm các thành phần vào Card Layout
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.user_name)
        card_layout.addWidget(self.password)
        card_layout.addWidget(login_button)
        card_layout.addWidget(self.msg_label)

        # Đưa Card vào Layout căn giữa
        center_horizontal_layout.addWidget(card)
        center_horizontal_layout.addStretch(1)

        main_layout.addLayout(center_horizontal_layout)
        main_layout.addStretch(1)  # Đẩy card lên giữa theo chiều dọc

        # Kết nối Event
        login_button.clicked.connect(self.check_login)
        self.user_name.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self.check_login)

    def check_login(self):
        user_name = self.user_name.text().strip()
        password = self.password.text().strip()

        if user_name == self.user and password == self.pw:
            self.msg_label.setStyleSheet("color: #16A34A;")
            self.msg_label.setText("Login successful!")
            if self.on_login_success:
                self.on_login_success()
        else:
            self.msg_label.setStyleSheet("color: #DC2626;")
            self.msg_label.setText("Invalid username or password.")