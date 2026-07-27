import asyncio
import logging
import subprocess
import sys

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QBrush, QLinearGradient, QFont, QRegion, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy, QGraphicsDropShadowEffect, QStackedWidget,
)

from friday.tools.system_monitor import SystemMonitor  # noqa: direct import to avoid bs4 dep
from friday.interfaces.audio import SpeechToText
from .widgets import HoloSphere, StatPanel, CommandBar, OutputArea, TitleBar, AgentPanel, ProfilePanel

logger = logging.getLogger("friday.desktop")


class FridayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QToolTip {
                background: rgba(10,10,30,0.9);
                border: 1px solid rgba(0,200,255,0.3);
                border-radius: 4px;
                color: #c0d8f0;
                padding: 4px 8px;
                font-family: monospace;
                font-size: 11px;
            }
        """)

        self._monitor = SystemMonitor()
        self._stt = SpeechToText()
        self._voice_active = False
        self._voice_task = None

        self._setup_ui()
        self._start_monitor()

        self.resize(960, 680)
        self._center_on_screen()
        self._update_mask()

        self._output.append_output("FRIDAY AI OS v" + self._get_version(), "system")
        self._output.append_output("System initialized. All systems online.", "success")
        self._output.append_output("Type a command or click the mic for voice.", "info")

        self._load_profile_data()

    def _get_version(self):
        try:
            from friday import __version__
            return __version__
        except ImportError:
            return "1.0.0"

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

    def _update_mask(self):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 14, 14)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def resizeEvent(self, event):
        self._update_mask()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 14, 14)
        g = QLinearGradient(QPointF(0, 0), QPointF(0, self.height()))
        g.setColorAt(0, QColor(12, 12, 30))
        g.setColorAt(0.5, QColor(8, 8, 22))
        g.setColorAt(1, QColor(5, 5, 18))
        painter.fillPath(path, QBrush(g))
        pen = QPen(QColor(0, 180, 255, 28))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)

    def _setup_ui(self):
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._title_bar = TitleBar(self)
        self._title_bar.profile_clicked.connect(self._toggle_profile)
        main_layout.addWidget(self._title_bar)

        # stacked widget: page 0 = dashboard, page 1 = profile
        self._stack = QStackedWidget()
        self._stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # -- dashboard page --
        dash = QWidget()
        dash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dl = QHBoxLayout(dash)
        dl.setContentsMargins(14, 8, 14, 6)
        dl.setSpacing(12)

        lc = QVBoxLayout()
        lc.setSpacing(8)
        self._cpu_panel = StatPanel("CPU")
        self._cpu_panel.setMinimumWidth(105)
        lc.addWidget(self._cpu_panel)
        self._gpu_panel = StatPanel("GPU")
        self._gpu_panel.setMinimumWidth(105)
        lc.addWidget(self._gpu_panel)
        lc.addStretch()
        dl.addLayout(lc)

        cc = QVBoxLayout()
        cc.setSpacing(8)
        self._holo = HoloSphere()
        self._holo.setMinimumSize(160, 130)
        cc.addWidget(self._holo, 1)
        self._agent_panel = AgentPanel()
        cc.addWidget(self._agent_panel)
        dl.addLayout(cc, 1)

        rc = QVBoxLayout()
        rc.setSpacing(8)
        self._ram_panel = StatPanel("RAM")
        self._ram_panel.setMinimumWidth(105)
        rc.addWidget(self._ram_panel)
        self._disk_panel = StatPanel("DISK")
        self._disk_panel.setMinimumWidth(105)
        rc.addWidget(self._disk_panel)
        rc.addStretch()
        dl.addLayout(rc)

        self._stack.addWidget(dash)  # page 0

        # -- profile page --
        self._profile_panel = ProfilePanel()
        self._stack.addWidget(self._profile_panel)  # page 1

        main_layout.addWidget(self._stack, 1)

        self._cmd_bar = CommandBar()
        self._cmd_bar.submitted.connect(self._on_command)
        self._cmd_bar.voice_toggled.connect(self._on_voice_toggle)
        main_layout.addWidget(self._cmd_bar)

        self._output = OutputArea()
        self._output.setMaximumHeight(160)
        self._output.setMinimumHeight(80)
        main_layout.addWidget(self._output)

        main_layout.addSpacing(6)

    def _start_monitor(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_stats)
        self._timer.start(2200)
        self._poll_stats()

    def _poll_stats(self):
        asyncio.ensure_future(self._do_poll())

    async def _do_poll(self):
        try:
            result = await self._monitor.collect()
            if result.success and result.metrics:
                m = result.metrics
                self._cpu_panel.set_value(m.cpu_percent,
                    f"{m.cpu_cores}c" + (f" {m.cpu_temp}°C" if m.cpu_temp else ""))
                self._ram_panel.set_value(m.memory_percent,
                    f"{m.memory_used_gb:.1f}/{m.memory_total_gb:.1f}")
                self._disk_panel.set_value(m.disk_percent,
                    f"{m.disk_used_gb:.1f}/{m.disk_total_gb:.1f}")
                if m.gpu_available:
                    short = m.gpu_name.split()[-1] if m.gpu_name else "GPU"
                    self._gpu_panel.set_value(m.gpu_util or 0, f"{short} {m.gpu_util:.0f}%")
                else:
                    self._gpu_panel.set_value(0, "not detected")
        except Exception as e:
            logger.debug("Stats poll error: %s", e)

    def _on_command(self, text):
        self._output.append_output(f"> {text}", "normal")
        t = text.lower().strip()

        if t.startswith("open "):
            self._launch_app(t[5:].strip())
        elif t in ("help", "?"):
            self._show_help()
        elif t == "clear":
            self._output.clear()
        elif t == "status":
            self._output.append_output("All systems online. FRIDAY operational.", "success")
        else:
            asyncio.ensure_future(self._process_command(text))

    async def _process_command(self, text):
        try:
            from friday.core.orchestrator import get_orchestrator
            o = get_orchestrator()
            result = await o.process(text)
            if result.success:
                self._output.append_output(result.output[:600], "success")
                self._agent_panel.set_status(result.agent, "done")
            else:
                self._output.append_output(result.output[:600], "error")
        except Exception:
            self._output.append_output(f"Run daemon for full command processing.", "info")

    def _launch_app(self, name):
        try:
            subprocess.Popen([name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._output.append_output(f"Launched: {name}", "success")
        except FileNotFoundError:
            self._output.append_output(f"App '{name}' not found", "error")
        except Exception as e:
            self._output.append_output(f"Launch failed: {e}", "error")

    def _show_help(self):
        for line in [
            "Available commands:",
            "  open <app>   Launch an application",
            "  help / ?     Show this help",
            "  clear        Clear terminal",
            "  status       Show system status",
            "  <question>   Ask FRIDAY (requires daemon running)",
        ]:
            self._output.append_output(line, "info")

    def _on_voice_toggle(self, active):
        self._voice_active = active
        if active:
            self._output.append_output("Voice input activated. Speak your command.", "system")
            self._voice_task = asyncio.ensure_future(self._voice_loop())
        else:
            self._output.append_output("Voice input deactivated.", "info")
            if self._voice_task:
                self._voice_task.cancel()
                self._voice_task = None

    async def _voice_loop(self):
        while self._voice_active:
            try:
                text = await self._stt.listen(timeout=1.5, phrase_time=4.0)
                if text and text.strip():
                    self._output.append_output(f"[voice] {text}", "system")
                    self._cmd_bar.set_text(text)
                    self._on_command(text)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug("Voice loop error: %s", e)
                await asyncio.sleep(0.5)

    def closeEvent(self, event):
        self._voice_active = False
        if self._voice_task:
            self._voice_task.cancel()
        event.accept()

    def _toggle_profile(self):
        if self._stack.currentIndex() == 0:
            self._stack.setCurrentIndex(1)
            self._title_bar._profile_btn.setStyleSheet("""
                QPushButton { background: rgba(0,200,255,0.15); border: none; color: #00d4ff; font-size: 13px; border-radius: 3px; }
                QPushButton:hover { background: rgba(0,200,255,0.25); color: #00d4ff; }
            """)
            self._load_profile_data()
        else:
            self._stack.setCurrentIndex(0)
            self._title_bar._profile_btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; color: #6b8caa; font-size: 13px; }
                QPushButton:hover { background: rgba(0,200,255,0.12); color: #00d4ff; }
            """)

    def _load_profile_data(self):
        try:
            from friday.memory.user_profile import UserProfile
            profile = UserProfile().get_profile()
            self._profile_panel.set_profile(profile)
        except Exception:
            self._profile_panel.set_profile({})

        try:
            from friday.memory.project_memory import ProjectMemory
            projects = ProjectMemory().list_projects()
            self._profile_panel.set_projects(projects)
        except Exception:
            self._profile_panel.set_projects([])

        try:
            from pathlib import Path
            import json
            cfg_path = Path("~/.config/friday/study_agent.json").expanduser()
            if cfg_path.exists():
                cfg = json.loads(cfg_path.read_text())
                self._profile_panel.set_study(
                    cfg.get("folder", ""),
                    cfg.get("online", False),
                )
            else:
                self._profile_panel.set_study("", False)
        except Exception:
            self._profile_panel.set_study("", False)


def run_gui():
    app = QApplication(sys.argv)
    f = QFont("monospace")
    f.setStyleHint(QFont.StyleHint.Monospace)
    app.setFont(f)
    window = FridayWindow()
    window.show()

    import qasync
    with qasync.QApplication(app):
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    run_gui()
