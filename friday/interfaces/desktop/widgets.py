from __future__ import annotations

import asyncio
import logging
import math
import os
import random
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("friday.desktop.widgets")


class HoloSphere(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0.0
        self._pulse = 0.0
        self._sparkle_time = 0.0
        self._particles = []
        self._inner_particles = []
        self._init_particles()
        self._init_inner_particles()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self.setMinimumSize(120, 120)

    def _init_particles(self):
        for i in range(80):
            particle_type = random.randint(0, 2)
            if particle_type == 0:  # Core particles
                size_range = (2.5, 4.5)
                speed_range = (0.4, 0.9)
                radius_range = (0.15, 0.35)
                alpha_base = 0.8
                color_hue = random.uniform(0, 360)
            elif particle_type == 1:  # Mid-ring particles
                size_range = (1.2, 2.5)
                speed_range = (1.0, 2.5)
                radius_range = (0.4, 0.7)
                alpha_base = 0.5
                color_hue = random.uniform(180, 340)
            else:  # Outer-ring particles
                size_range = (0.8, 2.0)
                speed_range = (1.8, 3.5)
                radius_range = (0.6, 0.9)
                alpha_base = 0.3
                color_hue = random.uniform(340, 360) + random.uniform(0, 60)

            self._particles.append(
                {
                    "angle": random.uniform(0, 2 * math.pi),
                    "speed": random.uniform(*speed_range),
                    "radius": random.uniform(*radius_range),
                    "size": random.uniform(*size_range),
                    "alpha": alpha_base * random.uniform(0.7, 1.0),
                    "type": particle_type,
                    "color_hue": color_hue,
                    "color_sat": random.uniform(60, 100),
                    "color_val": random.uniform(60, 90),
                    "tail_length": random.uniform(8, 20),
                    "trail_speed": random.uniform(0.3, 0.8),
                    "sparkle_prob": 0.02 if particle_type == 0 else 0.01,
                    "glow_intensity": random.uniform(0.3, 0.7),
                    "last_update": random.uniform(0, 1),
                }
            )

    def _init_inner_particles(self):
        for i in range(20):
            self._inner_particles.append(
                {
                    "angle": random.uniform(0, 2 * math.pi),
                    "speed": random.uniform(0.5, 1.5),
                    "radius": random.uniform(0.05, 0.15),
                    "size": random.uniform(0.5, 1.5),
                    "alpha": random.uniform(0.4, 0.8),
                    "phase": random.uniform(0, 2 * math.pi),
                    "glow_phase": random.uniform(0, 6.28),
                }
            )

    def _tick(self):
        self._angle = (self._angle + 0.025) % (2 * math.pi)
        self._pulse = (self._pulse + 0.015) % (2 * math.pi)
        self._sparkle_time = (self._sparkle_time + 0.05) % (2 * math.pi)

        for p in self._particles:
            p["angle"] = (p["angle"] + p["speed"] * 0.015) % (2 * math.pi)
            p["last_update"] = (p["last_update"] + 0.015) % 1.0

            # Update tail effects
            if p["last_update"] < 0.3:
                p["alpha"] = max(0.1, p["alpha"] * 0.98)
            else:
                p["alpha"] = min(0.2, p["alpha"] * 1.02)

        # Add sparkle effects occasionally
        if random.random() < 0.02:
            idx = random.randrange(len(self._particles))
            p = self._particles[idx]
            p["sparkle"] = True
            p["sparkle_timer"] = 0.0

        for p in self._inner_particles:
            p["angle"] = (p["angle"] + p["speed"] * 0.015) % (2 * math.pi)
            p["phase"] = (p["phase"] + 0.02) % (2 * math.pi)
            p["glow_phase"] = (p["glow_phase"] + 0.03) % (2 * math.pi)

        self.update()

    def paintEvent(self, event):  # noqa: N802
        if self.width() <= 0 or self.height() <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        radius = min(cx, cy) * 0.65
        max_particle_radius = radius * 0.9

        # Create a backup painter for effects
        painter.save()

        # Background gradient with animated glow
        bg_gradient = QLinearGradient(QPointF(0, 0), QPointF(0, self.height()))
        bg_gradient.setColorAt(0, QColor(8, 8, 20, 255))
        bg_gradient.setColorAt(0.3, QColor(15, 15, 40, 255))
        bg_gradient.setColorAt(0.7, QColor(8, 8, 25, 255))
        bg_gradient.setColorAt(1, QColor(5, 5, 20, 255))
        painter.fillRect(0, 0, self.width(), self.height(), QBrush(bg_gradient))

        # Outer luminous halo
        outer_glow_radius = max_particle_radius * 2.2
        outer_glow = QRadialGradient(QPointF(cx, cy), outer_glow_radius)
        outer_glow.setColorAt(0, QColor(0, 180, 255, 10))
        outer_glow.setColorAt(0.2, QColor(0, 100, 255, 25))
        outer_glow.setColorAt(0.4, QColor(0, 50, 200, 50))
        outer_glow.setColorAt(0.6, QColor(0, 30, 150, 75))
        outer_glow.setColorAt(0.8, QColor(0, 15, 100, 100))
        outer_glow.setColorAt(1, QColor(0, 0, 80, 120))
        painter.setBrush(QBrush(outer_glow))
        painter.drawEllipse(QPointF(cx, cy), outer_glow_radius, outer_glow_radius)

        # Core holographic sphere with animated gradients
        core_gradient = QRadialGradient(QPointF(cx, cy), max_particle_radius)
        core_gradient.setColorAt(0, QColor(255, 255, 255, 50 + int(30 * math.sin(self._pulse))))
        core_gradient.setColorAt(0.15, QColor(0, 180, 255, 80 + int(40 * math.sin(self._pulse + math.pi / 4))))
        core_gradient.setColorAt(0.3, QColor(0, 120, 255, 120 + int(25 * math.sin(self._pulse * 2))))
        core_gradient.setColorAt(0.5, QColor(0, 80, 180, 150))
        core_gradient.setColorAt(0.6, QColor(0, 60, 140, 100))
        core_gradient.setColorAt(0.7, QColor(0, 40, 120, 50))
        core_gradient.setColorAt(0.8, QColor(0, 30, 100, 30))
        core_gradient.setColorAt(1, QColor(0, 0, 60, 8))
        painter.setBrush(QBrush(core_gradient))

        # Add subtle rotation for dynamic appearance
        painter.save()
        painter.rotate(math.sin(self._pulse * 0.5) * 2)
        painter.drawEllipse(
            QPointF(cx - max_particle_radius, cy - max_particle_radius),
            max_particle_radius * 2,
            max_particle_radius * 2,
        )
        painter.restore()

        # Enhanced orbit rings
        pen_orb = QPen(QColor(0, 200, 255, 120), 1)
        pen_orb.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_orb)

        # Multiple orbit rings with variations
        # Create dynamic rings based on time for visual interest
        rings = []
        time_now = (math.sin(self._sparkle_time) + 1) / 2

        # Add more rings for complexity
        ring_configs = [
            (1.15, 0.3),
            (1.3, 0.5),
            (1.45, 0.7),
            (1.6, time_now * 0.9),
            (1.8, 0.6),
        ]

        for outer_factor, inner_factor in ring_configs:
            rings.append((max_particle_radius * outer_factor, max_particle_radius * inner_factor))

        for i, (outer_r, inner_r) in enumerate(rings):
            ring_glow = 1.0 + 0.3 * math.sin(time_now * 3 + i)
            pen_orb.setColor(QColor(0, 200, 255, int(60 * ring_glow)))

            painter.save()
            painter.translate(cx, cy)
            angle = self._angle * 180 / math.pi + i * 120
            painter.rotate(angle)

            # Draw ring with glow effect
            painter.setPen(pen_orb)
            painter.drawEllipse(QPointF(0, 0), outer_r, inner_r)

            # Add inner highlight
            painter.setPen(QPen(QColor(0, 220, 255, 50), 0.5))
            painter.drawEllipse(QPointF(0, 0), inner_r * 0.7, inner_r * 0.7)

            painter.restore()

        # Draw particles with enhanced effects
        for p in self._particles:
            px = cx + p["radius"] * max_particle_radius * math.cos(p["angle"])
            py = cy + p["radius"] * max_particle_radius * math.sin(p["angle"]) * 0.6

            # Calculate particle brightness
            brightness = p["alpha"] * (0.6 + 0.4 * math.sin(self._pulse))
            base_color = QColor(int(p["color_hue"]), int(p["color_sat"]), int(p["color_val"]), int(brightness))

            # Draw main particle with glow effect
            painter.setPen(Qt.PenStyle.NoPen)

            # Create gradient for particle
            particle_gradient = QRadialGradient(QPointF(px, py), p["size"])
            particle_gradient.setColorAt(0, base_color.lighter(20))
            particle_gradient.setColorAt(0.7, base_color)
            particle_gradient.setColorAt(1, base_color.darker(50))
            painter.setBrush(QBrush(particle_gradient))

            # Draw particle
            painter.drawEllipse(QPointF(px - p["size"], py - p["size"]), p["size"] * 2, p["size"] * 2)

            # Draw tail effect
            if p.get("sparkle", False):
                painter.setPen(QPen(base_color, max(1, int(p["size"] * 0.5))))
                painter.drawLine(
                    QPointF(px, py),
                    QPointF(px - p["tail_length"] * math.cos(p["angle"]), py - p["tail_length"] * math.sin(p["angle"])),
                )
                p["sparkle"] = False

        # Draw inner particles
        for p in self._inner_particles:
            px = cx + p["radius"] * max_particle_radius * math.cos(p["angle"])
            py = cy + p["radius"] * max_particle_radius * math.sin(p["angle"])

            # Create glow for inner particles
            glow_color = QColor(0, 180, 255, int(150 * (0.5 + 0.5 * math.sin(p["glow_phase"]))))

            painter.setPen(QPen(glow_color, 0.5))
            painter.drawEllipse(QPointF(px - p["size"], py - p["size"]), p["size"] * 3, p["size"] * 3)

            # Add subtle rotation for inner particles
            painter.save()
            painter.translate(px, py)
            painter.rotate(p["phase"] * 180 / math.pi)
            painter.setPen(QPen(QColor(0, 200, 255, 100), 1))
            painter.drawEllipse(QPointF(-p["size"], -p["size"]), p["size"] * 2, p["size"] * 0.3)
            painter.restore()

        # Add central highlight
        center_highlight = QRadialGradient(QPointF(cx, cy), radius * 0.1)
        center_highlight.setColorAt(0, QColor(255, 255, 255, 200))
        center_highlight.setColorAt(0.5, QColor(0, 200, 255, 100))
        center_highlight.setColorAt(1, QColor(0, 100, 255, 0))
        painter.setBrush(QBrush(center_highlight))
        painter.drawEllipse(QPointF(cx - radius * 0.1, cy - radius * 0.1), radius * 0.2, radius * 0.2)

        # Add final border glow
        border_pen = QPen(QColor(0, 180, 255, 80), 2)
        border_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(border_pen)
        painter.drawEllipse(
            QPointF(cx - max_particle_radius, cy - max_particle_radius),
            max_particle_radius * 2,
            max_particle_radius * 2,
        )

        painter.restore()


class CircularProgress(QWidget):
    def __init__(self, label="", parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._max = 100.0
        self._label = label
        self._color = QColor(0, 200, 255)
        self._bg_color = QColor(255, 255, 255, 25)
        self.setMinimumSize(70, 80)

    def set_value(self, value):
        self._value = max(0, min(self._max, value))
        self.update()

    def set_color(self, color):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):  # noqa: N802
        if self.width() <= 0 or self.height() <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        m = 10
        rw = 5
        cx, cy = self.width() / 2, self.height() / 2
        r = side / 2 - m - rw

        # bg ring
        pen = QPen(self._bg_color, rw)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 0, 360 * 16)

        # fg arc
        if self._value > 0:
            c = QColor(self._color)
            c.setAlpha(min(255, 120 + int(135 * self._value / self._max)))
            pen = QPen(c, rw)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            span = int(360 * 16 * self._value / self._max)
            painter.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 90 * 16, -span)

        # value text
        f = QFont("monospace")
        f.setPixelSize(int(r * 0.55))
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor(210, 230, 255))
        tr = QRectF(0, cy - r * 0.35, self.width(), r * 0.7)
        painter.drawText(tr, Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}%")

        # label
        if self._label:
            f.setPixelSize(int(r * 0.22))
            f.setBold(False)
            painter.setFont(f)
            painter.setPen(QColor(130, 170, 210))
            lr = QRectF(0, cy + r * 0.15, self.width(), r * 0.35)
            painter.drawText(lr, Qt.AlignmentFlag.AlignCenter, self._label)


class CommandBar(QWidget):
    submitted = pyqtSignal(str)
    voice_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(34, 34)
        self.voice_btn.setCheckable(True)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 17px; font-size: 15px;
            }
            QPushButton:hover {
                background: rgba(0,200,255,0.12);
                border-color: rgba(0,200,255,0.3);
            }
            QPushButton:checked {
                background: rgba(0,255,100,0.18);
                border-color: rgba(0,255,100,0.4);
            }
        """)
        self.voice_btn.toggled.connect(lambda c: self.voice_toggled.emit(c))
        layout.addWidget(self.voice_btn)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command or ask anything...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(0,200,255,0.18);
                border-radius: 8px; color: #d0e0ff;
                padding: 7px 12px;
                font-family: monospace; font-size: 13px;
                selection-background-color: rgba(0,200,255,0.25);
            }
            QLineEdit:focus {
                border-color: rgba(0,200,255,0.5);
                background: rgba(255,255,255,0.07);
            }
        """)
        self.input_field.returnPressed.connect(self._submit)
        layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("⏎")
        self.send_btn.setFixedSize(34, 34)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,200,255,0.12);
                border: 1px solid rgba(0,200,255,0.25);
                border-radius: 17px; font-size: 15px; color: #a0d0ff;
            }
            QPushButton:hover {
                background: rgba(0,200,255,0.22);
                border-color: rgba(0,200,255,0.45);
            }
            QPushButton:pressed {
                background: rgba(0,200,255,0.32);
            }
        """)
        self.send_btn.clicked.connect(self._submit)
        layout.addWidget(self.send_btn)

    def _submit(self):
        text = self.input_field.text().strip()
        if text:
            self.submitted.emit(text)
            self.input_field.clear()

    def set_text(self, text):
        self.input_field.setText(text)

    def focus(self):
        self.input_field.setFocus()


class OutputArea(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background: rgba(0,0,0,0.25);
                border: 1px solid rgba(0,200,255,0.08);
                border-radius: 8px; color: #c0d8f0;
                padding: 6px 8px;
                font-family: monospace; font-size: 12px;
                selection-background-color: rgba(0,200,255,0.15);
            }
        """)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    @staticmethod
    def _render_markdown(text: str) -> str:
        import re

        text = re.sub(
            r"```(\w*)\n(.*?)```",
            r'<pre style="color:#00d4ff;background:rgba(0,0,0,0.3);padding:4px 8px;border-radius:4px;">\2</pre>',
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"`([^`]+)`",
            r'<code style="color:#ffaa00;background:rgba(0,0,0,0.2);padding:1px 4px;border-radius:2px;">\1</code>',
            text,
        )
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        text = re.sub(
            r"\[(.+?)\]\((.+?)\)", r'<a href="\2" style="color:#00d4ff;text-decoration:underline;">\1</a>', text
        )
        text = re.sub(r"^### (.+)$", r'<b style="color:#00d4ff;font-size:13px;">\1</b>', text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)$", r'<b style="color:#00d4ff;font-size:14px;">\1</b>', text, flags=re.MULTILINE)
        text = re.sub(r"^# (.+)$", r'<b style="color:#00d4ff;font-size:15px;">\1</b>', text, flags=re.MULTILINE)
        text = re.sub(r"^- (.+)$", r"• \1", text, flags=re.MULTILINE)
        text = re.sub(r"\n", r"<br>", text)
        return text

    def append_output(self, text: str, style: str = "normal"):
        colors = {
            "normal": "#c0d8f0",
            "system": "#00d4ff",
            "success": "#00ff88",
            "warning": "#ffaa00",
            "error": "#ff3355",
            "info": "#6b8caa",
        }
        prefixes = {
            "normal": "│ ",
            "system": "◈ ",
            "success": "✓ ",
            "warning": "⚠ ",
            "error": "✗ ",
            "info": "· ",
        }
        color = colors.get(style, colors["normal"])
        prefix = prefixes.get(style, "│ ")
        body = self._render_markdown(text)
        html = f'<span style="color:{color};">{prefix}{body}</span><br>'
        self.append(html)
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


class TitleBar(QWidget):
    profile_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._dragging = False
        self._drag_pos = None
        self.setFixedHeight(38)
        self.setStyleSheet("""
            TitleBar {
                background: rgba(0,0,0,0.4);
                border-bottom: 1px solid rgba(0,200,255,0.12);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 6, 0)
        layout.setSpacing(4)

        title = QLabel("FRIDAY AI OS")
        title.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        try:
            from friday import __version__

            ver = __version__
        except ImportError:
            ver = "1.0.0"
        vl = QLabel(f"v{ver}")
        vl.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 10px;")
        layout.addWidget(vl)
        layout.addStretch()

        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFixedSize(26, 22)
        self._settings_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #6b8caa; font-size: 13px; }
            QPushButton:hover { background: rgba(0,200,255,0.12); color: #00d4ff; }
        """)
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self._settings_btn)

        self._profile_btn = QPushButton("👤")
        self._profile_btn.setFixedSize(26, 22)
        self._profile_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #6b8caa; font-size: 13px; }
            QPushButton:hover { background: rgba(0,200,255,0.12); color: #00d4ff; }
        """)
        self._profile_btn.clicked.connect(self.profile_clicked.emit)
        layout.addWidget(self._profile_btn)

        self.status_lbl = QLabel("● ONLINE")
        self.status_lbl.setStyleSheet("color: #00ff88; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.status_lbl)
        layout.addSpacing(12)

        self._max_btn = QPushButton("□")
        for btn, slot in [
            (QPushButton("─"), self._parent.showMinimized),
            (self._max_btn, self._toggle_max),
            (QPushButton("×"), self._parent.close),
        ]:
            btn.setFixedSize(26, 22)
            is_close = btn.text() == "×"
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; color: #6b8caa; }}
                QPushButton:hover {{ background: rgba(255,255,255,0.08); color: #c0d8f0; }}
                {"QPushButton:hover { background: rgba(255,50,50,0.15); color: #ff3355; }" if is_close else ""}
            """)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

    def _toggle_max(self):
        if self._parent.isMaximized():
            self._parent.showNormal()
            self._max_btn.setText("□")
        else:
            self._parent.showMaximized()
            self._max_btn.setText("❐")

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._dragging and self._parent:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._parent.move(self._parent.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            event.accept()

    def set_status(self, text, color="#00ff88"):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color: {color}; font-family: monospace; font-size: 11px;")


class StatPanel(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            StatPanel {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(0,212,255,0.10);
                border-radius: 10px;
            }
        """)
        self._title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = CircularProgress(title)
        self.progress.setFixedSize(85, 95)
        layout.addWidget(self.progress, 0, Qt.AlignmentFlag.AlignCenter)

        self.detail = QLabel("--")
        self.detail.setStyleSheet("color: #6b8caa; font-family: monospace; font-size: 9px;")
        self.detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.detail)

    def set_value(self, value, detail=""):
        self.progress.set_value(value)
        self.detail.setText(detail)


class AgentPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            AgentPanel {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(0,212,255,0.10);
                border-radius: 10px;
            }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 8, 10, 8)
        self._layout.setSpacing(2)

        h = QLabel("AGENTS")
        h.setStyleSheet(
            "color: #00d4ff; font-family: monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        self._layout.addWidget(h)
        self._layout.addSpacing(4)

        self._rows = {}
        for name in [
            "mentor",
            "planner",
            "software_engineer",
            "research_scientist",
            "automation_engineer",
            "knowledge_manager",
            "study",
            "gaming_assistant",
        ]:
            self._add_row(name)

    def _add_row(self, name: str):
        if name in self._rows:
            return
        row = QHBoxLayout()
        row.setSpacing(6)
        dot = QLabel("○")
        dot.setFixedWidth(12)
        dot.setStyleSheet("color: #4a6a8a; font-size: 11px;")
        row.addWidget(dot)

        lbl = QLabel(name)
        lbl.setStyleSheet("color: #8aaac0; font-family: monospace; font-size: 11px;")
        row.addWidget(lbl)
        row.addStretch()

        st = QLabel("idle")
        st.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 10px;")
        row.addWidget(st)
        self._layout.addLayout(row)
        self._rows[name] = (dot, st)

    def set_status(self, name: str, status: str):
        if name not in self._rows:
            self._add_row(name)
        dot, st = self._rows[name]
        if status == "running":
            dot.setText("●")
            dot.setStyleSheet("color: #00d4ff; font-size: 11px;")
            st.setText("active")
            st.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 10px;")
        elif status == "done":
            dot.setText("✓")
            dot.setStyleSheet("color: #00ff88; font-size: 11px;")
            st.setText("done")
            st.setStyleSheet("color: #00ff88; font-family: monospace; font-size: 10px;")
        else:
            dot.setText("○")
            dot.setStyleSheet("color: #4a6a8a; font-size: 11px;")
            st.setText("idle")
            st.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 10px;")


class _Field(QWidget):
    """A labeled editable field for the profile panel."""

    def __init__(self, label: str, default="", is_long=False, parent=None):
        super().__init__(parent)
        self._editing = False
        self._default = default
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #8aaac0; font-family: monospace; font-size: 10px;")
        layout.addWidget(lbl)

        self._display = QLabel(default)
        self._display.setStyleSheet("color: #e0e8ff; font-family: monospace; font-size: 12px;")
        self._display.setWordWrap(is_long)
        layout.addWidget(self._display)

        if is_long:
            self._edit = QTextEdit()
            self._edit.setFixedHeight(60)
        else:
            self._edit = QLineEdit()
        self._edit.setStyleSheet("""
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(0,200,255,0.3);
            border-radius: 4px;
            color: #e0e8ff;
            padding: 2px 6px;
            font-family: monospace;
            font-size: 12px;
        """)
        self._edit.setVisible(False)
        layout.addWidget(self._edit)

    def set_value(self, val):
        self._display.setText(str(val))
        if isinstance(self._edit, QTextEdit):
            self._edit.setPlainText(str(val))
        else:
            self._edit.setText(str(val))

    def get_value(self):
        if isinstance(self._edit, QTextEdit):
            return self._edit.toPlainText()
        return self._edit.text()

    def set_edit_mode(self, editing: bool):
        self._editing = editing
        self._display.setVisible(not editing)
        self._edit.setVisible(editing)


class ProfilePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ProfilePanel {
                background: transparent;
            }
        """)
        self._editing = False
        self._profile_cache = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        # header with edit button
        hdr_row = QHBoxLayout()
        hdr = QLabel("◆ PROFILE")
        hdr.setStyleSheet(
            "color: #00d4ff; font-family: monospace; font-size: 12px; font-weight: bold; letter-spacing: 1px;"
        )
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()

        self._edit_btn = QPushButton("✎ Edit")
        self._edit_btn.setFixedHeight(24)
        self._edit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,200,255,0.1);
                border: 1px solid rgba(0,200,255,0.2);
                border-radius: 4px;
                color: #00d4ff;
                font-family: monospace;
                font-size: 11px;
                padding: 2px 12px;
            }
            QPushButton:hover {
                background: rgba(0,200,255,0.2);
                border-color: rgba(0,200,255,0.4);
            }
        """)
        self._edit_btn.clicked.connect(self._toggle_edit)
        hdr_row.addWidget(self._edit_btn)
        layout.addLayout(hdr_row)

        # user info
        self._user_card = self._make_card()
        self._name_field = _Field("Name", "--")
        self._user_card.add_widget(self._name_field)
        self._title_field = _Field("Title", "--")
        self._user_card.add_widget(self._title_field)
        layout.addWidget(self._user_card)

        # coding style
        self._coding_card = self._make_card()
        self._coding_card.add_header("💻 CODING")
        self._lang_field = _Field("Language", "python")
        self._coding_card.add_widget(self._lang_field)
        self._indent_field = _Field("Indent style", "spaces")
        self._coding_card.add_widget(self._indent_field)
        self._linelen_field = _Field("Line length", "88")
        self._coding_card.add_widget(self._linelen_field)
        layout.addWidget(self._coding_card)

        # writing style
        self._writing_card = self._make_card()
        self._writing_card.add_header("✒️ WRITING")
        self._tone_field = _Field("Tone", "technical")
        self._writing_card.add_widget(self._tone_field)
        self._citation_field = _Field("Citation format", "APA")
        self._writing_card.add_widget(self._citation_field)
        layout.addWidget(self._writing_card)

        # preferences
        self._pref_card = self._make_card()
        self._pref_card.add_header("⚙️ PREFERENCES")
        self._challenge_cb = QCheckBox("Challenge mode")
        self._challenge_cb.setStyleSheet("color: #c0d8f0; font-family: monospace; font-size: 11px;")
        self._pref_card.add_widget(self._challenge_cb)
        self._alerts_cb = QCheckBox("Proactive alerts")
        self._alerts_cb.setStyleSheet("color: #c0d8f0; font-family: monospace; font-size: 11px;")
        self._pref_card.add_widget(self._alerts_cb)
        layout.addWidget(self._pref_card)

        # study info (read-only)
        self._study_card = self._make_card()
        self._study_card.add_header("📚 STUDY")
        self._folder_lbl = QLabel("Folder: not set")
        self._folder_lbl.setStyleSheet("color: #c0d8f0; font-family: monospace; font-size: 11px;")
        self._study_card.add_widget(self._folder_lbl)
        self._online_lbl = QLabel("Online: disabled")
        self._online_lbl.setStyleSheet("color: #6b8caa; font-family: monospace; font-size: 11px;")
        self._study_card.add_widget(self._online_lbl)
        layout.addWidget(self._study_card)

        # projects (read-only)
        self._proj_card = self._make_card()
        self._proj_card.add_header("● PROJECTS")
        self._proj_list = QLabel("No projects yet")
        self._proj_list.setStyleSheet("color: #8aaac0; font-family: monospace; font-size: 11px;")
        self._proj_list.setWordWrap(True)
        self._proj_card.add_widget(self._proj_list)
        layout.addWidget(self._proj_card)

        # goals & skills (editable)
        row = QHBoxLayout()
        row.setSpacing(10)

        self._goals_card = self._make_card()
        self._goals_card.add_header("🎯 GOALS")
        self._goals_field = _Field("", "No goals set yet", is_long=True)
        self._goals_card.add_widget(self._goals_field)
        row.addWidget(self._goals_card)

        self._skills_card = self._make_card()
        self._skills_card.add_header("⚡ SKILLS")
        self._skills_field = _Field("", "No skills listed", is_long=True)
        self._skills_card.add_widget(self._skills_field)
        row.addWidget(self._skills_card)

        layout.addLayout(row)

        # save / cancel (hidden by default)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        self._save_btn = QPushButton("💾 Save")
        self._save_btn.setFixedHeight(28)
        self._save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,255,136,0.12);
                border: 1px solid rgba(0,255,136,0.3);
                border-radius: 4px;
                color: #00ff88;
                font-family: monospace;
                font-size: 11px;
                padding: 2px 16px;
            }
            QPushButton:hover { background: rgba(0,255,136,0.25); }
        """)
        self._save_btn.clicked.connect(self._save)
        self._save_btn.setVisible(False)
        btn_row.addWidget(self._save_btn)

        self._cancel_btn = QPushButton("✕ Cancel")
        self._cancel_btn.setFixedHeight(28)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,50,50,0.1);
                border: 1px solid rgba(255,50,50,0.2);
                border-radius: 4px;
                color: #ff6688;
                font-family: monospace;
                font-size: 11px;
                padding: 2px 16px;
            }
            QPushButton:hover { background: rgba(255,50,50,0.25); }
        """)
        self._cancel_btn.clicked.connect(self._cancel_edit)
        self._cancel_btn.setVisible(False)
        btn_row.addWidget(self._cancel_btn)

        layout.addLayout(btn_row)
        layout.addStretch()

    def _make_card(self):
        return _Card()

    def _toggle_edit(self):
        if self._editing:
            self._cancel_edit()
        else:
            self._enter_edit_mode()

    def _enter_edit_mode(self):
        self._editing = True
        self._edit_btn.setText("✕ Cancel edit")
        self._edit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,50,50,0.1);
                border: 1px solid rgba(255,50,50,0.2);
                border-radius: 4px;
                color: #ff6688;
                font-family: monospace;
                font-size: 11px;
                padding: 2px 12px;
            }
            QPushButton:hover { background: rgba(255,50,50,0.25); }
        """)
        self._save_btn.setVisible(True)
        self._cancel_btn.setVisible(True)

        for f in self._editable_fields():
            f.set_edit_mode(True)
        for cb in (self._challenge_cb, self._alerts_cb):
            cb.setEnabled(True)

    def _cancel_edit(self):
        self._editing = False
        self._edit_btn.setText("✎ Edit")
        self._edit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,200,255,0.1);
                border: 1px solid rgba(0,200,255,0.2);
                border-radius: 4px;
                color: #00d4ff;
                font-family: monospace;
                font-size: 11px;
                padding: 2px 12px;
            }
            QPushButton:hover { background: rgba(0,200,255,0.2); border-color: rgba(0,200,255,0.4); }
        """)
        self._save_btn.setVisible(False)
        self._cancel_btn.setVisible(False)

        for f in self._editable_fields():
            f.set_edit_mode(False)
        for cb in (self._challenge_cb, self._alerts_cb):
            cb.setEnabled(False)

        # restore from cache
        if self._profile_cache:
            self.set_profile(self._profile_cache)

    def _save(self):
        asyncio.ensure_future(self._async_save())

    async def _async_save(self):
        try:
            from pathlib import Path

            from friday.memory.user_profile import UserProfile

            cfg_path = Path("~/.config/friday/user_profile.json").expanduser()

            goals_text = self._goals_field.get_value().strip()
            skills_text = self._skills_field.get_value().strip()

            updates = {
                "name": self._name_field.get_value().strip() or "Architect",
                "title": self._title_field.get_value().strip() or "sir",
                "coding_style": {
                    "language_preference": self._lang_field.get_value().strip() or "python",
                    "indent_style": self._indent_field.get_value().strip() or "spaces",
                    "line_length": int(self._linelen_field.get_value().strip() or "88"),
                },
                "writing_style": {
                    "tone": self._tone_field.get_value().strip() or "technical",
                    "citation_format": self._citation_field.get_value().strip() or "APA",
                },
                "preferences": {
                    "challenge_mode": self._challenge_cb.isChecked(),
                    "proactive_alerts": self._alerts_cb.isChecked(),
                },
                "goals": [g.strip() for g in goals_text.split("\n") if g.strip()],
                "skills": [s.strip() for s in skills_text.split("\n") if s.strip()],
            }
            up = UserProfile()
            up.update_profile(updates)
            await up.save(str(cfg_path))

            self._profile_cache = up.get_profile()
            self.set_profile(self._profile_cache)
            self._cancel_edit()
        except Exception as e:
            logger.error("Profile save error: %s", e)

    def _editable_fields(self):
        return (
            self._name_field,
            self._title_field,
            self._lang_field,
            self._indent_field,
            self._linelen_field,
            self._tone_field,
            self._citation_field,
            self._goals_field,
            self._skills_field,
        )

    def set_profile(self, profile: dict):
        self._profile_cache = dict(profile)
        self._name_field.set_value(profile.get("name", "--"))
        self._title_field.set_value(profile.get("title", "--"))

        coding = profile.get("coding_style", {})
        self._lang_field.set_value(coding.get("language_preference", "--"))
        self._indent_field.set_value(coding.get("indent_style", "--"))
        self._linelen_field.set_value(coding.get("line_length", "--"))

        writing = profile.get("writing_style", {})
        self._tone_field.set_value(writing.get("tone", "--"))
        self._citation_field.set_value(writing.get("citation_format", "--"))

        pref = profile.get("preferences", {})
        self._challenge_cb.setChecked(pref.get("challenge_mode", False))
        self._alerts_cb.setChecked(pref.get("proactive_alerts", False))

        goals = profile.get("goals", [])
        self._goals_field.set_value("\n".join(goals) if goals else "No goals set yet")

        skills = profile.get("skills", [])
        self._skills_field.set_value("\n".join(skills) if skills else "No skills listed")

    def set_study(self, folder: str, online: bool):
        if folder:
            self._folder_lbl.setText(f"Folder: {folder}")
            self._folder_lbl.setStyleSheet("color: #c0d8f0; font-family: monospace; font-size: 11px;")
        else:
            self._folder_lbl.setText("Folder: not set")
            self._folder_lbl.setStyleSheet("color: #6b8caa; font-family: monospace; font-size: 11px;")
        status = "enabled" if online else "disabled"
        color = "#00ff88" if online else "#6b8caa"
        self._online_lbl.setText(f"Online: {status}")
        self._online_lbl.setStyleSheet(f"color: {color}; font-family: monospace; font-size: 11px;")

    def set_projects(self, projects: list):
        if not projects:
            self._proj_list.setText("No projects yet")
            return
        lines = []
        for p in projects[:8]:
            name = p.get("name", "?")
            desc = p.get("description", "")
            item = f"● {name}"
            if desc:
                item += f" — {desc[:40]}"
            lines.append(item)
        if len(projects) > 8:
            lines.append(f"... and {len(projects) - 8} more")
        self._proj_list.setText("\n".join(lines))


class _Card(QFrame):
    """Helper: card frame with header + widget layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            _Card {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(0,212,255,0.12);
                border-radius: 10px;
            }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 10, 14, 10)
        self._layout.setSpacing(4)

    def add_header(self, text):
        h = QLabel(text)
        h.setStyleSheet(
            "color: #00d4ff; font-family: monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        self._layout.addWidget(h)

    def add_widget(self, w):
        self._layout.addWidget(w)


class UpdatePanel(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._version = "?"
        self._status = "checking..."
        self._latest = None
        self._installing = False
        try:
            from friday import __version__

            self._version = __version__
        except ImportError:
            pass
        self.setFixedSize(200, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        self._check()

    def _update_style(self):
        color = "#ffaa00" if self._latest and self._latest != self._version else "#4a8a6a"
        status_text = self._get_status_text()
        self.setStyleSheet(f"""
            UpdatePanel {{
                background: rgba(0,0,0,0.55);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 6px;
            }}
            QWidget {{
                color: {color};
                font-family: monospace;
                font-size: 10px;
            }}
        """)
        self._status = status_text
        self.update()

    def _get_status_text(self):
        if self._installing:
            return "installing..."
        if self._latest is None:
            return "checking..."
        if self._latest != self._version:
            return f"v{self._latest} available — click to install"
        return "up to date"

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 140)))
        painter.drawRoundedRect(QRectF(self.rect()), 6, 6)

        color = QColor("#ffaa00") if (self._latest and self._latest != self._version) else QColor("#6aaa8a")
        f = QFont("monospace", 9)
        painter.setFont(f)
        painter.setPen(color)
        painter.drawText(
            QRectF(8, 2, self.width() - 12, 14),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"v{self._version}",
        )

        f2 = QFont("monospace", 8)
        painter.setFont(f2)
        status_color = QColor("#ffaa00") if (self._latest and self._latest != self._version) else QColor("#4a8a6a")
        painter.setPen(status_color)
        painter.drawText(
            QRectF(8, 15, self.width() - 12, 14),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._get_status_text(),
        )

    def mousePressEvent(self, event):  # noqa: N802
        if self._latest and self._latest != self._version and not self._installing:
            self._install()

    def _check(self):
        async def _do():
            try:
                import httpx

                r = await httpx.AsyncClient(timeout=5).get(
                    "https://api.github.com/repos/king/FRIDAY/releases/latest",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if r.status_code == 200:
                    self._latest = r.json().get("tag_name", "").lstrip("v")
            except Exception:
                pass
            self._update_style()

        try:
            asyncio.get_running_loop()
            asyncio.ensure_future(_do())
        except RuntimeError:
            pass

    def _install(self):
        self._installing = True
        self._update_style()

        async def _do():
            try:
                proc = await asyncio.create_subprocess_shell(
                    "git pull origin main",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            except Exception:
                pass
            os.execl(sys.executable, sys.executable, *sys.argv)

        asyncio.ensure_future(_do())


class SettingsDialog(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(440, 420)
        self.setStyleSheet("""
            QFrame {
                background: rgba(8,8,28,0.97);
                border: 1px solid rgba(0,200,255,0.25);
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        hdr = QLabel("⚙ SETTINGS")
        hdr.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 13px; font-weight: bold;")
        layout.addWidget(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: rgba(0,0,0,0.2); width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,200,255,0.3); border-radius: 3px; min-height: 20px;
            }
        """)
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        sl = QVBoxLayout(scroll_content)
        sl.setSpacing(8)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # provider cards
        self._provider_rows = {}
        try:
            from friday.router.provider_registry import ProviderRegistry

            providers = ProviderRegistry().list_providers()
        except Exception:
            providers = []

        for p in providers:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(0,212,255,0.10);
                    border-radius: 6px;
                }
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10, 6, 10, 6)
            cl.setSpacing(8)

            status_colors = {"online": "#00ff88", "offline": "#ff3355", "unknown": "#6b8caa"}
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {status_colors.get(p.status, '#6b8caa')}; font-size: 10px;")
            cl.addWidget(dot)

            name_lbl = QLabel(p.name)
            name_lbl.setStyleSheet("color: #e0e8ff; font-family: monospace; font-size: 12px; font-weight: bold;")
            cl.addWidget(name_lbl)

            key_status = "✓" if p.api_key else "—"
            ks = QLabel(f"key: {key_status}")
            ks.setStyleSheet("color: #6b8caa; font-family: monospace; font-size: 10px;")
            cl.addWidget(ks)

            cl.addStretch()

            cb = QCheckBox()
            cb.setChecked(p.enabled)
            cb.setStyleSheet("""
                QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; }
                QCheckBox::indicator:checked { background: rgba(0,200,255,0.4); border: 1px solid #00d4ff; }
                QCheckBox::indicator:unchecked { background: rgba(255,255,255,0.05); border: 1px solid #4a6a8a; }
            """)
            cb.stateChanged.connect(lambda checked, name=p: self._toggle_provider(name, checked))
            cl.addWidget(cb)

            sl.addWidget(card)
            self._provider_rows[p.name] = (dot, cb)

        # version & close
        sl.addStretch()

        try:
            from friday import __version__

            ver = __version__
        except ImportError:
            ver = "1.0.0"
        ver_lbl = QLabel(f"FRIDAY v{ver}")
        ver_lbl.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 10px;")
        layout.addWidget(ver_lbl)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(0,200,255,0.15);
                border-radius: 4px;
                color: #c0d8f0;
                font-family: monospace;
                font-size: 11px;
                padding: 4px 16px;
            }
            QPushButton:hover { background: rgba(0,200,255,0.12); }
        """)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

    def _toggle_provider(self, name, checked):
        asyncio.ensure_future(self._async_toggle_provider(name, checked))

    async def _async_toggle_provider(self, name, checked):
        try:
            from friday.router.provider_registry import ProviderRegistry

            await ProviderRegistry().set_enabled(name, bool(checked))
        except Exception:
            pass

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._refresh_status()

    def _refresh_status(self):
        asyncio.ensure_future(self._async_refresh_status())

    async def _async_refresh_status(self):
        try:
            from friday.router.provider_registry import ProviderRegistry

            await ProviderRegistry().check_all()
            providers = ProviderRegistry().list_providers()
            status_colors = {"online": "#00ff88", "offline": "#ff3355", "unknown": "#6b8caa"}
            for p in providers:
                if p.name in self._provider_rows:
                    dot, _ = self._provider_rows[p.name]
                    dot.setStyleSheet(f"color: {status_colors.get(p.status, '#6b8caa')}; font-size: 10px;")
        except Exception:
            pass
