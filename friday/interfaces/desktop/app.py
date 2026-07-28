import asyncio
import json
import logging
import subprocess
import sys
import threading

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QSizeGrip,
    QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from friday.agents.automation_engineer import AutomationEngineerAgent
from friday.agents.chat import ChatAgent
from friday.agents.gaming_assistant import GamingAssistantAgent
from friday.agents.knowledge_manager import KnowledgeManagerAgent
from friday.agents.mentor import MentorAgent
from friday.agents.planner import PlannerAgent
from friday.agents.research_scientist import ResearchScientistAgent
from friday.agents.software_engineer import SoftwareEngineerAgent
from friday.agents.study import StudyAgent
from friday.core.ipc import GUI_SOCK, UnixServer
from friday.core.orchestrator import get_orchestrator
from friday.interfaces.audio import SpeechToText

from .widgets import (
    AgentPanel, AnimatedBackground, CommandBar, CoreRings,
    Gauge, LogPanel, MetricBar, Panel, ProviderPanel, ResponseBox,
    StatusPill,
)

logger = logging.getLogger("friday.desktop")

_AGENT_ICONS = {
    "chat": "💬", "mentor": "🧠", "planner": "📋", "software_engineer": "⚙️",
    "research_scientist": "🔬", "knowledge_manager": "📚",
    "automation_engineer": "🤖", "study": "🎓", "gaming_assistant": "🎮",
}


class FridayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._stt = SpeechToText()
        self._voice_active = False
        self._voice_task = None
        self._pending_submit = ""

        self._setup_ui()
        self._resize_grip = QSizeGrip(self)
        self._position_grip()

        self.resize(1100, 720)
        self._center_on_screen()
        self._init_backend()

    # -------------------------------------------------------------------
    # UI setup
    # -------------------------------------------------------------------

    def _setup_ui(self):
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)

        self._bg = AnimatedBackground(self.centralWidget())
        self._bg.lower()

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # top bar
        layout.addWidget(self._build_top_bar())

        # main content grid
        content = QHBoxLayout()
        content.setContentsMargins(14, 8, 14, 6)
        content.setSpacing(12)

        content.addLayout(self._build_left_panel(), 2)
        content.addLayout(self._build_center(), 5)
        content.addLayout(self._build_right_panel(), 2)

        layout.addLayout(content, 1)

        # bottom bar
        self._cmd_bar = CommandBar()
        self._cmd_bar.submitted.connect(self._on_command)
        self._cmd_bar.voice_toggled.connect(self._on_voice_toggle)
        layout.addWidget(self._cmd_bar)

        layout.addSpacing(6)

    def _build_top_bar(self):
        bar = QWidget()
        bar.setFixedHeight(70)
        bar.setStyleSheet("background: rgba(0,26,51,0.4); border-bottom: 1px solid rgba(0,229,255,0.2);")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("FRIDAY")
        logo.setStyleSheet("color: #00e5ff; font-family: Rajdhani; font-size: 22px; font-weight: 700; letter-spacing: 4px; background: transparent;")
        layout.addWidget(logo)

        layout.addStretch()

        pills = QHBoxLayout()
        pills.setSpacing(8)

        self._online_pill = StatusPill("ONLINE", "#00ff88")
        pills.addWidget(self._online_pill)
        self._linked_pill = StatusPill("LINKED", "#00e5ff")
        pills.addWidget(self._linked_pill)
        self._zen_pill = StatusPill("ZEN", "#ff6b35")
        pills.addWidget(self._zen_pill)

        layout.addLayout(pills)
        layout.addSpacing(20)

        self._clock_lbl = QLabel("00:00:00")
        self._clock_lbl.setStyleSheet("color: #c0d8ff; font-family: monospace; font-size: 14px; background: transparent; letter-spacing: 2px;")
        layout.addWidget(self._clock_lbl)

        # clock timer
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # drag support
        self._top_bar_drag = bar
        bar.mousePressEvent = self._drag_press
        bar.mouseMoveEvent = self._drag_move
        bar.mouseReleaseEvent = self._drag_release
        self._dragging = False
        self._drag_pos = None

        return bar

    def _build_left_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # gauges
        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(4)
        self._cpu_gauge = Gauge("CPU")
        gauge_row.addWidget(self._cpu_gauge)
        self._ram_gauge = Gauge("RAM")
        gauge_row.addWidget(self._ram_gauge)
        self._gpu_gauge = Gauge("GPU")
        gauge_row.addWidget(self._gpu_gauge)
        layout.addLayout(gauge_row)

        # metrics
        metrics = Panel("SYSTEM TELEMETRY")
        self._gpu_metric = MetricBar("GPU LOAD")
        metrics.add_widget(self._gpu_metric)
        self._disk_metric = MetricBar("DISK USAGE")
        metrics.add_widget(self._disk_metric)
        self._net_metric = MetricBar("NETWORK")
        metrics.add_widget(self._net_metric)
        self._temp_metric = MetricBar("CORE TEMP")
        metrics.add_widget(self._temp_metric)
        layout.addWidget(metrics, 1)

        # logs
        logs_panel = Panel("SYSLOG")
        self._logs = LogPanel()
        logs_panel.add_widget(self._logs)
        layout.addWidget(logs_panel, 2)

        return layout

    def _build_center(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self._core = CoreRings()
        layout.addWidget(self._core, 0, Qt.AlignmentFlag.AlignCenter)

        self._response = ResponseBox()
        self._response.setMinimumHeight(120)
        self._response.setMaximumWidth(600)
        layout.addWidget(self._response, 0, Qt.AlignmentFlag.AlignCenter)

        return layout

    def _build_right_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # agents
        agent_panel = Panel("ACTIVE AGENTS")
        self._agent_panel = AgentPanel()
        agent_panel.add_widget(self._agent_panel)
        layout.addWidget(agent_panel, 1)

        # separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(0,229,255,0.1);")
        layout.addWidget(sep)

        # providers
        prov_panel = Panel("PROVIDERS")
        self._prov_panel = ProviderPanel()
        self._prov_panel.add_provider("ZEN")
        self._prov_panel.add_provider("OPENROUTER")
        self._prov_panel.add_provider("OLLAMA")
        self._prov_panel.add_provider("OPENAI")
        self._prov_panel.add_provider("ANTHROPIC")
        self._prov_panel.add_provider("GOOGLE")
        prov_panel.add_widget(self._prov_panel)
        layout.addWidget(prov_panel, 0)

        # version
        self._ver_lbl = QLabel("v--")
        self._ver_lbl.setStyleSheet("color: #4a6a8a; font-family: monospace; font-size: 9px; background: transparent;")
        layout.addWidget(self._ver_lbl, 0, Qt.AlignmentFlag.AlignRight)

        layout.addStretch()
        return layout

    def _position_grip(self):
        self._resize_grip.move(self.width() - self._resize_grip.width() - 4,
                                self.height() - self._resize_grip.height() - 4)

    def resizeEvent(self, event):
        self._position_grip()
        if hasattr(self, "_bg"):
            self._bg.setGeometry(self.rect())
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "_bg"):
            self._bg.setGeometry(self.rect())
            self._bg.raise_()
            self._bg.lower()

    # -------------------------------------------------------------------
    # Drag support
    # -------------------------------------------------------------------

    def _drag_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def _drag_move(self, event):
        if self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def _drag_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            event.accept()

    # -------------------------------------------------------------------
    # Backend init
    # -------------------------------------------------------------------

    def _init_backend(self):
        self._log("FRIDAY AI OS INITIALIZING")
        try:
            from friday import __version__
            ver = __version__
        except ImportError:
            ver = "1.0.0"
        self._ver_lbl.setText(f"v{ver}")

        self._log("NEURAL INTERFACE CALIBRATED")
        self._start_monitor()
        self._setup_ipc()
        self._setup_tray()
        self._setup_shortcuts()
        asyncio.ensure_future(self._init_orchestrator())

        self._response.set_text("SYSTEM ONLINE. STANDING BY FOR INPUT...")

    async def _init_orchestrator(self):
        try:
            o = get_orchestrator()
            for cls, name in [
                (ChatAgent, "chat"),
                (MentorAgent, "mentor"),
                (PlannerAgent, "planner"),
                (SoftwareEngineerAgent, "software_engineer"),
                (ResearchScientistAgent, "research_scientist"),
                (AutomationEngineerAgent, "automation_engineer"),
                (KnowledgeManagerAgent, "knowledge_manager"),
                (StudyAgent, "study"),
                (GamingAssistantAgent, "gaming_assistant"),
            ]:
                agent = cls()
                o.register_agent(agent)
                icon = _AGENT_ICONS.get(name, "?")
                self._agent_panel.add_agent(name, icon)

            await o.initialize()
            o.subscribe_event("agent:status", self._on_agent_status)
            self._log("HEURISTIC ENGINES AT 100%")
            self._response.set_text("ALL SYSTEMS ONLINE. FRIDAY READY.")
        except Exception as e:
            logger.warning("Orchestrator init failed: %s", e)
            self._log("BACKEND UNAVAILABLE")

    def _on_agent_status(self, data: dict):
        agent = data.get("agent", "")
        status = data.get("status", "")
        if agent and status:
            self._agent_panel.set_status(agent, status)

    # -------------------------------------------------------------------
    # IPC
    # -------------------------------------------------------------------

    def _setup_ipc(self):
        async def handler(reader, writer):
            try:
                data = await reader.readline()
                cmd = json.loads(data.decode())
                if cmd.get("type") == "focus":
                    self.activateWindow()
                    self.raise_()
                    self.showNormal()
                writer.write(b'{"ok": true}\n')
                await writer.drain()
            except Exception:
                pass
            finally:
                writer.close()

        asyncio.ensure_future(UnixServer(GUI_SOCK).start(handler))

    # -------------------------------------------------------------------
    # Tray
    # -------------------------------------------------------------------

    def _setup_tray(self):
        try:
            from .tray import FridayTray
            t = threading.Thread(target=FridayTray().run, daemon=True)
            t.start()
            self._tray_running = True
        except Exception as e:
            logger.debug("Tray not available: %s", e)
            self._tray_running = False

    # -------------------------------------------------------------------
    # Shortcuts
    # -------------------------------------------------------------------

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._toggle_dashboard)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.showMinimized)

    def _toggle_dashboard(self):
        pass

    # -------------------------------------------------------------------
    # Monitor
    # -------------------------------------------------------------------

    def _start_monitor(self):
        try:
            from friday.tools.system_monitor import SystemMonitor
            self._monitor = SystemMonitor()
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._poll_stats)
            self._timer.start(2500)
            self._poll_stats()
        except Exception:
            self._monitor = None

    def _poll_stats(self):
        asyncio.ensure_future(self._do_poll())

    async def _do_poll(self):
        if not self._monitor:
            return
        try:
            result = await self._monitor.collect()
            if result.success and result.metrics:
                m = result.metrics
                self._cpu_gauge.set_value(m.cpu_percent)
                self._ram_gauge.set_value(m.memory_percent)
                if m.gpu_available:
                    self._gpu_gauge.set_value(m.gpu_util or 0)
                else:
                    self._gpu_gauge.set_value(0)
                self._gpu_metric.set_value(m.gpu_util or 0, m.gpu_name.split()[-1] if m.gpu_name else "")
                self._disk_metric.set_value(m.disk_percent, f"{m.disk_used_gb:.0f}/{m.disk_total_gb:.0f}GB")
                self._net_metric.set_value(min(m.network_sent_mb + m.network_recv_mb, 100))
                if m.cpu_temp:
                    self._temp_metric.set_value(m.cpu_temp / 100 * 100, f"{m.cpu_temp}°C")
        except Exception:
            pass

    # -------------------------------------------------------------------
    # Command handling
    # -------------------------------------------------------------------

    def _on_command(self, text):
        self._log(f"> {text}")
        self._response.set_text(f"PROCESSING: {text.upper()}...")

        t = text.lower().strip()
        if t.startswith("open "):
            self._launch_app(t[5:].strip())
        elif t in ("help", "?"):
            self._show_help()
        elif t == "clear":
            pass
        elif t == "status":
            self._response.set_text("ALL SYSTEMS ONLINE. FRIDAY OPERATIONAL.")
        else:
            asyncio.ensure_future(self._process_command(text))

    async def _process_command(self, text):
        try:
            o = get_orchestrator()
            result = await o.process(text)
            if result.success:
                self._response.set_text(result.output[:600])
                self._agent_panel.set_status(result.agent, "active")
            else:
                self._response.set_text(f"ERROR: {result.output[:300]}")
        except Exception as e:
            self._response.set_text(f"ERROR: {e}")

    def _launch_app(self, name):
        try:
            subprocess.Popen([name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._response.set_text(f"LAUNCHED: {name}")
        except FileNotFoundError:
            self._response.set_text(f"APP '{name}' NOT FOUND")

    def _show_help(self):
        lines = [
            "AVAILABLE COMMANDS:",
            "  open <app>   Launch an application",
            "  help / ?     Show this help",
            "  clear        Clear terminal",
            "  status       Show system status",
            "  <question>   Ask FRIDAY anything",
        ]
        self._response.set_text("\n".join(lines))

    # -------------------------------------------------------------------
    # Voice
    # -------------------------------------------------------------------

    def _on_voice_toggle(self, active):
        self._voice_active = active
        if active:
            if not self._stt.available:
                self._log("VOICE UNAVAILABLE: INSTALL PYAUDIO + SPEECHRECOGNITION")
                self._cmd_bar._voice_btn.setChecked(False)
                return
            self._log("VOICE INPUT ACTIVATED")
            self._voice_task = asyncio.ensure_future(self._voice_loop())
        else:
            self._log("VOICE INPUT DEACTIVATED")
            if self._voice_task:
                self._voice_task.cancel()
                self._voice_task = None

    async def _voice_loop(self):
        while self._voice_active:
            try:
                text = await self._stt.listen(timeout=1.5, phrase_time=4.0)
                if text and text.strip():
                    self._log(f"[VOICE] {text}")
                    self._cmd_bar.set_text(text)
                    self._on_command(text)
            except asyncio.CancelledError:
                break
            except Exception:
                break

    # -------------------------------------------------------------------
    # Clock
    # -------------------------------------------------------------------

    def _update_clock(self):
        from datetime import datetime
        self._clock_lbl.setText(datetime.now().strftime("%H:%M:%S"))

    # -------------------------------------------------------------------
    # Log helper
    # -------------------------------------------------------------------

    def _log(self, msg: str):
        self._logs.append(msg)

    # -------------------------------------------------------------------
    # Close
    # -------------------------------------------------------------------

    def closeEvent(self, event):
        self._voice_active = False
        if self._voice_task:
            self._voice_task.cancel()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._save_and_close())
        except RuntimeError:
            pass
        if getattr(self, "_tray_running", False):
            event.ignore()
            self.hide()
        else:
            event.accept()
            QApplication.quit()

    async def _save_and_close(self):
        try:
            o = get_orchestrator()
            await o.persistence.save_all()
        except Exception:
            pass

    # -------------------------------------------------------------------
    # Center
    # -------------------------------------------------------------------

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())


def run_gui():
    app = QApplication(sys.argv)
    import qasync

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    f = QFont("JetBrains Mono", 10)
    f.setStyleHint(QFont.StyleHint.Monospace)
    app.setFont(f)
    window = FridayWindow()
    window.show()

    loop.run_forever()


if __name__ == "__main__":
    run_gui()
