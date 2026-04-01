import sys
import json
import random
import math
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QPushButton, QLineEdit, QMenu, QAction, QSystemTrayIcon)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal, QThread, QTime
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QCursor, QMovie

from ollama_client import OllamaClient
from memory import MemorySystem


class ChatThread(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, ollama_client, message, memory_system):
        super().__init__()
        self.ollama_client = ollama_client
        self.message = message
        self.memory_system = memory_system

    def run(self):
        try:
            context = self.memory_system.get_context()
            response = self.ollama_client.chat_with_tools(self.message, context)
            self.memory_system.add_conversation(self.message, response)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class PetWindow(QWidget):
    def __init__(self, pet_id, pet_name, pet_color, screen_rect, gif_path="duckygif/duckyo.gif"):
        super().__init__()
        self.pet_id = pet_id
        self.pet_name = pet_name
        self.pet_color = pet_color
        self.screen_rect = screen_rect
        
        self.position = QPoint(
            random.randint(100, screen_rect.width() - 100),
            random.randint(100, screen_rect.height() - 200)
        )
        self.target_position = self.position
        self.direction = 1
        self.is_hovering = False
        
        self.gif_path = gif_path
        self.gif_hover_path = "duckygif/duckyorisehand.gif"
        self.gif_thinking_path = "duckygif/duckyogettheinfo.gif"
        self.gif_sleep_path = "duckygif/duckyosleep.gif"
        self.gif_caboli_path = "duckygif/duckyocaboli.gif"
        self.movie = QMovie(self.gif_path)
        self.movie.setScaledSize(QPixmap(self.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.movie_default = self.movie
        
        pixmap = QPixmap(self.gif_path)
        self.pet_size = min(150, max(120, max(pixmap.width(), pixmap.height())))
        
        self.is_sleeping = False
        self.is_caboli = False
        self.sleep_timeout = 120000
        
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        
        self.canvas_width = max(280, self.pet_size + 30)
        self.canvas_height = self.pet_size + 320
        
        self.setFixedSize(self.canvas_width, self.canvas_height)
        self.move(self.position)
        self.setMouseTracking(True)
        
        self.gif_label = QLabel(self)
        self.gif_label.setMovie(self.movie)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setFixedSize(self.pet_size, self.pet_size)
        self.gif_label.move((self.canvas_width - self.pet_size) // 2, 130)
        self.gif_label.setStyleSheet("background: transparent; border: none;")
        self.gif_label.setMouseTracking(True)
        self.gif_label.installEventFilter(self)
        
        self.input_frame = QWidget(self)
        self.input_frame.setGeometry(0, self.pet_size + 140, self.canvas_width, 150)
        self.input_frame.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 245);
                border-radius: 12px;
                border: 2px solid #4CAF50;
            }
        """)
        self.input_frame.setMouseTracking(True)
        self.input_frame.hide()
        
        self.input_box = QLineEdit(self.input_frame)
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setGeometry(10, 10, self.canvas_width - 20, 70)
        self.input_box.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }
        """)
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setMouseTracking(True)
        
        self.send_btn = QPushButton("发送", self.input_frame)
        self.send_btn.setGeometry(self.canvas_width - 80, 85, 65, 45)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        self.clear_btn = QPushButton("清空上下文", self.input_frame)
        self.clear_btn.setGeometry(10, 90, 100, 35)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_context)
        
        self.show()
        self.movie.start()

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.Enter:
            self.on_hover_start()
        elif event.type() == QEvent.Leave:
            self.check_leave(event)
        return super().eventFilter(obj, event)

    def enterEvent(self, event):
        self.on_hover_start()
        super().enterEvent(event)

    def check_leave(self, event):
        if self.input_frame.isVisible():
            input_global = self.input_frame.mapToGlobal(QPoint(0, 0))
            input_rect = self.input_frame.rect().translated(input_global)
            if input_rect.contains(QCursor.pos()):
                return
            
            gif_global = self.gif_label.mapToGlobal(QPoint(0, 0))
            gif_rect = self.gif_label.rect().translated(gif_global)
            if gif_rect.contains(QCursor.pos()):
                return
            
        self.on_hover_end()
        super().leaveEvent(event)

    def leaveEvent(self, event):
        self.check_leave(event)

    def on_hover_start(self):
        if self.is_sleeping:
            self.wake_up()
        
        if self.is_caboli:
            self.is_caboli = False
        
        self.is_hovering = True
        
        self.movie.stop()
        if Path(self.gif_hover_path).exists():
            self.movie = QMovie(self.gif_hover_path)
            self.movie.setScaledSize(QPixmap(self.gif_hover_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        
        self.input_frame.show()

    def on_hover_end(self):
        self.is_hovering = False
        self.last_activity_time = QTime.currentTime()
        
        self.movie.stop()
        self.movie = QMovie(self.gif_path)
        self.movie.setScaledSize(QPixmap(self.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        
        self.input_frame.hide()

    def clear_context(self):
        if hasattr(self, '_memory_system'):
            self._memory_system.clear_memory()
        self.input_box.setPlaceholderText("上下文已清空!")
        QTimer.singleShot(1500, lambda: self.input_box.setPlaceholderText("输入消息..."))

    def send_message(self):
        message = self.input_box.text().strip()
        if not message:
            return
        
        self.movie.stop()
        if Path(self.gif_thinking_path).exists():
            self.movie = QMovie(self.gif_thinking_path)
            self.movie.setScaledSize(QPixmap(self.gif_thinking_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        
        if hasattr(self, '_chat_callback'):
            self._chat_callback(message)
        self.input_box.setPlaceholderText("等待回复...")
        self.input_box.clear()

    def setup_animation(self):
        self.walk_timer = QTimer(self)
        self.walk_timer.timeout.connect(self.walk)
        self.walk_timer.start(50)
        
        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.check_sleep)
        self.sleep_timer.start(1000)
        self.last_activity_time = QTime.currentTime()
        
        self.caboli_timer = QTimer(self)
        self.caboli_timer.timeout.connect(self.check_caboli)
        self.caboli_timer.start(5000)

    def check_caboli(self):
        if self.is_hovering or self.is_sleeping or self.is_caboli:
            return
        if hasattr(self, '_active_thread') and self._active_thread is not None:
            return
        if random.random() < 0.25:
            self.play_caboli()

    def play_caboli(self):
        if not Path(self.gif_caboli_path).exists():
            return
        self.is_caboli = True
        self.movie.stop()
        self.movie = QMovie(self.gif_caboli_path)
        self.movie.setScaledSize(QPixmap(self.gif_caboli_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        QTimer.singleShot(10000, self.stop_caboli)

    def stop_caboli(self):
        self.is_caboli = False
        self.movie.stop()
        self.movie = QMovie(self.gif_path)
        self.movie.setScaledSize(QPixmap(self.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def check_sleep(self):
        if self.is_sleeping:
            return
        if self.is_hovering:
            self.last_activity_time = QTime.currentTime()
            return
        if hasattr(self, '_active_thread') and self._active_thread is not None:
            return
            
        elapsed = self.last_activity_time.msecsTo(QTime.currentTime())
        if elapsed >= self.sleep_timeout:
            self.go_to_sleep()

    def go_to_sleep(self):
        self.is_sleeping = True
        self.movie.stop()
        if Path(self.gif_sleep_path).exists():
            self.movie = QMovie(self.gif_sleep_path)
            self.movie.setScaledSize(QPixmap(self.gif_sleep_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def wake_up(self):
        self.is_sleeping = False
        self.last_activity_time = QTime.currentTime()
        self.movie.stop()
        self.movie = QMovie(self.gif_path)
        self.movie.setScaledSize(QPixmap(self.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def walk(self):
        if self.is_hovering or self.is_sleeping or self.is_caboli:
            return
            
        if random.random() < 0.02:
            self.target_position = QPoint(
                random.randint(50, self.screen_rect.width() - 50),
                random.randint(50, self.screen_rect.height() - 150)
            )

        dx = self.target_position.x() - self.position.x()
        dy = self.target_position.y() - self.position.y()

        if abs(dx) > 5:
            self.position.setX(self.position.x() + (1 if dx > 0 else -1) * 2)
            self.direction = 1 if dx > 0 else -1

        if abs(dy) > 5:
            self.position.setY(self.position.y() + (1 if dy > 0 else -1) * 2)

        self.move(self.position)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(60, 60, 60))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        name_rect = QRect(0, self.pet_size + 5, self.pet_size + 20, 15)
        painter.drawText(name_rect, Qt.AlignCenter, self.pet_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        pet_menu = QMenu("切换宠物", self)
        colors = [("粉色猫咪", "#FFB6C1"), ("蓝色小狗", "#87CEEB"), ("绿色青蛙", "#90EE90"), ("橙色狐狸", "#FFD700")]
        for name, color in colors:
            action = QAction(name, self)
            action.triggered.connect(lambda c, n=name: self.change_pet(n, c))
            pet_menu.addAction(action)
        menu.addMenu(pet_menu)

        menu.exec_(pos)

    def change_pet(self, name, color):
        self.pet_name = name
        self.pet_color = color
        self.update()


class DesktopPetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.pets = []
        self.ollama_client = OllamaClient(
            base_url=self.config.get("ollama", {}).get("base_url", "http://localhost:11434"),
            model=self.config.get("ollama", {}).get("model", "llama3")
        )
        self.memory_system = MemorySystem(
            memory_dir=self.config.get("memory", {}).get("memory_dir", "memory")
        )
        
        self.setup_tray()
        pet_config = self.config.get("pet", {})
        self.create_pet(
            pet_config.get("default_name", "小萌"),
            pet_config.get("default_color", "#FFB6C1")
        )

    def load_config(self):
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建一个简单的图标
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#FFB6C1"))
        painter = QPainter(pixmap)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FF69B4"))
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        
        add_pet_action = QAction("添加宠物", self)
        add_pet_action.triggered.connect(self.add_pet_dialog)
        tray_menu.addAction(add_pet_action)

        tray_menu.addSeparator()

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def create_pet(self, name, color, gif_path="duckygif/duckyo.gif"):
        screen = QApplication.primaryScreen().geometry()
        pet_id = len(self.pets)
        pet = PetWindow(pet_id, name, color, screen, gif_path)
        pet._chat_callback = lambda msg: self.handle_message(pet, msg)
        pet._active_thread = None
        pet._memory_system = self.memory_system
        self.pets.append(pet)

    def handle_message(self, pet, message):
        def show_response(response):
            self.show_response_bubble(pet, response)
            pet._active_thread = None
            pet.input_box.setPlaceholderText("输入消息...")
            
            pet.movie.stop()
            if Path(pet.gif_hover_path).exists():
                pet.movie = QMovie(pet.gif_hover_path)
                pet.movie.setScaledSize(QPixmap(pet.gif_hover_path).size().scaled(150, 150, Qt.KeepAspectRatio))
            pet.gif_label.setMovie(pet.movie)
            pet.movie.start()
            
            if not pet.is_hovering:
                pet.input_frame.hide()
        
        def on_error(e):
            self.show_response_bubble(pet, f"错误: {e}")
            pet._active_thread = None
            pet.input_box.setPlaceholderText("输入消息...")
        
        chat_thread = ChatThread(self.ollama_client, message, self.memory_system)
        chat_thread.response_ready.connect(show_response)
        chat_thread.error_occurred.connect(on_error)
        pet._active_thread = chat_thread
        chat_thread.start()

    def show_response_bubble(self, pet, response):
        pet.response_label = QLabel(pet)
        pet.response_label.setWordWrap(True)
        pet.response_label.setText(response)
        pet.response_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 250);
                border-radius: 15px;
                border: 2px solid #4CAF50;
                padding: 15px;
                font-size: 16px;
                color: #333;
            }
        """)
        pet.response_label.setFixedSize(max(280, pet.pet_size + 20), 100)
        pet.response_label.move(5, 15)
        pet.response_label.show()
        QTimer.singleShot(8000, pet.response_label.close)

    def add_pet_dialog(self):
        colors = [("粉色猫咪", "#FFB6C1"), ("蓝色小狗", "#87CEEB"), ("绿色青蛙", "#90EE90"), ("橙色狐狸", "#FFD700")]
        color_name, color = random.choice(colors)
        name = f"宠物{len(self.pets) + 1}"
        self.create_pet(name, color)

    def show_settings(self):
        QMessageBox.information(self, "设置", "设置功能开发中...")

    def quit_app(self):
        for pet in self.pets:
            pet.close()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = DesktopPetApp()
    
    sys.exit(app.exec_())
