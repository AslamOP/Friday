"""Verify desktop UI modules can be imported without a display."""


def test_widgets_import():
    from friday.interfaces.desktop.widgets import (
        HoloSphere, CircularProgress, StatPanel, CommandBar,
        OutputArea, TitleBar, AgentPanel, ProfilePanel, SettingsDialog,
    )
    assert HoloSphere is not None


def test_app_import():
    from friday.interfaces.desktop.app import FridayWindow, run_gui
    assert FridayWindow is not None


def test_tray_import():
    from friday.interfaces.desktop.tray import FridayTray
    assert FridayTray is not None


def test_notifications_import():
    from friday.interfaces.desktop.notifications import Notifier
    assert Notifier is not None


def test_desktop_init():
    from friday.interfaces.desktop import run_gui, FridayTray, Notifier
    assert run_gui is not None


def test_output_area_render_markdown():
    from friday.interfaces.desktop.widgets import OutputArea
    html = OutputArea._render_markdown("**bold** and `code`")
    assert "<b>" in html
    assert "<code" in html


def test_output_area_render_markdown_codeblock():
    from friday.interfaces.desktop.widgets import OutputArea
    html = OutputArea._render_markdown("```python\nprint('hi')\n```")
    assert "<pre" in html


def test_output_area_render_markdown_link():
    from friday.interfaces.desktop.widgets import OutputArea
    html = OutputArea._render_markdown("[click](https://example.com)")
    assert "<a href=" in html


def test_output_area_render_markdown_heading():
    from friday.interfaces.desktop.widgets import OutputArea
    html = OutputArea._render_markdown("# Title\n## Sub\n### H3")
    assert "font-size:15px" in html
    assert "font-size:14px" in html
    assert "font-size:13px" in html



