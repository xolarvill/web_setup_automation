# main_launcher.py - 现代化启动画面设计
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QBrush
from qt_material import apply_stylesheet
import math



# PyInstaller兼容性修复
if hasattr(sys, '_MEIPASS'):
    import multiprocessing
    multiprocessing.freeze_support()
    os.environ['NUMPY_MADVISE_HUGEPAGE'] = '0'

class ModernSplashScreen(QWidget):
    """
    现代化启动画面 - 具有玻璃质感和呼吸动画效果
    """
    
    def __init__(self):
        super().__init__()
        self.main_window = None
        self.animation_value = 0.0
        self.setup_window()
        self.setup_ui()
        self.setup_animations()
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(243, 115, 53, 153))  # 0.6 透明度对应 153
        shadow.setOffset(0, 0)
        self.logo_label.setGraphicsEffect(shadow)
        
        # 延迟加载主应用
        QTimer.singleShot(100, self.load_main_app)
        
    def setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(480, 360)
        self.center_on_screen()
        
    def center_on_screen(self):
        """将窗口居中显示"""
        screen_geometry = QApplication.primaryScreen().geometry()
        self.move(
            (screen_geometry.width() - self.width()) // 2,
            (screen_geometry.height() - self.height()) // 2
        )
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Logo区域
        self.logo_container = QWidget()
        self.logo_container.setFixedSize(100, 100)
        logo_layout = QVBoxLayout(self.logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logo_label = QLabel("🚀")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("""
            QLabel {
                font-size: 56px;
                color: #F37335;
                background: transparent;
            }
        """)
        logo_layout.addWidget(self.logo_label)
        
        # 添加Logo容器到主布局并居中
        logo_container_layout = QVBoxLayout()
        logo_container_layout.addWidget(self.logo_container, 0, Qt.AlignCenter)
        layout.addLayout(logo_container_layout)
        
        # 标题
        self.title_label = QLabel("Web Setup Automation")
        self.title_label.setAlignment(Qt.AlignCenter)
        font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                background: transparent;
                letter-spacing: 1px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # 版本信息
        self.version_label = QLabel("Version 0.4.1")
        self.version_label.setAlignment(Qt.AlignCenter)
        version_font = QFont("Segoe UI", 11)
        self.version_label.setFont(version_font)
        self.version_label.setStyleSheet("""
            QLabel {
                color: #7F8C8D;
                background: transparent;
                margin-top: 5px;
            }
        """)
        layout.addWidget(self.version_label)
        
        # 状态标签
        self.status_label = QLabel("正在启动应用...")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont("Segoe UI", 12)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #34495E;
                background: transparent;
                margin-top: 30px;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 现代化进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #F37335, 
                    stop:0.5 #FF8C42, 
                    stop:1 #F37335);
                border-radius: 3px;
                animation: pulse 2s ease-in-out infinite;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 版权信息
        self.copyright_label = QLabel("© 2024 Victor Li. All rights reserved.")
        self.copyright_label.setAlignment(Qt.AlignCenter)
        copyright_font = QFont("Segoe UI", 9)
        self.copyright_label.setFont(copyright_font)
        self.copyright_label.setStyleSheet("""
            QLabel {
                color: rgba(149, 165, 166, 0.8);
                background: transparent;
                margin-top: 25px;
            }
        """)
        layout.addWidget(self.copyright_label)
        
        # 添加阴影效果
        self.add_shadow_effects()
        
    def add_shadow_effects(self):
        """为UI元素添加阴影效果"""
        # Logo阴影
        logo_shadow = QGraphicsDropShadowEffect()
        logo_shadow.setBlurRadius(25)
        logo_shadow.setColor(QColor(243, 115, 53, 80))
        logo_shadow.setOffset(0, 5)
        self.logo_label.setGraphicsEffect(logo_shadow)
        
        # 标题阴影
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(15)
        title_shadow.setColor(QColor(0, 0, 0, 30))
        title_shadow.setOffset(0, 2)
        self.title_label.setGraphicsEffect(title_shadow)
        
    def setup_animations(self):
        """设置呼吸动画"""
        # Logo呼吸动画
        self.logo_animation = QPropertyAnimation(self.logo_label, b"geometry")
        self.logo_animation.setDuration(2000)
        self.logo_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        # 创建动画定时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_breathing_animation)
        self.animation_timer.start(50)  # 20 FPS
        
    def update_breathing_animation(self):
        """更新呼吸动画"""
        import time
        current_time = time.time()
        self.animation_value = (math.sin(current_time * 1.5) + 1) / 2  # 0 to 1
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        """自定义绘制事件 - 玻璃质感背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建圆角矩形路径
        rect = self.rect()
        corner_radius = 20
        
        # 背景阴影
        shadow_rect = rect.adjusted(0, 5, -5, 0)
        shadow_gradient = QRadialGradient(
            shadow_rect.center().x(), 
            shadow_rect.center().y(), 
            max(shadow_rect.width(), shadow_rect.height()) / 2
        )
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, 40))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, corner_radius + 5, corner_radius + 5)
        
        # 主背景 - 磨砂玻璃效果
        main_rect = rect.adjusted(0, 0, -5, -5)
        
        # 基础渐变背景
        base_gradient = QLinearGradient(0, 0, 0, main_rect.height())
        base_gradient.setColorAt(0, QColor(255, 255, 255, 200))
        base_gradient.setColorAt(0.5, QColor(255, 255, 255, 180))
        base_gradient.setColorAt(1, QColor(250, 250, 250, 190))
        
        painter.setBrush(QBrush(base_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(main_rect, corner_radius, corner_radius)
        
        # 橙色装饰渐变
        accent_gradient = QLinearGradient(0, 0, main_rect.width(), main_rect.height())
        accent_alpha = int(30 + 20 * self.animation_value)  # 呼吸效果
        accent_gradient.setColorAt(0, QColor(243, 115, 53, accent_alpha))
        accent_gradient.setColorAt(0.3, QColor(255, 140, 66, accent_alpha // 2))
        accent_gradient.setColorAt(0.7, QColor(243, 115, 53, accent_alpha // 3))
        accent_gradient.setColorAt(1, QColor(255, 140, 66, accent_alpha))
        
        painter.setBrush(QBrush(accent_gradient))
        painter.drawRoundedRect(main_rect, corner_radius, corner_radius)
        
        # 边框 - 玻璃质感
        border_color = QColor(243, 115, 53, int(100 + 50 * self.animation_value))
        painter.setPen(QPen(border_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(main_rect, corner_radius, corner_radius)
        
        # 高光效果
        highlight_rect = main_rect.adjusted(1, 1, -1, -main_rect.height()//2)
        highlight_gradient = QLinearGradient(0, highlight_rect.top(), 0, highlight_rect.bottom())
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 60))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(highlight_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(highlight_rect, corner_radius - 1, corner_radius - 1)
        
        # 装饰性光斑
        self.draw_decorative_elements(painter, main_rect)
        
        super().paintEvent(event)
        
    def draw_decorative_elements(self, painter, rect):
        """绘制装饰性元素"""
        # 浮动的装饰圆点
        import time
        current_time = time.time()
        
        # 大圆点
        circle1_x = rect.width() * 0.8 + 10 * math.sin(current_time * 0.8)
        circle1_y = rect.height() * 0.2 + 5 * math.cos(current_time * 0.8)
        circle1_alpha = int(40 + 20 * math.sin(current_time * 1.2))
        
        painter.setBrush(QBrush(QColor(243, 115, 53, circle1_alpha)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(circle1_x - 8), int(circle1_y - 8), 16, 16)
        
        # 小圆点
        circle2_x = rect.width() * 0.15 + 8 * math.cos(current_time * 1.2)
        circle2_y = rect.height() * 0.8 + 6 * math.sin(current_time * 1.0)
        circle2_alpha = int(30 + 15 * math.cos(current_time * 0.9))
        
        painter.setBrush(QBrush(QColor(255, 140, 66, circle2_alpha)))
        painter.drawEllipse(int(circle2_x - 6), int(circle2_y - 6), 12, 12)
        
        # 微小装饰点
        for i in range(3):
            angle = current_time * 0.5 + i * 2.1
            x = rect.width() * (0.3 + 0.4 * i / 3) + 15 * math.sin(angle)
            y = rect.height() * 0.6 + 10 * math.cos(angle)
            alpha = int(20 + 10 * math.sin(angle * 2))
            
            painter.setBrush(QBrush(QColor(243, 115, 53, alpha)))
            painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)

    def load_main_app(self):
        """加载主应用"""
        self.status_label.setText("正在加载主界面...")
        QApplication.processEvents()

        try:
            from app import create_main_window
            self.main_window = create_main_window()
            self.main_window.show()
            
            # 淡出动画
            self.fade_out_animation()
            
        except Exception as e:
            self.status_label.setText(f"启动失败: {e}")
            print(f"Error loading main window: {e}")
            import traceback
            traceback.print_exc()
            
            # 停止动画并显示错误状态
            self.animation_timer.stop()
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #e74c3c, stop:1 #c0392b); 
                }
            """)
            
    def fade_out_animation(self):
        """淡出动画"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()


def main():
    """主入口函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("Web Setup Automation")
    app.setApplicationVersion("0.4.1")
    app.setOrganizationName("Victor Li")
    
    # 应用Qt-Material样式
    apply_stylesheet(app, theme='light_orange.xml')
    
    # 创建并显示现代化启动画面
    splash = ModernSplashScreen()
    splash.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()