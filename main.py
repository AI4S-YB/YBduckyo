import sys
import json
import random
import math
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QPushButton, QLineEdit, QMenu, QAction, QSystemTrayIcon,
                             QDialog, QTextEdit, QVBoxLayout, QScrollArea, QPushButton as QB)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal, QThread, QTime
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QCursor, QMovie

from memory import MemorySystem

def get_client(config):
    ollama_config = config.get("ollama", {})
    base_url = ollama_config.get("base_url", "")
    
    if "xiaomimimo.com" in base_url or "api.mimo" in base_url:
        from mimo_client import MiMoClient
        return MiMoClient(
            base_url=base_url,
            model=ollama_config.get("model", "mimo-v2-flash"),
            api_key=ollama_config.get("api_key", "")
        )
    else:
        from ollama_client import OllamaClient
        return OllamaClient(
            base_url=base_url,
            model=ollama_config.get("model", "llama3")
        )


class ChatThread(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client, message, memory_system):
        super().__init__()
        self.client = client
        self.message = message
        self.memory_system = memory_system

    def run(self):
        try:
            context = self.memory_system.get_context()
            response = self.client.chat(self.message, context)
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
        self.gif_search_path = "duckygif/duckyoqiaojianpan.gif"
        self.gif_sleep_path = "duckygif/duckyosleep.gif"
        self.gif_caboli_path = "duckygif/duckyocaboli.gif"
        self.gif_feiwu_path = "duckygif/duckyofeiwu.gif"
        self.gif_swanan_path = "duckygif/duckyoswanan.gif"
        self.gif_xixi_path = "duckygif/duckyoxixi.gif"
        self.movie = QMovie(self.gif_path)
        self.movie.setScaledSize(QPixmap(self.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.movie_default = self.movie
        
        pixmap = QPixmap(self.gif_path)
        self.pet_size = min(150, max(120, max(pixmap.width(), pixmap.height())))
        
        self.is_sleeping = False
        self.is_swanan = False
        self.is_caboli = False
        self.is_feiwu = False
        self.is_xixi = False
        self.sleep_timeout = 120000
        
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        
        self.canvas_width = max(280, self.pet_size + 30)
        self.canvas_height = self.pet_size + 620
        
        self.setFixedSize(self.canvas_width, self.canvas_height)
        self.move(self.position)
        self.setMouseTracking(True)
        
        self.gif_label = QLabel(self)
        self.gif_label.setMovie(self.movie)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setFixedSize(self.pet_size, self.pet_size)
        self.gif_label.move((self.canvas_width - self.pet_size) // 2, 250)
        self.gif_label.setStyleSheet("background: transparent; border: none;")
        self.gif_label.setMouseTracking(True)
        self.gif_label.installEventFilter(self)
        
        self.input_frame = QWidget(self)
        self.input_frame.setGeometry(0, self.pet_size + 260, self.canvas_width, 150)
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
        if self.is_sleeping or self.is_swanan:
            self.wake_up()
        
        if self.is_caboli or self.is_feiwu or self.is_xixi:
            self.is_caboli = False
            self.is_feiwu = False
            self.is_xixi = False
        
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
        
        need_search_keywords = ["今天", "昨天", "明天", "新闻", "天气", "最新", "现在", "热搜", "几号", "星期几",
                               "是什么", "怎么样", "如何", "为什么", "哪个", "哪里", "多少", "介绍", "科技", "财经", "体育", "娱乐",
                               "上网", "怎么"]
        need_search = any(kw in message for kw in need_search_keywords)
        
        self.movie.stop()
        if Path(self.gif_thinking_path).exists():
            self.movie = QMovie(self.gif_thinking_path)
            self.movie.setScaledSize(QPixmap(self.gif_thinking_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        
        if need_search and Path(self.gif_search_path).exists():
            QTimer.singleShot(2000, self._switch_to_search_gif)
        
        if hasattr(self, '_chat_callback'):
            self._chat_callback(message)
        self.input_box.setPlaceholderText("等待回复...")
        self.input_box.clear()
    
    def _switch_to_search_gif(self):
        self.movie.stop()
        self.movie = QMovie(self.gif_search_path)
        self.movie.setScaledSize(QPixmap(self.gif_search_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

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
        self.caboli_timer.start(10000)
        
        self.feiwu_timer = QTimer(self)
        self.feiwu_timer.timeout.connect(self.check_feiwu)
        self.feiwu_timer.start(10000)

    def check_caboli(self):
        if self.is_hovering or self.is_sleeping or self.is_caboli or self.is_feiwu:
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

    def check_feiwu(self):
        if self.is_hovering or self.is_sleeping or self.is_caboli or self.is_feiwu:
            return
        if hasattr(self, '_active_thread') and self._active_thread is not None:
            return
        if random.random() < 0.25:
            self.play_feiwu()

    def play_feiwu(self):
        if not Path(self.gif_feiwu_path).exists():
            return
        self.is_feiwu = True
        self.movie.stop()
        self.movie = QMovie(self.gif_feiwu_path)
        self.movie.setScaledSize(QPixmap(self.gif_feiwu_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        QTimer.singleShot(10000, self.stop_feiwu)

    def stop_feiwu(self):
        self.is_feiwu = False
        self.movie.stop()
        self.movie = QMovie(self.gif_path)
        self.movie.setScaledSize(QPixmap(self.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def check_sleep(self):
        if self.is_hovering:
            self.last_activity_time = QTime.currentTime()
            return
        if hasattr(self, '_active_thread') and self._active_thread is not None:
            return
            
        elapsed = self.last_activity_time.msecsTo(QTime.currentTime())
        
        if elapsed >= self.sleep_timeout and not self.is_sleeping:
            self.go_to_sleep()
        elif elapsed >= 180000 and not self.is_swanan:
            self.go_to_swanan()

    def go_to_sleep(self):
        self.is_sleeping = True
        self.movie.stop()
        if Path(self.gif_sleep_path).exists():
            self.movie = QMovie(self.gif_sleep_path)
            self.movie.setScaledSize(QPixmap(self.gif_sleep_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def go_to_swanan(self):
        self.is_swanan = True
        self.movie.stop()
        if Path(self.gif_swanan_path).exists():
            self.movie = QMovie(self.gif_swanan_path)
            self.movie.setScaledSize(QPixmap(self.gif_swanan_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def wake_up(self):
        self.is_sleeping = False
        self.is_swanan = False
        self.last_activity_time = QTime.currentTime()
        self.movie.stop()
        self.movie = QMovie(self.gif_path)
        self.movie.setScaledSize(QPixmap(self.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def walk(self):
        if self.is_hovering or self.is_sleeping or self.is_swanan or self.is_caboli or self.is_feiwu:
            return
            
        if random.random() < 0.02:
            self.target_position = QPoint(
                random.randint(100, self.screen_rect.width() - 200),
                random.randint(100, self.screen_rect.height() - 400)
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
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
        elif event.button() == Qt.LeftButton:
            self.drag_start_pos = event.globalPos()
            self.is_dragging = True

    def mouseMoveEvent(self, event):
        if hasattr(self, 'is_dragging') and self.is_dragging and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.drag_start_pos
            self.position = self.position + delta
            self.move(self.position)
            self.drag_start_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'is_dragging'):
            self.is_dragging = False

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        history_action = QAction("查看对话记录", self)
        history_action.triggered.connect(self.show_conversation_history)
        menu.addAction(history_action)
        
        menu.addSeparator()
        
        pet_menu = QMenu("切换宠物", self)
        colors = [("粉色猫咪", "#FFB6C1"), ("蓝色小狗", "#87CEEB"), ("绿色青蛙", "#90EE90"), ("橙色狐狸", "#FFD700")]
        for name, color in colors:
            action = QAction(name, self)
            action.triggered.connect(lambda c, n=name: self.change_pet(n, c))
            pet_menu.addAction(action)
        menu.addMenu(pet_menu)

        menu.exec_(pos)

    def show_conversation_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("对话记录")
        dialog.setFixedSize(500, 600)
        
        layout = QVBoxLayout(dialog)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        if hasattr(self, '_memory_system'):
            conversations = self._memory_system.conversations
            if conversations:
                content = "<b>最近对话记录</b><br><br>"
                for conv in reversed(conversations[-20:]):
                    time_str = conv.get('timestamp', '')[:16]
                    content += f"<b>[{time_str}]</b><br>"
                    content += f"<b>主人:</b> {conv.get('user', '')}<br>"
                    content += f"<b>YBduckyo:</b> {conv.get('pet', '')}<br>"
                    content += "<br>" + "-"*50 + "<br><br>"
                text_edit.setHtml(content)
            else:
                text_edit.setHtml("<center>暂无对话记录</center>")
        else:
            text_edit.setHtml("<center>暂无对话记录</center>")
        
        scroll.setWidget(text_edit)
        layout.addWidget(scroll)
        
        close_btn = QB("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec_()

    def change_pet(self, name, color):
        self.pet_name = name
        self.pet_color = color
        self.update()


class DesktopPetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.pets = []
        self.client = get_client(self.config)
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
            if Path(pet.gif_xixi_path).exists():
                pet.is_xixi = True
                pet.movie = QMovie(pet.gif_xixi_path)
                pet.movie.setScaledSize(QPixmap(pet.gif_xixi_path).size().scaled(150, 150, Qt.KeepAspectRatio))
            pet.gif_label.setMovie(pet.movie)
            pet.movie.start()
            
            if not pet.is_hovering:
                pet.input_frame.hide()
        
        def on_error(e):
            self.show_response_bubble(pet, f"错误: {e}")
            pet._active_thread = None
            pet.input_box.setPlaceholderText("输入消息...")
        
        chat_thread = ChatThread(self.client, message, self.memory_system)
        chat_thread.response_ready.connect(show_response)
        chat_thread.error_occurred.connect(on_error)
        pet._active_thread = chat_thread
        chat_thread.start()

    def show_response_bubble(self, pet, response):
        pet.response_label = QLabel(pet)
        pet.response_label.setWordWrap(True)
        pet.response_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        pet.response_label.setText(response)
        pet.response_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 250);
                border-radius: 15px;
                border: 2px solid #4CAF50;
                padding: 12px;
                font-size: 15px;
                color: #333;
            }
        """)
        
        bubble_width = pet.canvas_width
        pet.response_label.setFixedWidth(bubble_width)
        pet.response_label.adjustSize()
        
        if pet.response_label.height() < 50:
            pet.response_label.setFixedHeight(60)
        elif pet.response_label.height() > 210:
            pet.response_label.setFixedHeight(210)
        
        pet.response_label.move(0, 16)
        pet.response_label.show()
        QTimer.singleShot(5000, lambda: self.hide_response_and_restore(pet))
        QTimer.singleShot(8000, pet.response_label.close)

    def hide_response_and_restore(self, pet):
        pet.is_xixi = False
        if not pet.is_hovering and not pet.is_sleeping and not pet.is_swanan:
            pet.movie.stop()
            pet.movie = QMovie(pet.gif_path)
            pet.movie.setScaledSize(QPixmap(pet.gif_path).size().scaled(150, 150, Qt.KeepAspectRatio))
            pet.gif_label.setMovie(pet.movie)
            pet.movie.start()

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
