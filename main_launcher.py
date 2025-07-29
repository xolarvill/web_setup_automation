# main_launcher.py - 这个文件替换app.py作为spec文件的入口点
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient
from qt_material import apply_stylesheet

# PyInstaller兼容性修复
if hasattr(sys, '_MEIPASS'):
    import multiprocessing
    multiprocessing.freeze_support()
    os.environ['NUMPY_MADVISE_HUGEPAGE'] = '0'

class SplashScreen(QWidget):
    """
    启动画面 - 立即显示，在主线程中延迟加载主应用。
    """
    
    def __init__(self):
        """
        初始化启动画面UI并设置一个定时器来加载主应用。
        """
        super().__init__()
        self.main_window = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 300)
        self.center_on_screen()
        self.setup_ui()
        
        # 使用QTimer延迟加载主应用，确保启动画面先显示
        QTimer.singleShot(100, self.load_main_app)
        
    def center_on_screen(self):
        """
        将窗口居中显示。
        """
        screen_geometry = QApplication.primaryScreen().geometry()
        self.move(
            (screen_geometry.width() - self.width()) // 2,
            (screen_geometry.height() - self.height()) // 2
        )
    
    def setup_ui(self):
        """
        设置UI界面。
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        self.logo_label = QLabel("🚀", self)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.logo_label)
        
        self.title_label = QLabel("Web Setup Automation", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        font = self.title_label.font()
        font.setPointSize(18)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(self.title_label)
        
        self.version_label = QLabel("Version 0.2.2", self)
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self.version_label)
        
        self.status_label = QLabel("正在启动应用...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #34495e; font-size: 14px; margin-top: 20px;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress bar
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2980b9);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.copyright_label = QLabel("© 2024 Victor Li. All rights reserved.", self)
        self.copyright_label.setAlignment(Qt.AlignCenter)
        self.copyright_label.setStyleSheet("color: #95a5a6; font-size: 10px; margin-top: 20px;")
        layout.addWidget(self.copyright_label)
        
        self.setLayout(layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 230);
                border-radius: 15px;
            }
        """)

    def paintEvent(self, event):
        """
        自定义绘制事件，添加阴影效果。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制阴影
        shadow_color = QColor(0, 0, 0, 30)
        painter.setBrush(shadow_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(5, 5, -5, -5), 10, 10)
        
        # 绘制主背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 240))
        gradient.setColorAt(1, QColor(245, 245, 245, 240))
        painter.setBrush(gradient)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -5, -5), 15, 15)
        
        super().paintEvent(event)

    def load_main_app(self):
        """
        在主线程中加载并显示主应用窗口。
        """
        self.status_label.setText("正在加载主界面...")
        QApplication.processEvents() # 确保状态更新显示

        try:
            from app import create_main_window
            self.main_window = create_main_window()
            self.main_window.show()
            self.close()
        except Exception as e:
            self.status_label.setText(f"启动失败: {e}")
            print(f"Error loading main window: {e}")
            import traceback
            traceback.print_exc()
            # 在启动失败时保持启动画面，以便用户看到错误信息
            self.progress_bar.setRange(0, 1) # 停止动画
            self.progress_bar.setValue(1)
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")


def main():
    """
    主入口函数。
    """
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("Web Setup Automation")
    app.setApplicationVersion("0.2.2")
    app.setOrganizationName("Victor Li")
    
    # 应用Qt-Material样式
    apply_stylesheet(app, theme='light_orange.xml')
    
    # 创建并显示启动画面
    splash = SplashScreen()
    splash.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
