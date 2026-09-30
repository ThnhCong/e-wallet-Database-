import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from Login_frame import LoginFrame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("E-wallet Application")
        self.resize(900, 650)
        self.setMinimumSize(700, 500)  # Đảm bảo không bị vỡ giao diện khi thu nhỏ quá mức

        # Màu nền chung cho cả Window
        self.setStyleSheet("QMainWindow { background-color: #F1F5F9; }")

        # Stack quản lý các trang
        self.stack = QStackedWidget()

        # Tạo các trang
        self.home_page = self.create_home_page()
        self.settings_page = self.create_settings_page()
        self.login_frame = LoginFrame(
            on_login_success=lambda: self.stack.setCurrentWidget(self.home_page)
        )

        # Add vào Stack
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.login_frame)

        # Mặc định mở trang Login
        self.stack.setCurrentWidget(self.login_frame)

        self.setCentralWidget(self.stack)

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("HOME PAGE")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #0F172A;")

        desc = QLabel("Welcome back to your E-wallet Dashboard!")
        desc.setStyleSheet("color: #475569; font-size: 15px;")

        # Thanh điều hướng phía trên
        nav_layout = QHBoxLayout()
        settings_button = QPushButton("Go to Settings")
        settings_button.setFixedHeight(38)
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #0EA5E9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0284C7; }
        """)
        settings_button.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.settings_page)
        )

        logout_button = QPushButton("Logout")
        logout_button.setFixedHeight(38)
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        logout_button.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.login_frame)
        )

        nav_layout.addWidget(settings_button)
        nav_layout.addStretch()
        nav_layout.addWidget(logout_button)

        layout.addLayout(nav_layout)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()

        return page

    def create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("SETTINGS")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #0F172A;")

        home_button = QPushButton("Back to Home")
        home_button.setFixedWidth(140)
        home_button.setFixedHeight(38)
        home_button.setStyleSheet("""
            QPushButton {
                background-color: #64748B;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        home_button.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.home_page)
        )

        layout.addWidget(title)
        layout.addWidget(home_button)
        layout.addStretch()

        return page


def main():
    app = QApplication(sys.argv)

    # Đặt phông chữ mặc định cho toàn bộ ứng dụng
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()