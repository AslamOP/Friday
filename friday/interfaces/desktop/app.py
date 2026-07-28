from __future__ import annotations
import asyncio
import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
import qasync

from friday import __version__
from friday.core.orchestrator import Orchestrator
from friday.interfaces.desktop.widgets import (
    AnimatedBackground, AgentPanel, CommandBar, HelpDialog,
    LogPanel, ResponseBox, StatusBar,
)

logger = logging.getLogger("friday.desktop")


class FridayWindow(QMainWindow):
    def __init__(self, orchestrator: Orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        self.setWindowTitle(f"FRIDAY v{__version__}")
        self.setGeometry(100, 100, 1100, 720)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
                border: 1px solid rgba(0, 229, 255, 0.3);
                border-radius: 8px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._bg = AnimatedBackground(self)
        self._bg.lower()

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(8)

        header = QLabel(f"FRIDY  v{__version__}")
        header.setStyleSheet("""
            color: #00e5ff;
            font-family: Rajdhani;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 3px;
            background: transparent;
        """)
        cl.addWidget(header)

        mid = QWidget()
        mid.setStyleSheet("background: transparent;")
        mid_layout = QVBoxLayout(mid)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(8)

        self._agent_panel = AgentPanel()
        mid_layout.addWidget(self._agent_panel)

        self._response = ResponseBox()
        mid_layout.addWidget(self._response, 1)

        cl.addWidget(mid, 1)

        self._log = LogPanel()
        self._log.setMaximumHeight(80)
        cl.addWidget(self._log)

        self._status = StatusBar()
        cl.addWidget(self._status)

        self._cmd = CommandBar()
        self._cmd.submitted.connect(self._on_submit)
        cl.addWidget(self._cmd)

        layout.addWidget(content)

        self._log_message("System online. Standing by for input, sir.")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self._toggle_help)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._close_overlay)

    def _toggle_help(self):
        if not hasattr(self, "_help_dialog") or self._help_dialog is None:
            self._help_dialog = HelpDialog(self)
        d = self._help_dialog
        d.move(self.x() + (self.width() - d.width()) // 2,
               self.y() + (self.height() - d.height()) // 2)
        d.show()
        d.raise_()

    def _close_overlay(self):
        if hasattr(self, "_help_dialog") and self._help_dialog and self._help_dialog.isVisible():
            self._help_dialog.hide()
        else:
            self.showMinimized()

    def _log_message(self, msg: str):
        self._log.add_message(msg)

    @qasync.asyncSlot()
    async def _on_submit(self, text: str):
        self._response.set_text("Processing...")
        await self._process(text)

    async def _process(self, text: str):
        try:
            self._log_message(f"> {text}")
            response = await self.orchestrator.process(text)
            self._response.set_text(response)
            self._log_message(f"FRIDAY: {response[:80]}...")
        except Exception as e:
            logger.exception("Process error")
            self._response.set_text(f"[red]Error: {e}[/red]")
            self._log_message(f"Error: {e}")

    def closeEvent(self, event):
        event.accept()


def run_gui(orchestrator: Orchestrator):
    app = QApplication(sys.argv)
    font = QFont("Rajdhani", 10)
    app.setFont(font)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    win = FridayWindow(orchestrator)
    win.show()
    with loop:
        loop.run_forever()
