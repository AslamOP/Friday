import math

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QFont, QFontDatabase,
)
from PyQt6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QSizePolicy, QGraphicsDropShadowEffect,
)


class HoloSphere(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0.0
        self._pulse = 0.0
        self._particles = []
        self._init_particles()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self.setMinimumSize(120, 120)

    def _init_particles(self):
        import random
        for _ in range(40):
            self._particles.append({
                'angle': random.uniform(0, 2 * math.pi),
                'speed': random.uniform(0.3, 1.8),
                'radius': random.uniform(0.2, 0.95),
                'size': random.uniform(1, 3),
                'alpha': random.uniform(0.2, 0.9),
            })

    def _tick(self):
        self._angle = (self._angle + 0.025) % (2 * math.pi)
        self._pulse = (self._pulse + 0.015) % (2 * math.pi)
        for p in self._particles:
            p['angle'] = (p['angle'] + p['speed'] * 0.015) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        if self.width() <= 0 or self.height() <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        radius = min(cx, cy) * 0.65

        # outer glow
        glow_r = radius * 2.2
        g = QRadialGradient(QPointF(cx, cy), glow_r)
        gi = 0.12 + 0.06 * math.sin(self._pulse)
        g.setColorAt(0, QColor(0, 180, 255, int(60 * gi * 2)))
        g.setColorAt(0.3, QColor(0, 100, 255, int(25 * gi * 2)))
        g.setColorAt(0.7, QColor(0, 30, 120, int(8 * gi * 2)))
        g.setColorAt(1, QColor(0, 0, 30, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(g))
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # core sphere
        cg = QRadialGradient(QPointF(cx, cy), radius)
        cg.setColorAt(0, QColor(180, 230, 255, 200))
        cg.setColorAt(0.25, QColor(0, 180, 255, 160))
        cg.setColorAt(0.5, QColor(0, 100, 220, 90))
        cg.setColorAt(0.75, QColor(0, 40, 140, 40))
        cg.setColorAt(1, QColor(0, 0, 60, 8))
        painter.setBrush(QBrush(cg))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # orbit rings
        pen_orb = QPen(QColor(0, 200, 255, 70), 1)
        painter.setPen(pen_orb)

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle * 180 / math.pi)
        painter.drawEllipse(QPointF(0, 0), radius * 1.05, radius * 0.25)
        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle * 180 / math.pi + 60)
        painter.drawEllipse(QPointF(0, 0), radius * 0.25, radius * 1.05)
        painter.restore()

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle * 180 / math.pi + 120)
        painter.drawEllipse(QPointF(0, 0), radius * 0.85, radius * 0.45)
        painter.restore()

        # particles
        for p in self._particles:
            px = cx + p['radius'] * radius * math.cos(p['angle'])
            py = cy + p['radius'] * radius * math.sin(p['angle']) * 0.6
            a = int(p['alpha'] * 200 * (0.6 + 0.4 * math.sin(self._pulse)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 220, 255, a)))
            painter.drawEllipse(QPointF(px, py), p['size'], p['size'])


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

    def paintEvent(self, event):
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

    def append_output(self, text: str, style: str = "normal"):
        colors = {
            "normal": "#c0d8f0", "system": "#00d4ff",
            "success": "#00ff88", "warning": "#ffaa00",
            "error": "#ff3355", "info": "#6b8caa",
        }
        prefixes = {
            "normal": "│ ", "system": "◈ ", "success": "✓ ",
            "warning": "⚠ ", "error": "✗ ", "info": "· ",
        }
        color = colors.get(style, colors["normal"])
        prefix = prefixes.get(style, "│ ")
        html = f'<span style="color:{color};">{prefix}{text}</span><br>'
        self.append(html)
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


class TitleBar(QWidget):
    profile_clicked = pyqtSignal()

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._parent:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._parent.move(self._parent.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        h = QLabel("AGENTS")
        h.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(h)
        layout.addSpacing(4)

        self._rows = {}
        for name in ["Analyzer", "Coder", "Planner", "Researcher", "Automator", "Tutor"]:
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
            layout.addLayout(row)
            self._rows[name] = (dot, st)

    def set_status(self, name: str, status: str):
        if name not in self._rows:
            return
        dot, st = self._rows[name]
        if status == "running":
            dot.setText("●"); dot.setStyleSheet("color: #00d4ff; font-size: 11px;")
            st.setText("active"); st.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 10px;")
        elif status == "done":
            dot.setText("✓"); dot.setStyleSheet("color: #00ff88; font-size: 11px;")
            st.setText("done"); st.setStyleSheet("color: #00ff88; font-family: monospace; font-size: 10px;")
        else:
            dot.setText("○"); dot.setStyleSheet("color: #4a6a8a; font-size: 11px;")
            st.setText("idle"); st.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 10px;")


class ProfilePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ProfilePanel {
                background: transparent;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        # header
        hdr = QLabel("◆ PROFILE")
        hdr.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(hdr)

        # user info
        self._user_card = QFrame()
        self._user_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(0,212,255,0.12);
                border-radius: 10px;
            }
        """)
        uc = QVBoxLayout(self._user_card)
        uc.setContentsMargins(14, 10, 14, 10)
        uc.setSpacing(3)
        self._name_lbl = QLabel("Name: --")
        self._name_lbl.setStyleSheet("color: #e0e8ff; font-family: monospace; font-size: 13px;")
        uc.addWidget(self._name_lbl)
        self._title_lbl = QLabel("Title: --")
        self._title_lbl.setStyleSheet("color: #8aaac0; font-family: monospace; font-size: 11px;")
        uc.addWidget(self._title_lbl)
        layout.addWidget(self._user_card)

        # study info
        self._study_card = QFrame()
        self._study_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(0,212,255,0.12);
                border-radius: 10px;
            }
        """)
        sc = QVBoxLayout(self._study_card)
        sc.setContentsMargins(14, 10, 14, 10)
        sc.setSpacing(3)
        sh = QLabel("📚 STUDY")
        sh.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        sc.addWidget(sh)
        self._folder_lbl = QLabel("Folder: not set")
        self._folder_lbl.setStyleSheet("color: #c0d8f0; font-family: monospace; font-size: 11px;")
        sc.addWidget(self._folder_lbl)
        self._online_lbl = QLabel("Online: disabled")
        self._online_lbl.setStyleSheet("color: #6b8caa; font-family: monospace; font-size: 11px;")
        sc.addWidget(self._online_lbl)
        layout.addWidget(self._study_card)

        # projects
        self._proj_card = QFrame()
        self._proj_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(0,212,255,0.12);
                border-radius: 10px;
            }
        """)
        pc = QVBoxLayout(self._proj_card)
        pc.setContentsMargins(14, 10, 14, 10)
        pc.setSpacing(3)
        ph = QLabel("● PROJECTS")
        ph.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        pc.addWidget(ph)
        self._proj_list = QLabel("No projects yet")
        self._proj_list.setStyleSheet("color: #8aaac0; font-family: monospace; font-size: 11px;")
        self._proj_list.setWordWrap(True)
        pc.addWidget(self._proj_list)
        layout.addWidget(self._proj_card)

        # goals & skills row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self._goals_card = QFrame()
        self._goals_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(0,212,255,0.12);
                border-radius: 10px;
            }
        """)
        gc = QVBoxLayout(self._goals_card)
        gc.setContentsMargins(14, 10, 14, 10)
        gc.setSpacing(3)
        ghl = QLabel("🎯 GOALS")
        ghl.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        gc.addWidget(ghl)
        self._goals_lbl = QLabel("None")
        self._goals_lbl.setStyleSheet("color: #8aaac0; font-family: monospace; font-size: 11px;")
        self._goals_lbl.setWordWrap(True)
        gc.addWidget(self._goals_lbl)
        bottom_row.addWidget(self._goals_card)

        self._skills_card = QFrame()
        self._skills_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(0,212,255,0.12);
                border-radius: 10px;
            }
        """)
        skc = QVBoxLayout(self._skills_card)
        skc.setContentsMargins(14, 10, 14, 10)
        skc.setSpacing(3)
        skh = QLabel("⚡ SKILLS")
        skh.setStyleSheet("color: #00d4ff; font-family: monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        skc.addWidget(skh)
        self._skills_lbl = QLabel("None")
        self._skills_lbl.setStyleSheet("color: #8aaac0; font-family: monospace; font-size: 11px;")
        self._skills_lbl.setWordWrap(True)
        skc.addWidget(self._skills_lbl)
        bottom_row.addWidget(self._skills_card)

        layout.addLayout(bottom_row)

        # hint
        hint = QLabel("Set your profile via the REPL or study agent commands.")
        hint.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 9px;")
        layout.addWidget(hint)

        layout.addStretch()

    def set_profile(self, profile: dict):
        name = profile.get("name", "--")
        title = profile.get("title", "--")
        self._name_lbl.setText(f"Name: {name}")
        self._title_lbl.setText(f"Title: {title}")

        pref = profile.get("preferences", {})
        goals = profile.get("goals", [])
        skills = profile.get("skills", [])

        if goals:
            self._goals_lbl.setText("\n".join(f"• {g}" for g in goals))
        else:
            self._goals_lbl.setText("None set")
        if skills:
            self._skills_lbl.setText("\n".join(f"• {s}" for s in skills))
        else:
            self._skills_lbl.setText("None set")

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
