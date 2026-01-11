#!/usr/bin/env python3
"""
Echolog TUI - Terminal User Interface for Echolog Audio Recorder

A Textual-based interactive terminal interface for managing recording sessions.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.binding import Binding


class StatusPanel(Static):
    """Display current recording status."""
    
    def __init__(self) -> None:
        super().__init__()
        self.status = "Idle"
        self.session_id = None
    
    def compose(self) -> ComposeResult:
        yield Label(self._render_status(), id="status-label")
    
    def _render_status(self) -> str:
        indicator = "○" if self.status == "Idle" else "●"
        status_text = f"Status: {indicator} {self.status.upper()}"
        if self.session_id:
            status_text += f"          Session: {self.session_id}"
        return status_text
    
    def update_status(self, status: str, session_id: str = None) -> None:
        self.status = status
        self.session_id = session_id
        label = self.query_one("#status-label", Label)
        label.update(self._render_status())


class TimerPanel(Static):
    """Display elapsed recording time."""
    
    DEFAULT_CSS = """
    TimerPanel {
        border: solid green;
        padding: 0 1;
        width: 20;
        height: 3;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Label("00:00:00", id="timer-label")
    
    def update_time(self, seconds: int) -> None:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        label = self.query_one("#timer-label", Label)
        label.update(time_str)


class ChunkPanel(Static):
    """Display list of recorded chunks."""
    
    DEFAULT_CSS = """
    ChunkPanel {
        border: solid green;
        padding: 0 1;
        height: 8;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []
    
    def compose(self) -> ComposeResult:
        yield Label("No chunks yet", id="chunks-label")
    
    def add_chunk(self, chunk_name: str, size_mb: float = 0.0, in_progress: bool = False) -> None:
        self.chunks.append((chunk_name, size_mb, in_progress))
        self._update_display()
    
    def _update_display(self) -> None:
        if not self.chunks:
            text = "No chunks yet"
        else:
            lines = []
            for name, size, in_progress in self.chunks[-6:]:  # Show last 6
                marker = "◐" if in_progress else "✓"
                size_str = f"{size:.1f} MB" if size > 0 else "(rec...)"
                lines.append(f"{marker} {name}  {size_str}")
            text = "\n".join(lines)
        
        label = self.query_one("#chunks-label", Label)
        label.update(text)


class InfoPanel(Static):
    """Display device and configuration info."""
    
    DEFAULT_CSS = """
    InfoPanel {
        border: solid green;
        padding: 0 1;
        height: 8;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.device = "Not selected"
        self.format = "OGG/Opus"
        self.sample_rate = "16000 Hz"
        self.segment_duration = "5 min"
        self.disk_free = "-- GB free"
    
    def compose(self) -> ComposeResult:
        yield Label(self._render_info(), id="info-label")
    
    def _render_info(self) -> str:
        return (
            f"Device: {self.device}\n"
            f"Format: {self.format}\n"
            f"Rate: {self.sample_rate}\n"
            f"Segment: {self.segment_duration}\n"
            f"Disk: {self.disk_free}"
        )
    
    def update_info(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        label = self.query_one("#info-label", Label)
        label.update(self._render_info())


class LogPanel(Static):
    """Display session log entries."""
    
    DEFAULT_CSS = """
    LogPanel {
        border: solid green;
        padding: 0 1;
        height: 6;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.log_entries: list[str] = []
        self.max_entries = 5
    
    def compose(self) -> ComposeResult:
        yield Label("No log entries", id="log-label")
    
    def add_entry(self, entry: str) -> None:
        self.log_entries.append(entry)
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
        self._update_display()
    
    def _update_display(self) -> None:
        if not self.log_entries:
            text = "No log entries"
        else:
            text = "\n".join(self.log_entries)
        label = self.query_one("#log-label", Label)
        label.update(text)


class Dashboard(Container):
    """Main dashboard view with all panels."""
    
    DEFAULT_CSS = """
    Dashboard {
        layout: vertical;
        padding: 1;
    }
    
    #status-row {
        height: 3;
        margin-bottom: 1;
    }
    
    #timer-row {
        height: 5;
        margin-bottom: 1;
    }
    
    #main-row {
        height: auto;
        margin-bottom: 1;
    }
    
    #chunks-col {
        width: 1fr;
        margin-right: 1;
    }
    
    #info-col {
        width: 1fr;
    }
    
    #log-row {
        height: auto;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(id="status-row"):
            yield StatusPanel()
        
        with Horizontal(id="timer-row"):
            yield TimerPanel()
        
        with Horizontal(id="main-row"):
            with Vertical(id="chunks-col"):
                yield Static("─ Chunks ─", classes="panel-title")
                yield ChunkPanel()
            with Vertical(id="info-col"):
                yield Static("─ Info ─", classes="panel-title")
                yield InfoPanel()
        
        with Container(id="log-row"):
            yield Static("─ Log ─", classes="panel-title")
            yield LogPanel()


class EchologTUI(App):
    """Main TUI application for Echolog."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        dock: top;
    }
    
    Footer {
        dock: bottom;
    }
    
    .panel-title {
        text-style: bold;
        color: $text-muted;
        height: 1;
    }
    
    StatusPanel {
        height: 3;
        padding: 0 1;
    }
    """
    
    TITLE = "ECHOLOG"
    SUB_TITLE = "Audio Recorder"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "start_recording", "Record"),
        Binding("s", "stop_recording", "Stop"),
        Binding("d", "select_device", "Devices"),
        Binding("question_mark", "show_help", "Help"),
    ]
    
    def __init__(self) -> None:
        super().__init__()
        self.recorder = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Dashboard()
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted."""
        log_panel = self.query_one(LogPanel)
        log_panel.add_entry("TUI started - Press ? for help")
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_start_recording(self) -> None:
        """Start recording (placeholder)."""
        log_panel = self.query_one(LogPanel)
        log_panel.add_entry("Recording start requested (not yet implemented)")
    
    def action_stop_recording(self) -> None:
        """Stop recording (placeholder)."""
        log_panel = self.query_one(LogPanel)
        log_panel.add_entry("Recording stop requested (not yet implemented)")
    
    def action_select_device(self) -> None:
        """Open device selection (placeholder)."""
        log_panel = self.query_one(LogPanel)
        log_panel.add_entry("Device selection requested (not yet implemented)")
    
    def action_show_help(self) -> None:
        """Show help overlay (placeholder)."""
        log_panel = self.query_one(LogPanel)
        log_panel.add_entry("Help: [R]ecord [S]top [D]evices [Q]uit")


def run_tui() -> None:
    """Entry point to run the TUI application."""
    app = EchologTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
