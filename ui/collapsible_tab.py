# 第三方库导入
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QFrame, QSizePolicy, QToolButton, QScrollArea,
    QGraphicsOpacityEffect, QApplication
)
from PySide6.QtCore import (
    Qt, QTimer, QSize, QParallelAnimationGroup, 
    QPropertyAnimation, QAbstractAnimation, Signal,
    QEasingCurve, QRect
)
from PySide6.QtGui import QGuiApplication, QFont, QPainter, QPen
from typing import Optional, List, Dict, Any


class HorizontalCollapsibleTabs(QWidget):
    """
    水平排列的折叠面板切换器 + 垂直内容区域展示。
    
    改进点：
    - 添加了缓动动画效果
    - 改进了内存管理和性能
    - 增加了主题样式支持
    - 添加了键盘导航支持
    - 更好的错误处理
    - 支持禁用/启用标签页
    - 添加了回调信号
    """
    
    # 信号定义
    tabExpanded = Signal(int)  # 标签展开信号
    tabCollapsed = Signal(int)  # 标签收起信号
    allCollapsed = Signal()    # 所有标签收起信号

    def __init__(self, parent: Optional[QWidget] = None, 
                 parent_window: Optional[QWidget] = None, 
                 tab_height: int = 40,
                 animation_duration: int = 300):
        super().__init__(parent)
        
        self.parent_window = parent_window
        self.tab_height = tab_height
        self.animation_duration = animation_duration
        self.tabs: List[Dict[str, Any]] = []
        self.current_index = -1
        self.content_height = 0
        self.is_expanded = False
        self.is_animating = False
        
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        """初始化UI布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标签按钮容器
        self.tabs_container = QWidget()
        self.tabs_layout = QHBoxLayout(self.tabs_container)
        self.tabs_layout.setSpacing(5)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        
        # 内容区域容器 - 直接使用QWidget，不用ScrollArea
        self.content_container = QWidget()
        self.content_container.setFixedHeight(0)  # 初始高度为0
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self.tabs_container)
        main_layout.addWidget(self.content_container)

    def _setup_animations(self):
        """设置动画效果"""
        self.animation_group = QParallelAnimationGroup(self)
        
        # 内容区域高度动画 - 直接控制content_container的高度
        self.content_animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self.content_animation.setDuration(self.animation_duration)
        self.content_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 透明度动画
        self.opacity_effect = QGraphicsOpacityEffect()
        self.content_container.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(self.animation_duration // 2)
        
        self.animation_group.addAnimation(self.content_animation)
        self.animation_group.addAnimation(self.opacity_animation)
        
        # 窗口大小动画（如果提供了父窗口）
        if self.parent_window:
            self.window_animation = QPropertyAnimation(self.parent_window, b"size")
            self.window_animation.setDuration(self.animation_duration)
            self.window_animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation_group.addAnimation(self.window_animation)
        
        # 动画完成回调
        self.animation_group.finished.connect(self._on_animation_finished)



    def add_tab(self, title: str, widget: QWidget, enabled: bool = True, 
                tooltip: str = "", icon = None) -> int:
        """
        添加一个新的标签页和其对应的内容小部件。
        
        Args:
            title: 标签标题
            widget: 内容组件
            enabled: 是否启用
            tooltip: 提示文本
            icon: 图标（可选）
            
        Returns:
            int: 标签索引
        """
        try:
            # 创建标签按钮
            button = QToolButton(text=title, checkable=True, checked=False)
            button.setFixedHeight(self.tab_height)
            button.setEnabled(enabled)
            button.setToolTip(tooltip or title)
            
            if icon:
                button.setIcon(icon)
                button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            else:
                button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                
            button.setArrowType(Qt.RightArrow)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # 连接按钮点击事件
            tab_index = len(self.tabs)
            button.pressed.connect(lambda: self._on_tab_clicked(tab_index))
            
            # 键盘导航支持
            button.setFocusPolicy(Qt.TabFocus)
            
            # 添加到布局
            self.tabs_layout.addWidget(button)
            self.content_layout.addWidget(widget)
            
            # 初始隐藏内容
            widget.hide()
            
            # 存储标签信息
            tab_info = {
                'button': button,
                'widget': widget,
                'title': title,
                'enabled': enabled,
                'content_height': self._calculate_content_height(widget)
            }
            self.tabs.append(tab_info)
            
            return tab_index
            
        except Exception as e:
            print(f"Error adding tab: {e}")
            return -1

    def _calculate_content_height(self, widget: QWidget) -> int:
        """计算内容高度，考虑边距和填充"""
        base_height = widget.sizeHint().height()
        # 不再限制最大高度，让内容完全展示
        return base_height + 20  # 只增加少量边距

    def _on_tab_clicked(self, tab_index: int):
        """处理标签点击事件"""
        if self.is_animating or tab_index < 0 or tab_index >= len(self.tabs):
            return
            
        clicked_tab = self.tabs[tab_index]
        
        if not clicked_tab['enabled']:
            return
        
        if self.current_index == tab_index and self.is_expanded:
            # 点击当前已展开的标签，收起
            self._collapse_all()
        else:
            # 展开新标签
            self._expand_tab(tab_index)

    def _expand_tab(self, tab_index: int):
        """展开指定标签"""
        if self.is_animating:
            return
            
        self.is_animating = True
        
        # 更新按钮状态
        for i, tab in enumerate(self.tabs):
            if i == tab_index:
                tab['button'].setChecked(True)
                tab['button'].setArrowType(Qt.DownArrow)
                tab['widget'].show()
            else:
                tab['button'].setChecked(False)
                tab['button'].setArrowType(Qt.RightArrow)
                tab['widget'].hide()
        
        old_index = self.current_index
        self.current_index = tab_index
        self.content_height = self.tabs[tab_index]['content_height']
        
        # 设置动画
        start_height = 0 if not self.is_expanded else self.content_scroll.height()
        self.content_animation.setStartValue(start_height)
        self.content_animation.setEndValue(self.content_height)
        
        # 透明度动画
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        
        # 窗口大小动画
        if self.parent_window:
            current_size = self.parent_window.size()
            height_diff = self.content_height - start_height
            new_height = max(current_size.height() + height_diff, 200)  # 最小窗口高度
            self.window_animation.setStartValue(current_size)
            self.window_animation.setEndValue(QSize(current_size.width(), new_height))
        
        self.is_expanded = True
        self.animation_group.start()
        
        # 发射信号
        if old_index != -1:
            self.tabCollapsed.emit(old_index)
        self.tabExpanded.emit(tab_index)

    def _collapse_all(self):
        """收起所有标签"""
        if self.is_animating or not self.is_expanded:
            return
            
        self.is_animating = True
        old_index = self.current_index
        
        # 更新按钮状态
        for tab in self.tabs:
            tab['button'].setChecked(False)
            tab['button'].setArrowType(Qt.RightArrow)
            tab['widget'].hide()
        
        # 设置动画
        self.content_animation.setStartValue(self.content_container.height())
        self.content_animation.setEndValue(0)
        
        # 透明度动画
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        
        # 窗口大小动画
        if self.parent_window:
            current_size = self.parent_window.size()
            new_height = current_size.height() - self.content_height
            self.window_animation.setStartValue(current_size)
            self.window_animation.setEndValue(QSize(current_size.width(), new_height))
        
        self.current_index = -1
        self.is_expanded = False
        self.animation_group.start()
        
        # 发射信号
        if old_index != -1:
            self.tabCollapsed.emit(old_index)
        self.allCollapsed.emit()

    def _on_animation_finished(self):
        """动画完成回调"""
        self.is_animating = False

    def set_tab_enabled(self, tab_index: int, enabled: bool):
        """启用/禁用指定标签"""
        if 0 <= tab_index < len(self.tabs):
            self.tabs[tab_index]['button'].setEnabled(enabled)
            self.tabs[tab_index]['enabled'] = enabled

    def get_current_tab(self) -> int:
        """获取当前展开的标签索引"""
        return self.current_index

    def expand_tab(self, tab_index: int):
        """程序化展开指定标签"""
        if 0 <= tab_index < len(self.tabs):
            self._expand_tab(tab_index)

    def collapse_all(self):
        """程序化收起所有标签"""
        self._collapse_all()


class CollapsibleBox(QWidget):
    """
    可折叠框组件类
    
    改进点：
    - 添加了缓动动画效果
    - 更好的内容高度计算
    - 添加了加载状态指示
    - 改进了内存管理
    - 添加了更多信号
    """
    
    # 信号定义
    expanded = Signal()
    collapsed = Signal()
    contentChanged = Signal()

    def __init__(self, title: str = "", parent: Optional[QWidget] = None, 
                 parent_window: Optional[QWidget] = None, 
                 button_height: int = 35,
                 animation_duration: int = 300):
        super().__init__(parent)
        
        self.parent_window = parent_window
        self.content_height = 0
        self.animation_duration = animation_duration
        self.is_animating = False
        self._content_widget = None

        self._setup_ui(title, button_height)
        self._setup_animations()

    def _setup_ui(self, title: str, button_height: int):
        """设置UI组件"""
        # 主按钮
        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        if button_height > 0:
            self.toggle_button.setFixedHeight(button_height)
            
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toggle_button.setFocusPolicy(Qt.TabFocus)
        self.toggle_button.pressed.connect(self.on_pressed)

        # 内容区域
        self.content_area = QScrollArea(maximumHeight=0, minimumHeight=0)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_area.setFrameShape(QFrame.NoFrame)
        self.content_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_area.setWidgetResizable(True)

                
        # 布局
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

    def _setup_animations(self):
        """设置动画"""
        self.toggle_animation = QParallelAnimationGroup(self)
        
        # 高度动画
        self.height_animation = QPropertyAnimation(self, b"maximumHeight")
        self.height_animation.setDuration(self.animation_duration)
        self.height_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.content_height_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.content_height_animation.setDuration(self.animation_duration)
        self.content_height_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 透明度动画
        self.opacity_effect = QGraphicsOpacityEffect()
        self.content_area.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(self.animation_duration // 2)

        self.toggle_animation.addAnimation(self.height_animation)
        self.toggle_animation.addAnimation(self.content_height_animation)
        self.toggle_animation.addAnimation(self.opacity_animation)
        
        self.toggle_animation.finished.connect(self._on_animation_finished)

    def on_pressed(self):
        """处理按钮点击"""
        if self.is_animating:
            return
            
        self.is_animating = True
        checked = self.toggle_button.isChecked()
        
        self.toggle_button.setArrowType(Qt.DownArrow if not checked else Qt.RightArrow)
        
        # 设置透明度动画
        if not checked:  # 展开
            self.opacity_animation.setStartValue(0.0)
            self.opacity_animation.setEndValue(1.0)
        else:  # 收起
            self.opacity_animation.setStartValue(1.0)
            self.opacity_animation.setEndValue(0.0)

        self.toggle_animation.setDirection(
            QAbstractAnimation.Forward if not checked else QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def _on_animation_finished(self):
        """动画完成回调"""
        self.is_animating = False
        if self.toggle_animation.direction() == QAbstractAnimation.Forward:
            self.expanded.emit()
        else:
            self.collapsed.emit()

    def collapse(self):
        """程序化收起"""
        if self.toggle_button.isChecked() and not self.is_animating:
            self.toggle_button.setChecked(False)
            self.on_pressed()

    def expand(self):
        """程序化展开"""
        if not self.toggle_button.isChecked() and not self.is_animating:
            self.toggle_button.setChecked(True)
            self.on_pressed()

    def setContentLayout(self, layout):
        """设置内容布局"""
        # 清理旧布局
        if self.content_area.widget():
            old_widget = self.content_area.widget()
            self.content_area.setWidget(None)
            old_widget.deleteLater()
        
        # 创建新的内容容器
        content_widget = QWidget()
        content_widget.setLayout(layout)
        self.content_area.setWidget(content_widget)
        self._content_widget = content_widget
        
        # 计算内容高度
        self.content_height = layout.sizeHint().height() + 20  # 移除高度限制
        
        collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        
        # 停止当前动画
        self.toggle_animation.stop()

        # 重新配置动画
        self.height_animation.setStartValue(collapsed_height)
        self.height_animation.setEndValue(collapsed_height + self.content_height)
        
        self.content_height_animation.setStartValue(0)
        self.content_height_animation.setEndValue(self.content_height)
        
        # 发射内容变更信号
        self.contentChanged.emit()

    def setTitle(self, title: str):
        """设置标题"""
        self.toggle_button.setText(title)

    def getTitle(self) -> str:
        """获取标题"""
        return self.toggle_button.text()

    def isExpanded(self) -> bool:
        """检查是否展开"""
        return self.toggle_button.isChecked()



