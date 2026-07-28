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


# ---------------------------------------------------------------------------
# Background layers
# ---------------------------------------------------------------------------

class AnimatedBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # gradient bg
        g = QLinearGradient(QPointF(0, 0), QPointF(0, h))
        g.setColorAt(0, QColor(0, 10, 18))
        g.setColorAt(0.5, QColor(0, 26, 51))
        g.setColorAt(1, QColor(0, 10, 18))
        p.fillRect(0, 0, w, h, QBrush(g))

        # scanlines
        p.setPen(Qt.PenStyle.NoPen)
        for y in range(0, h, 4):
            c = QColor(0, 229, 255, 4)
            p.fillRect(0, y, w, 2, c)

        # hex grid
        pen = QPen(QColor(0, 229, 255, 10))
        pen.setWidth(1)
        p.setPen(pen)
        for x in range(0, w, 60):
            for y in range(0, h, 52):
                off = 30 if (y // 52) % 2 else 0
                cx, cy = x + off, y
                self._draw_hex(p, cx, cy, 20)

        # vignette
        vg = QRadialGradient(QPointF(w / 2, h / 2), max(w, h) * 0.7)
        vg.setColorAt(0, QColor(0, 0, 0, 0))
        vg.setColorAt(1, QColor(0, 0, 0, 180))
        p.fillRect(0, 0, w, h, QBrush(vg))

    @staticmethod
    def _draw_hex(p: QPainter, cx: float, cy: float, r: float):
        path = QPainterPath()
        for i in range(6):
            a = math.radians(60 * i - 30)
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        p.drawPath(path)


# ---------------------------------------------------------------------------
# Circular gauge (CPU / RAM)
# ---------------------------------------------------------------------------

class Gauge(QWidget):
    def __init__(self, label="", parent=None):
        super().__init__(parent)
        self._label = label
        self._value = 0
        self.setFixedSize(100, 110)

    def set_value(self, val: float):
        self._value = max(0, min(100, val))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = 50, 50
        r = 38
        w = 4

        # bg ring
        pen = QPen(QColor(0, 229, 255, 25), w)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 0, 360 * 16)

        # fg arc
        if self._value > 0:
            c = QColor(0, 229, 255)
            c.setAlpha(80 + int(120 * self._value / 100))
            pen = QPen(c, w)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            span = int(360 * 16 * self._value / 100)
            p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 90 * 16, -span)

        # value text
        f = QFont("JetBrains Mono", 14, QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(QColor(0, 229, 255))
        tr = QRectF(0, cy - 10, self.width(), 20)
        p.drawText(tr, Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}%")

        # label
        f2 = QFont("Rajdhani", 9)
        p.setFont(f2)
        p.setPen(QColor(0, 184, 204))
        lr = QRectF(0, cy + 14, self.width(), 16)
        p.drawText(lr, Qt.AlignmentFlag.AlignCenter, self._label)


# ---------------------------------------------------------------------------
# Metric progress bar
# ---------------------------------------------------------------------------

class MetricBar(QWidget):
    def __init__(self, label="", parent=None):
        super().__init__(parent)
        self._label = label
        self._value = 0
        self._suffix = ""
        self.setFixedHeight(28)

    def set_value(self, val: float, suffix=""):
        self._value = max(0, min(100, val))
        self._suffix = suffix
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        f = QFont("JetBrains Mono", 8)
        p.setFont(f)

        # label
        p.setPen(QColor(0, 184, 204))
        p.drawText(QRectF(4, 0, w * 0.45, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._label)

        # value
        suffix = f" {self._suffix}" if self._suffix else ""
        p.setPen(QColor(120, 200, 220))
        p.drawText(QRectF(w * 0.45, 0, w * 0.55 - 4, 14),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{self._value:.0f}%{suffix}")

        # track
        ty = 18
        p.fillRect(4, ty, w - 8, 3, QColor(0, 229, 255, 15))

        # fill
        fw = max(0, w - 8) * self._value / 100
        if fw > 0:
            c = QColor(0, 229, 255)
            c.setAlpha(120)
            p.fillRect(4, ty, int(fw), 3, c)
            p.fillRect(4, ty, int(fw), 1, QColor(0, 229, 255, 60))


# ---------------------------------------------------------------------------
# Log lines
# ---------------------------------------------------------------------------

class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines: list[str] = []
        self.setMinimumHeight(80)

    def append(self, msg: str):
        self._lines.insert(0, msg.upper())
        if len(self._lines) > 30:
            self._lines.pop()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont("JetBrains Mono", 7)
        p.setFont(f)

        y = 0
        for line in self._lines[:20]:
            p.setPen(QColor(0, 184, 204))
            p.drawText(QRectF(4, y, 10, 14), Qt.AlignmentFlag.AlignLeft, ">")
            p.setPen(QColor(0, 229, 255, 180))
            p.drawText(QRectF(14, y, self.width() - 18, 14), Qt.AlignmentFlag.AlignLeft, line)
            y += 14


# ---------------------------------------------------------------------------
# Animated core rings
# ---------------------------------------------------------------------------

class CoreRings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0.0
        self._pulse = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self.setMinimumSize(160, 160)

    def _tick(self):
        self._angle = (self._angle + 0.02) % (2 * math.pi)
        self._pulse = (self._pulse + 0.015) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        r = min(cx, cy) * 0.7

        # rings
        rings_config = [(r * 1.0, 0.5), (r * 0.8, 1.0), (r * 0.55, 1.5)]
        for i, (radius, dash) in enumerate(rings_config):
            p.save()
            p.translate(cx, cy)
            rot = math.degrees(self._angle) + i * 120
            p.rotate(rot)

            pen = QPen(QColor(0, 229, 255, 60 - i * 15), 2 - i * 0.5)
            pen.setDashPattern([6 * dash, 4 * dash])
            p.setPen(pen)
            p.drawEllipse(QPointF(0, 0), radius, radius * 0.6)
            p.restore()

        # "F" center
        pulse = 0.8 + 0.2 * math.sin(self._pulse)
        glow = QRadialGradient(QPointF(cx, cy), r * 0.25)
        glow.setColorAt(0, QColor(0, 229, 255, int(200 * pulse)))
        glow.setColorAt(0.5, QColor(0, 60, 100, int(100 * pulse)))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r * 0.25, r * 0.25)

        f = QFont("Rajdhani", int(r * 0.25), QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(QColor(0, 229, 255))
        p.drawText(QRectF(cx - r * 0.2, cy - r * 0.15, r * 0.4, r * 0.3),
                    Qt.AlignmentFlag.AlignCenter, "F")


# ---------------------------------------------------------------------------
# Response box (output)
# ---------------------------------------------------------------------------

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

        self._text = QLabel("SYSTEM ONLINE. STANDING BY FOR INPUT...")
        self._text.setWordWrap(True)
        self._text.setStyleSheet("color: #c0d8ff; font-family: monospace; font-size: 11px; background: transparent;")
        layout.addWidget(self._text)

    def set_text(self, text: str):
        self._text.setText(text)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 229, 255), 1)
        p.setPen(pen)
        s = 8
        # corner decorations
        for x1, y1, x2, y2 in [(1, 1, s, 1), (1, 1, 1, s),
                                 (self.width() - 2, 1, self.width() - s - 1, 1),
                                 (self.width() - 2, 1, self.width() - 2, s),
                                 (1, self.height() - 2, s, self.height() - 2),
                                 (1, self.height() - 2, 1, self.height() - s),
                                 (self.width() - 2, self.height() - 2, self.width() - s - 1, self.height() - 2),
                                 (self.width() - 2, self.height() - 2, self.width() - 2, self.height() - s)]:
            p.drawLine(x1, y1, x2, y2)


# ---------------------------------------------------------------------------
# Agent card
# ---------------------------------------------------------------------------

class AgentCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name: str, icon: str, parent=None):
        super().__init__(parent)
        self._name = name
        self._icon = icon
        self._status = "idle"
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setStyleSheet("background: transparent; font-size: 16px;")
        layout.addWidget(self._icon_lbl)

        nl = QVBoxLayout()
        nl.setSpacing(0)
        self._name_lbl = QLabel(name.replace("_", " ").title())
        self._name_lbl.setStyleSheet("color: #c0d8ff; font-family: monospace; font-size: 11px; font-weight: 600; background: transparent;")
        nl.addWidget(self._name_lbl)
        self._status_lbl = QLabel("IDLE")
        self._status_lbl.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 9px; background: transparent;")
        nl.addWidget(self._status_lbl)
        layout.addLayout(nl, 1)

        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #4a6a8a; font-size: 8px; background: transparent;")
        layout.addWidget(self._dot)

        self._update_style()

    def set_status(self, status: str):
        self._status = status
        if status == "active":
            self._dot.setStyleSheet("color: #00ff88; font-size: 8px; background: transparent;")
            self._status_lbl.setText("ACTIVE")
            self._status_lbl.setStyleSheet("color: #00ff88; font-family: monospace; font-size: 9px; background: transparent;")
        elif status == "running":
            self._dot.setStyleSheet("color: #00e5ff; font-size: 8px; background: transparent;")
            self._status_lbl.setText("RUNNING")
            self._status_lbl.setStyleSheet("color: #00e5ff; font-family: monospace; font-size: 9px; background: transparent;")
        else:
            self._dot.setStyleSheet("color: #4a6a8a; font-size: 8px; background: transparent;")
            self._status_lbl.setText("IDLE")
            self._status_lbl.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 9px; background: transparent;")
        self._update_style()

    def _update_style(self):
        border = "#00ff8840" if self._status == "active" else "rgba(0,229,255,0.1)"
        bg = "rgba(0,255,136,0.05)" if self._status == "active" else "rgba(0,229,255,0.03)"
        self.setStyleSheet(f"""
            AgentCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            AgentCard:hover {{
                background: rgba(0,229,255,0.08);
                border-color: rgba(0,229,255,0.3);
            }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self._name)


# ---------------------------------------------------------------------------
# Provider row
# ---------------------------------------------------------------------------

class ProviderRow(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self._name = QLabel(name)
        self._name.setStyleSheet("color: #6b8caa; font-family: monospace; font-size: 9px; background: transparent;")
        layout.addWidget(self._name)
        layout.addStretch()

        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #4a6a8a; font-size: 6px; background: transparent;")
        layout.addWidget(self._dot)

    def set_online(self, online: bool):
        c = "#00ff88" if online else "#4a6a8a"
        self._dot.setStyleSheet(f"color: {c}; font-size: 6px; background: transparent;")


# ---------------------------------------------------------------------------
# Top bar status pill
# ---------------------------------------------------------------------------

class StatusPill(QWidget):
    def __init__(self, label: str, color: str = "#00ff88", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 6px; background: transparent;")
        layout.addWidget(dot)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #c0d8ff; font-family: monospace; font-size: 9px; background: transparent;")
        layout.addWidget(lbl)

        self.setStyleSheet(f"""
            StatusPill {{
                border: 1px solid rgba(0,229,255,0.2);
                border-radius: 12px;
                background: rgba(0,229,255,0.05);
            }}
        """)


# ---------------------------------------------------------------------------
# Command bar (form input + TRANSMIT button)
# ---------------------------------------------------------------------------

class CommandBar(QWidget):
    submitted = pyqtSignal(str)
    voice_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(12)

        self._voice_btn = QPushButton("🎤")
        self._voice_btn.setFixedSize(44, 44)
        self._voice_btn.setCheckable(True)
        self._voice_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,229,255,0.1);
                border: 1px solid #00e5ff;
                border-radius: 22px;
                font-size: 18px;
            }
            QPushButton:hover { background: rgba(0,229,255,0.2); }
            QPushButton:checked {
                background: rgba(0,229,255,0.2);
                border-color: #00ff88;
            }
        """)
        self._voice_btn.toggled.connect(lambda c: self.voice_toggled.emit(c))
        layout.addWidget(self._voice_btn)

        self._input = QLineEdit()
        self._input.setPlaceholderText("SAY 'HEY FRIDAY' OR TYPE COMMAND...")
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
            QLineEdit:focus {
                border-color: #00e5ff;
            }
        """)
        self._input.returnPressed.connect(self._submit)
        layout.addWidget(self._input, 1)

        self._send_btn = QPushButton("TRANSMIT")
        self._send_btn.setStyleSheet("""
            QPushButton {
                font-family: Rajdhani;
                font-weight: 700;
                background: rgba(0,229,255,0.1);
                border: 1px solid #00e5ff;
                color: #00e5ff;
                padding: 7px 18px;
                letter-spacing: 2px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #00e5ff;
                color: #000;
            }
        """)
        self._send_btn.clicked.connect(self._submit)
        layout.addWidget(self._send_btn)

    def _submit(self):
        text = self._input.text().strip()
        if text:
            self.submitted.emit(text)
            self._input.clear()

    def set_text(self, text: str):
        self._input.setText(text)

    def focus(self):
        self._input.setFocus()

    @property
    def text(self):
        return self._input.text()


# ---------------------------------------------------------------------------
# Agent panel container
# ---------------------------------------------------------------------------

class AgentPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("AgentPanel { background: transparent; }")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        header = QLabel("ACTIVE AGENTS")
        header.setStyleSheet("color: #00e5ff; font-family: Rajdhani; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;")
        self._layout.addWidget(header)

        self._agent_widgets: dict[str, AgentCard] = {}

    def add_agent(self, name: str, icon: str):
        card = AgentCard(name, icon)
        self._layout.addWidget(card)
        self._agent_widgets[name] = card
        return card

    def set_status(self, name: str, status: str):
        w = self._agent_widgets.get(name)
        if w:
            w.set_status(status)


# ---------------------------------------------------------------------------
# Provider panel container
# ---------------------------------------------------------------------------

class ProviderPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("ProviderPanel { background: transparent; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        header = QLabel("PROVIDERS")
        header.setStyleSheet("color: #00e5ff; font-family: Rajdhani; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;")
        layout.addWidget(header)

        self._rows: dict[str, ProviderRow] = {}

    def add_provider(self, name: str, online: bool = False):
        row = ProviderRow(name)
        row.set_online(online)
        self._rows[name.lower()] = row
        self.layout().addWidget(row)

    def set_online(self, name: str, online: bool):
        row = self._rows.get(name.lower())
        if row:
            row.set_online(online)


# ---------------------------------------------------------------------------
# Panel wrapper with header
# ---------------------------------------------------------------------------

class Panel(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            Panel {{
                background: rgba(0,26,51,0.2);
                border: 1px solid rgba(0,229,255,0.15);
                border-radius: 4px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        header = QLabel(title)
        header.setStyleSheet("color: #00e5ff; font-family: Rajdhani; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;")
        layout.addWidget(header)

        self._content = QVBoxLayout()
        self._content.setSpacing(4)
        layout.addLayout(self._content)

        self._layout = layout

    def add_widget(self, w: QWidget):
        self._content.addWidget(w)

    def add_layout(self, l):
        self._content.addLayout(l)
