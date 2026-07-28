from __future__ import annotations
import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath,
    QPen, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)


class AnimatedBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: self.update())
        self._timer.start(50)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        g = QLinearGradient(QPointF(0, 0), QPointF(0, h))
        g.setColorAt(0, QColor(0, 10, 18))
        g.setColorAt(0.5, QColor(0, 26, 51))
        g.setColorAt(1, QColor(0, 10, 18))
        p.fillRect(0, 0, w, h, QBrush(g))

        p.setPen(Qt.PenStyle.NoPen)
        for y in range(0, h, 4):
            p.fillRect(0, y, w, 1, QColor(0, 229, 255, 3))

        pen = QPen(QColor(0, 229, 255, 8))
        pen.setWidth(1)
        p.setPen(pen)
        for x in range(0, w, 60):
            for y in range(0, h, 52):
                cx = x + 30
                cy = y + 26
                for i in range(6):
                    a = math.radians(60 * i - 30)
                    ox = cx + 14 * math.cos(a)
                    oy = cy + 14 * math.sin(a)
                    p.drawPoint(QPointF(ox, oy))


class ResponseBox(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ResponseBox {
                background: rgba(0, 26, 51, 0.4);
                border: 1px solid rgba(0, 229, 255, 0.3);
                border-radius: 2px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self._text = QLabel("SYSTEM ONLINE. STANDING BY FOR INPUT, SIR.")
        self._text.setWordWrap(True)
        self._text.setStyleSheet("color: #c0d8ff; font-family: monospace; font-size: 11px; background: transparent;")
        layout.addWidget(self._text)

    def set_text(self, text: str):
        self._text.setText(text)


class CommandBar(QWidget):
    submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self._input = QLineEdit()
        self._input.setPlaceholderText("TYPE COMMAND OR ASK ANYTHING...")
        self._input.setStyleSheet("""
            QLineEdit {
                background: rgba(0,26,51,0.6);
                border: 1px solid rgba(0,229,255,0.3);
                border-radius: 4px;
                color: #00e5ff;
                padding: 8px 14px;
                font-family: monospace;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #00e5ff; }
        """)
        self._input.returnPressed.connect(self._submit)
        self._history: list[str] = []
        self._history_index = -1
        self._saved = ""
        self._input.installEventFilter(self)
        layout.addWidget(self._input, 1)

        self._send = QPushButton("SEND")
        self._send.setStyleSheet("""
            QPushButton {
                font-family: Rajdhani; font-weight: 700;
                background: rgba(0,229,255,0.1);
                border: 1px solid #00e5ff;
                color: #00e5ff;
                padding: 7px 18px;
                letter-spacing: 2px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background: #00e5ff; color: #000; }
        """)
        self._send.clicked.connect(self._submit)
        layout.addWidget(self._send)

    def eventFilter(self, obj, event):
        if obj is self._input and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                self._history_up()
                return True
            elif key == Qt.Key.Key_Down:
                self._history_down()
                return True
        return super().eventFilter(obj, event)

    def _history_up(self):
        if not self._history:
            return
        if self._history_index == -1:
            self._saved = self._input.text()
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._input.setText(self._history[-(self._history_index + 1)])

    def _history_down(self):
        if self._history_index == -1:
            return
        self._history_index -= 1
        if self._history_index <= -1:
            self._input.setText(self._saved)
            self._history_index = -1
        else:
            self._input.setText(self._history[-(self._history_index + 1)])

    def _submit(self):
        text = self._input.text().strip()
        if text:
            if not self._history or self._history[-1] != text:
                self._history.append(text)
            self._history_index = -1
            self.submitted.emit(text)
            self._input.clear()


class AgentPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        agents = ["chat", "research", "code", "study", "planner", "gaming"]
        for a in agents:
            lbl = QLabel(a.upper())
            lbl.setStyleSheet("""
                color: rgba(0,229,255,0.6);
                font-family: Rajdhani; font-size: 10px;
                font-weight: 700; letter-spacing: 1px;
                background: rgba(0,229,255,0.05);
                border: 1px solid rgba(0,229,255,0.15);
                border-radius: 2px; padding: 2px 8px;
            """)
            layout.addWidget(lbl)
        layout.addStretch()


class LogPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            LogPanel {
                background: rgba(0, 26, 51, 0.3);
                border: 1px solid rgba(0, 229, 255, 0.15);
                border-radius: 2px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self._log = QLabel("")
        self._log.setStyleSheet("color: rgba(0,229,255,0.5); font-family: monospace; font-size: 9px; background: transparent;")
        layout.addWidget(self._log)
        self._messages: list[str] = []

    def add_message(self, msg: str):
        self._messages.append(msg)
        self._messages = self._messages[-3:]
        self._log.setText("\n".join(self._messages))


class StatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        self._status = QLabel("STANDBY")
        self._status.setStyleSheet("color: rgba(0,229,255,0.4); font-family: Rajdhani; font-size: 9px; font-weight: 700; letter-spacing: 2px; background: transparent;")
        layout.addWidget(self._status)
        layout.addStretch()

    def set_status(self, text: str):
        self._status.setText(text)


class HelpDialog(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(480, 460)
        self.setStyleSheet("""
            HelpDialog {
                background: rgba(8, 8, 30, 0.97);
                border: 1px solid rgba(0, 229, 255, 0.3);
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        header = QLabel("FRIDAY COMMANDS")
        header.setStyleSheet("color: #00e5ff; font-family: Rajdhani; font-size: 15px; font-weight: 700; letter-spacing: 2px; background: transparent;")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        il = QVBoxLayout(inner)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(4)

        _C = "color: #00e5ff; font-family: monospace; font-size: 11px; background: transparent;"
        _D = "color: #8aaac0; font-family: monospace; font-size: 11px; background: transparent;"
        _S = "color: #00b8cc; font-family: Rajdhani; font-size: 11px; font-weight: 700; background: transparent; margin-top: 4px;"

        sections = [
            ("CHAT", [("<ask anything>", "Natural conversation"), ("exit / quit", "Shutdown")]),
            ("AGENTS", [("/agents", "List agents"), ("/research <q>", "Deep research"), ("/code <q>", "Software engineering"), ("/study <q>", "Study mentor"), ("/plan <q>", "Project planning")]),
            ("SYSTEM", [("/status", "System state"), ("/history", "Conversation history"), ("/clear", "Clear screen"), ("/learn", "Self-reflect & learn"), ("/feedback <1-5>", "Rate response")]),
            ("SHORTCUTS", [("Ctrl+H", "Toggle this help"), ("Ctrl+Q", "Quit"), ("Escape", "Close overlay / minimize"), ("Up/Down", "Command history")]),
        ]

        for title, items in sections:
            lbl = QLabel(f"# {title}")
            lbl.setStyleSheet(_S)
            il.addWidget(lbl)
            for cmd, desc in items:
                row = QHBoxLayout()
                row.setSpacing(10)
                c = QLabel(cmd)
                c.setStyleSheet(_C)
                c.setFixedWidth(140)
                row.addWidget(c)
                d = QLabel(desc)
                d.setStyleSheet(_D)
                row.addWidget(d, 1)
                il.addLayout(row)

        il.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

        close_btn = QPushButton("CLOSE")
        close_btn.setStyleSheet("""
            QPushButton {
                font-family: Rajdhani; font-weight: 700;
                background: rgba(0,229,255,0.1);
                border: 1px solid #00e5ff;
                color: #00e5ff;
                padding: 6px 20px;
                letter-spacing: 2px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #00e5ff; color: #000; }
        """)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)
