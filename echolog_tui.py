#!/usr/bin/env python3
"""
Echolog TUI - Terminal User Interface for Echolog Audio Recorder

A Textual-based interactive terminal interface for managing recording sessions.
"""

from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, Input
from textual.binding import Binding
from textual.screen import ModalScreen

if TYPE_CHECKING:
    from echolog import EchologRecorder


class SessionNameModal(ModalScreen[str]):
    """Modal dialog to prompt for session name before recording."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    DEFAULT_CSS = """
    SessionNameModal {
        align: center middle;
    }
    
    SessionNameModal > Container {
        width: 60;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }
    
    SessionNameModal > Container > Label {
        margin-bottom: 1;
    }
    
    SessionNameModal > Container > Input {
        width: 100%;
    }
    
    SessionNameModal > Container > Static {
        margin-top: 1;
        color: $text-muted;
        text-align: center;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Enter session name:")
            yield Input(placeholder="my_session", id="session-name-input")
            yield Static("Press Enter to start, Escape to cancel")
    
    def on_mount(self) -> None:
        """Focus the input when modal opens."""
        self.query_one(Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input - start recording."""
        session_name = event.value.strip()
        if session_name:
            self.dismiss(session_name)
        else:
            # Shake or notify invalid - just refocus for now
            self.query_one(Input).focus()
    
    def action_cancel(self) -> None:
        """Handle Escape key - cancel recording."""
        self.dismiss("")


class StatusPanel(Static):
    """Display current recording status."""
    
    DEFAULT_CSS = """
    StatusPanel {
        height: 3;
        padding: 0 1;
    }
    
    StatusPanel .status-idle {
        color: $text-muted;
    }
    
    StatusPanel .status-recording {
        color: #00ff00;
        text-style: bold;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.status = "Idle"
        self.session_id: str | None = None
    
    def compose(self) -> ComposeResult:
        yield Label(self._render_status(), id="status-label", classes="status-idle")
    
    def _render_status(self) -> str:
        indicator = "○" if self.status == "Idle" else "●"
        status_text = f"Status: {indicator} {self.status.upper()}"
        if self.session_id:
            status_text += f"          Session: {self.session_id}"
        return status_text
    
    def update_status(self, status: str, session_id: str | None = None) -> None:
        """Update the status display.
        
        Args:
            status: Either 'Idle' or 'Recording'
            session_id: Current session ID (shown when recording)
        """
        self.status = status
        self.session_id = session_id
        label = self.query_one("#status-label", Label)
        label.update(self._render_status())
        # Update CSS class for coloring
        label.remove_class("status-idle", "status-recording")
        if status == "Recording":
            label.add_class("status-recording")
        else:
            label.add_class("status-idle")


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


class SegmentPanel(Static):
    """Display segment progress with progress bar."""
    
    DEFAULT_CSS = """
    SegmentPanel {
        border: solid green;
        padding: 0 1;
        width: 1fr;
        height: 3;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.current_chunk = 0
        self.segment_elapsed = 0
        self.segment_duration = 300
    
    def compose(self) -> ComposeResult:
        yield Label(self._render_progress(), id="segment-label")
    
    def _render_progress(self) -> str:
        """Render the segment progress display."""
        if self.current_chunk == 0:
            return "Chunk -/∞   [░░░░░░░░░░░░] --:--"
        
        # Calculate progress percentage
        progress = self.segment_elapsed / self.segment_duration if self.segment_duration > 0 else 0
        progress = min(1.0, max(0.0, progress))
        
        # Create progress bar (12 chars wide)
        bar_width = 12
        filled = int(progress * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Format remaining time as MM:SS
        remaining = self.segment_duration - self.segment_elapsed
        mins = remaining // 60
        secs = remaining % 60
        time_str = f"{mins}:{secs:02d}"
        
        return f"Chunk {self.current_chunk}/∞   [{bar}] {time_str}"
    
    def update_progress(self, current_chunk: int, segment_elapsed: int, segment_duration: int) -> None:
        """Update the segment progress display.
        
        Args:
            current_chunk: Current chunk number (1-indexed)
            segment_elapsed: Seconds elapsed in current segment
            segment_duration: Total segment duration in seconds
        """
        self.current_chunk = current_chunk
        self.segment_elapsed = segment_elapsed
        self.segment_duration = segment_duration
        label = self.query_one("#segment-label", Label)
        label.update(self._render_progress())


class ChunkPanel(Static):
    """Display list of recorded chunks with scrolling support."""
    
    DEFAULT_CSS = """
    ChunkPanel {
        border: solid green;
        padding: 0 1;
        height: 8;
        overflow-y: auto;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[dict] = []
        self._visible_lines = 6
    
    def compose(self) -> ComposeResult:
        yield Label("No chunks yet", id="chunks-label")
    
    def update_chunks(self, chunks: list[dict]) -> None:
        """Update the chunk list display.
        
        Args:
            chunks: List of chunk dicts with 'filename', 'size_bytes', 'finalized' keys.
        """
        self._chunks = chunks
        self._update_display()
    
    def _update_display(self) -> None:
        if not self._chunks:
            text = "No chunks yet"
        else:
            lines = []
            # Show last N chunks to fit in visible area, auto-scroll to latest
            visible_chunks = self._chunks[-self._visible_lines:]
            for chunk in visible_chunks:
                filename = chunk.get('filename', 'unknown')
                size_bytes = chunk.get('size_bytes', 0)
                finalized = chunk.get('finalized', False)
                
                # Determine if this is the last chunk (in-progress if not finalized)
                is_last = chunk == self._chunks[-1]
                in_progress = is_last and not finalized
                
                marker = "◐" if in_progress else "✓"
                
                # Format size: show MB for finalized, "(rec...)" for in-progress
                if in_progress:
                    size_str = "(rec...)"
                else:
                    size_mb = size_bytes / (1024 * 1024)
                    size_str = f"{size_mb:.1f} MB"
                
                lines.append(f"{marker} {filename}  {size_str}")
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
            yield SegmentPanel()
        
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
    
    def __init__(self, recorder: "EchologRecorder | None" = None) -> None:
        super().__init__()
        self.recorder = recorder
        self._last_status: bool | None = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Dashboard()
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted."""
        log_panel = self.query_one(LogPanel)
        log_panel.add_entry("TUI started - Press ? for help")
        # Initial status sync
        self._sync_recorder_status()
        # Sync info panel with recorder config
        self._sync_info_panel()
        # Start periodic status polling (every 0.5 seconds)
        self.set_interval(0.5, self._sync_recorder_status)
        # Start timer update (every 1 second for smooth HH:MM:SS display)
        self.set_interval(1.0, self._update_timer)
    
    def _sync_recorder_status(self) -> None:
        """Sync the status panel with the recorder state."""
        if self.recorder is None:
            return
        
        status = self.recorder.get_status()
        is_recording = status.get("recording", False)
        session_id = status.get("session_id")
        
        # Only update if status changed to avoid redundant updates
        if is_recording != self._last_status:
            self._last_status = is_recording
            status_panel = self.query_one(StatusPanel)
            if is_recording:
                status_panel.update_status("Recording", session_id)
            else:
                status_panel.update_status("Idle", None)
                # Reset timer to 00:00:00 when recording stops
                timer_panel = self.query_one(TimerPanel)
                timer_panel.update_time(0)
                # Reset segment progress when recording stops
                segment_panel = self.query_one(SegmentPanel)
                segment_panel.update_progress(0, 0, 300)
                # Clear chunk list when recording stops
                chunk_panel = self.query_one(ChunkPanel)
                chunk_panel.update_chunks([])
    
    def _sync_info_panel(self) -> None:
        """Sync the info panel with recorder config."""
        if self.recorder is None:
            return
        
        status = self.recorder.get_status()
        info_panel = self.query_one(InfoPanel)
        
        # Format segment duration as human-readable
        segment_secs = status.get("segment_duration_seconds", 300)
        if segment_secs >= 60:
            segment_str = f"{segment_secs // 60} min"
        else:
            segment_str = f"{segment_secs} sec"
        
        info_panel.update_info(
            device=status.get("device_name", "Not selected"),
            format=status.get("format", "OGG/Opus"),
            sample_rate=f"{status.get('sample_rate', '16000')} Hz",
            segment_duration=segment_str
        )
    
    def _update_timer(self) -> None:
        """Update the timer display with elapsed recording time."""
        if self.recorder is None:
            return
        
        status = self.recorder.get_status()
        elapsed_seconds = status.get("elapsed_seconds", 0)
        timer_panel = self.query_one(TimerPanel)
        timer_panel.update_time(elapsed_seconds)
        
        # Update segment progress
        segment_panel = self.query_one(SegmentPanel)
        segment_panel.update_progress(
            current_chunk=status.get("current_chunk_number", 0),
            segment_elapsed=status.get("segment_elapsed_seconds", 0),
            segment_duration=status.get("segment_duration_seconds", 300)
        )
        
        # Update chunk list
        self._sync_chunks(status)
    
    def _sync_chunks(self, status: dict | None = None) -> None:
        """Sync the chunk panel with recorder chunk data."""
        if self.recorder is None:
            return
        
        if status is None:
            status = self.recorder.get_status()
        
        chunks = status.get("chunks", [])
        chunk_panel = self.query_one(ChunkPanel)
        chunk_panel.update_chunks(chunks)
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_start_recording(self) -> None:
        """Open session name prompt and start recording."""
        if self.recorder is None:
            log_panel = self.query_one(LogPanel)
            log_panel.add_entry("ERROR: No recorder available")
            return
        
        # Check if already recording
        if self.recorder.is_recording():
            log_panel = self.query_one(LogPanel)
            log_panel.add_entry("Already recording - stop first")
            return
        
        # Show modal to get session name
        self.push_screen(SessionNameModal(), self._on_session_name_submitted)
    
    def _on_session_name_submitted(self, session_name: str) -> None:
        """Callback when session name is submitted from modal."""
        log_panel = self.query_one(LogPanel)
        
        if not session_name:
            log_panel.add_entry("Recording cancelled")
            return
        
        if self.recorder is None:
            log_panel.add_entry("ERROR: No recorder available")
            return
        
        log_panel.add_entry(f"Starting recording: {session_name}")
        
        try:
            success = self.recorder.start_recording(session_name)
            if success:
                log_panel.add_entry(f"Recording started: {session_name}")
                # Force immediate status sync
                self._last_status = None
                self._sync_recorder_status()
            else:
                log_panel.add_entry(f"ERROR: Failed to start recording")
        except Exception as e:
            log_panel.add_entry(f"ERROR: {e}")
    
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


def run_tui(recorder: "EchologRecorder | None" = None) -> None:
    """Entry point to run the TUI application.
    
    Args:
        recorder: Optional EchologRecorder instance to integrate with.
                  If provided, TUI will sync status from the recorder.
    """
    app = EchologTUI(recorder=recorder)
    app.run()


if __name__ == "__main__":
    run_tui()
