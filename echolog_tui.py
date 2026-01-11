#!/usr/bin/env python3
"""
Echolog TUI - Terminal User Interface for Echolog Audio Recorder

A Textual-based interactive terminal interface for managing recording sessions.
"""

from typing import TYPE_CHECKING
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, Input
from textual.binding import Binding
from textual.screen import ModalScreen

if TYPE_CHECKING:
    from echolog import EchologRecorder


class HelpModal(ModalScreen[None]):
    """Modal overlay displaying keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "dismiss_help", "Close"),
        Binding("question_mark", "dismiss_help", "Close"),
    ]

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }

    HelpModal > Container {
        width: 50;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }

    HelpModal > Container > Label#help-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    HelpModal > Container > Static#help-content {
        margin-bottom: 1;
    }

    HelpModal > Container > Static#help-footer {
        color: $text-muted;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Keyboard Shortcuts", id="help-title")
            yield Static(
                "  [R]  Start recording\n"
                "  [S]  Stop recording\n"
                "  [D]  Select audio device\n"
                "  [E]  Edit session name (display)\n"
                "  [?]  Show this help\n"
                "  [Q]  Quit application",
                id="help-content"
            )
            yield Static("Press any key to close", id="help-footer")

    def action_dismiss_help(self) -> None:
        """Dismiss the help overlay."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Any key dismisses the help overlay."""
        self.dismiss(None)


class DeviceSelectionScreen(ModalScreen[str]):
    """Screen for selecting an audio device from a list."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "move_up", "Up"),
        Binding("down", "move_down", "Down"),
        Binding("enter", "select_device", "Select"),
    ]

    DEFAULT_CSS = """
    DeviceSelectionScreen {
        align: center middle;
    }

    DeviceSelectionScreen > Container {
        width: 70;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }

    DeviceSelectionScreen > Container > Label#device-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    DeviceSelectionScreen > Container > Container#device-list {
        height: auto;
        max-height: 15;
        overflow-y: auto;
    }

    DeviceSelectionScreen > Container > Container#device-list > Label {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    DeviceSelectionScreen > Container > Container#device-list > Label.device-selected {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    DeviceSelectionScreen > Container > Container#device-list > Label.device-current {
        color: #00ff00;
    }

    DeviceSelectionScreen > Container > Static#device-footer {
        margin-top: 1;
        color: $text-muted;
        text-align: center;
    }
    """

    def __init__(self, devices: list[dict], current_device: str = "") -> None:
        super().__init__()
        self._devices = devices
        self._current_device = current_device
        self._selected_index = 0
        # Try to select current device initially
        for i, dev in enumerate(devices):
            if dev.get('name') == current_device:
                self._selected_index = i
                break

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Select Audio Device", id="device-title")
            with Container(id="device-list"):
                for i, device in enumerate(self._devices):
                    name = device.get('name', 'Unknown')
                    status = device.get('status', '')
                    status_str = f" [{status}]" if status else ""
                    is_current = name == self._current_device
                    marker = "● " if is_current else "  "
                    label = Label(f"{marker}{name}{status_str}", id=f"device-{i}")
                    if is_current:
                        label.add_class("device-current")
                    if i == self._selected_index:
                        label.add_class("device-selected")
                    yield label
            yield Static("↑/↓ Navigate  Enter: Select  Esc: Cancel", id="device-footer")

    def _update_selection(self) -> None:
        """Update visual selection."""
        for i in range(len(self._devices)):
            label = self.query_one(f"#device-{i}", Label)
            if i == self._selected_index:
                label.add_class("device-selected")
            else:
                label.remove_class("device-selected")

    def action_move_up(self) -> None:
        """Move selection up."""
        if self._selected_index > 0:
            self._selected_index -= 1
            self._update_selection()

    def action_move_down(self) -> None:
        """Move selection down."""
        if self._selected_index < len(self._devices) - 1:
            self._selected_index += 1
            self._update_selection()

    def action_select_device(self) -> None:
        """Select the currently highlighted device."""
        if self._devices:
            device = self._devices[self._selected_index]
            self.dismiss(device.get('name', ''))
        else:
            self.dismiss('')

    def action_cancel(self) -> None:
        """Cancel device selection."""
        self.dismiss('')


class QuitConfirmModal(ModalScreen[bool]):
    """Modal dialog to confirm quit while recording."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
    ]

    DEFAULT_CSS = """
    QuitConfirmModal {
        align: center middle;
    }

    QuitConfirmModal > Container {
        width: 50;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }

    QuitConfirmModal > Container > Label#quit-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    QuitConfirmModal > Container > Static#quit-message {
        text-align: center;
        margin-bottom: 1;
    }

    QuitConfirmModal > Container > Static#quit-footer {
        color: $text-muted;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Recording Active", id="quit-title")
            yield Static(
                "A recording is in progress.\n"
                "Do you want to stop recording and quit?",
                id="quit-message"
            )
            yield Static("[Y]es to stop and quit  [N]o to cancel", id="quit-footer")

    def action_confirm(self) -> None:
        """Confirm quit - stop recording and exit."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel quit - return to dashboard."""
        self.dismiss(False)


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
    
    def __init__(self, default_value: str = "", title: str = "Enter session name:") -> None:
        super().__init__()
        self._default_value = default_value
        self._title = title

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self._title)
            yield Input(value=self._default_value, placeholder="my_session", id="session-name-input")
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
        self.session_label: str | None = None
    
    def compose(self) -> ComposeResult:
        yield Label(self._render_status(), id="status-label", classes="status-idle")
    
    def _render_status(self) -> str:
        indicator = "○" if self.status == "Idle" else "●"
        status_text = f"Status: {indicator} {self.status.upper()}"
        if self.session_label:
            status_text += f"          Session: {self.session_label}"
        return status_text
    
    def update_status(self, status: str, session_label: str | None = None) -> None:
        """Update the status display.
        
        Args:
            status: Either 'Idle' or 'Recording'
            session_label: Current session label (shown when recording)
        """
        self.status = status
        self.session_label = session_label
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
        border: solid $primary;
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
        border: solid $primary;
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
        border: solid $primary;
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
        border: solid $primary;
        padding: 0 1;
        height: auto;
        min-height: 7;
    }

    InfoPanel .disk-warning {
        color: #ff6600;
        text-style: bold;
    }

    InfoPanel .time-warning {
        color: #ffaa00;
        text-style: bold;
    }
    """

    LOW_DISK_THRESHOLD_BYTES = 1024 * 1024 * 1024  # 1 GB
    LOW_TIME_THRESHOLD_SECONDS = 5 * 60  # 5 minutes

    def __init__(self) -> None:
        super().__init__()
        self.device = "Not selected"
        self.format = "OGG/Opus"
        self.sample_rate = "16000 Hz"
        self.segment_duration = "5 min"
        self.disk_free = "-- GB free"
        self.disk_free_bytes = 0
        self.time_limit = ""  # Empty string means no limit
        self.time_limit_remaining = ""
    
    def compose(self) -> ComposeResult:
        yield Label(self._render_info(), id="info-label")
    
    def _render_info(self) -> str:
        lines = [
            f"Device: {self.device}",
            f"Format: {self.format}",
            f"Rate: {self.sample_rate}",
            f"Segment: {self.segment_duration}",
            f"Disk: {self.disk_free}",
        ]
        # Only show time limit line if a limit is configured
        if self.time_limit:
            if self.time_limit_remaining:
                lines.append(f"Limit: {self.time_limit} ({self.time_limit_remaining} left)")
            else:
                lines.append(f"Limit: {self.time_limit}")
        return "\n".join(lines)
    
    def update_info(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        label = self.query_one("#info-label", Label)
        label.update(self._render_info())
        
        # Apply warning class if disk space is low
        if self.disk_free_bytes > 0 and self.disk_free_bytes < self.LOW_DISK_THRESHOLD_BYTES:
            label.add_class("disk-warning")
        else:
            label.remove_class("disk-warning")


class VUMeterPanel(Static):
    """Display audio level meter (VU meter) during recording."""

    DEFAULT_CSS = """
    VUMeterPanel {
        border: solid $primary;
        padding: 0 1;
        height: 3;
    }

    VUMeterPanel .vu-disabled {
        color: $text-muted;
    }

    VUMeterPanel .vu-low {
        color: #00ff00;
    }

    VUMeterPanel .vu-medium {
        color: #ffff00;
    }

    VUMeterPanel .vu-high {
        color: #ff6600;
    }

    VUMeterPanel .vu-peak {
        color: #ff0000;
        text-style: bold;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._level_db: float = -60.0
        self._enabled: bool = False

    def compose(self) -> ComposeResult:
        yield Label(self._render_meter(), id="vu-label")

    def _render_meter(self) -> str:
        """Render the VU meter bar with dB value."""
        if not self._enabled:
            return "VU: [────────────────────] -- dB"

        # Map dB to bar position: -60 dB = 0%, 0 dB = 100%
        # Use 20 characters for the bar
        bar_width = 20
        normalized = (self._level_db + 60.0) / 60.0  # 0.0 to 1.0
        normalized = max(0.0, min(1.0, normalized))
        filled = int(normalized * bar_width)

        # Build the bar with color zones
        # Green: -60 to -20 dB, Yellow: -20 to -10 dB, Orange: -10 to -3 dB, Red: -3 to 0 dB
        bar_chars = []
        for i in range(bar_width):
            if i < filled:
                pos_db = -60.0 + (i / bar_width) * 60.0
                if pos_db < -20:
                    bar_chars.append("█")  # Green zone
                elif pos_db < -10:
                    bar_chars.append("█")  # Yellow zone
                elif pos_db < -3:
                    bar_chars.append("█")  # Orange zone
                else:
                    bar_chars.append("█")  # Red zone (peak)
            else:
                bar_chars.append("─")

        bar = "".join(bar_chars)

        # Format dB value
        if self._level_db <= -60.0:
            db_str = "-∞ dB"
        else:
            db_str = f"{self._level_db:.0f} dB"

        return f"VU: [{bar}] {db_str}"

    def update_level(self, level_db: float, enabled: bool = True) -> None:
        """Update the VU meter display.

        Args:
            level_db: Audio level in dB (-60 to 0).
            enabled: Whether the meter is active (recording in progress).
        """
        self._level_db = level_db
        self._enabled = enabled
        label = self.query_one("#vu-label", Label)
        label.update(self._render_meter())

        # Update CSS class for coloring based on level
        label.remove_class("vu-disabled", "vu-low", "vu-medium", "vu-high", "vu-peak")
        if not enabled:
            label.add_class("vu-disabled")
        elif self._level_db >= -3:
            label.add_class("vu-peak")
        elif self._level_db >= -10:
            label.add_class("vu-high")
        elif self._level_db >= -20:
            label.add_class("vu-medium")
        else:
            label.add_class("vu-low")


class LogPanel(Static):
    """Display session log entries with color-coded levels."""
    
    DEFAULT_CSS = """
    LogPanel {
        border: solid $primary;
        padding: 0 1;
        height: 6;
    }
    
    LogPanel .log-error {
        color: #ff4444;
        text-style: bold;
    }
    
    LogPanel .log-warning {
        color: #ffaa00;
    }
    
    LogPanel .log-info {
        color: $text;
    }
    
    LogPanel .log-debug {
        color: $text-muted;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.log_entries: list[dict[str, str]] = []
        self._session_log_entries: list[dict[str, str]] = []
        self.max_entries = 5
    
    def compose(self) -> ComposeResult:
        yield Label("No log entries", id="log-label")
    
    def add_entry(self, entry: str, level: str = "INFO") -> None:
        """Add a local TUI message to the log panel.
        
        Args:
            entry: The message text.
            level: Log level (DEBUG, INFO, WARNING, ERROR).
        """
        self.log_entries.append({"message": entry, "level": level.upper()})
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
        self._update_display()
    
    def update_session_log(self, entries: list[dict[str, str]]) -> None:
        """Update with session log entries from recorder.

        Args:
            entries: List of dicts with 'timestamp', 'level', 'message' keys.
        """
        self._session_log_entries = entries
        self._update_display()
    
    def _format_entry(self, entry: dict[str, str]) -> str:
        """Format a log entry for display with level prefix."""
        level = entry.get("level", "INFO").upper()
        message = entry.get("message", "")
        timestamp = entry.get("timestamp", "")
        
        # Format timestamp: extract HH:MM:SS from ISO format
        if timestamp and "T" in timestamp:
            time_part = timestamp.split("T")[1].replace("Z", "")
            prefix = f"{time_part} {level}"
        else:
            prefix = level
        
        return f"{prefix}  {message}"
    
    def _update_display(self) -> None:
        # Combine session log entries with local TUI entries
        # Session log entries take priority; local entries shown if no session
        all_entries: list[dict[str, str]] = []

        if self._session_log_entries:
            all_entries = self._session_log_entries[-self.max_entries:]

        # Add local entries that aren't duplicates
        for entry in self.log_entries:
            all_entries.append(entry)

        # Keep only the most recent entries
        all_entries = all_entries[-self.max_entries:]

        if not all_entries:
            text = "No log entries"
        else:
            lines: list[str] = []
            for entry in all_entries:
                line = self._format_entry(entry)
                level = entry.get("level", "INFO").upper()
                # Apply Rich markup for coloring
                if level == "ERROR":
                    line = f"[#ff4444 bold]{line}[/]"
                elif level == "WARNING":
                    line = f"[#ffaa00]{line}[/]"
                elif level == "DEBUG":
                    line = f"[#888888]{line}[/]"
                lines.append(line)
            text = "\n".join(lines)

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

    #vu-row {
        height: 3;
        margin-bottom: 1;
    }
    """

    def __init__(self, no_meter: bool = False) -> None:
        super().__init__()
        self._no_meter = no_meter

    def compose(self) -> ComposeResult:
        with Container(id="status-row"):
            yield StatusPanel()

        with Horizontal(id="timer-row"):
            yield TimerPanel()
            yield SegmentPanel()

        if not self._no_meter:
            with Container(id="vu-row"):
                yield VUMeterPanel()

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
        Binding("r", "start_recording", "[R]ecord", priority=True),
        Binding("R", "start_recording", None, priority=True),
        Binding("s", "stop_recording", "[S]top", priority=True),
        Binding("S", "stop_recording", None, priority=True),
        Binding("d", "select_device", "[D]evices", priority=True),
        Binding("D", "select_device", None, priority=True),
        Binding("e", "edit_session_label", "[E]dit name", priority=True),
        Binding("E", "edit_session_label", None, priority=True),
        Binding("question_mark", "show_help", "[?]Help", priority=True),
        Binding("q", "quit", "[Q]uit", priority=True),
        Binding("Q", "quit", None, priority=True),
    ]
    
    def __init__(self, recorder: "EchologRecorder | None" = None, no_meter: bool = False) -> None:
        super().__init__()
        self.recorder = recorder
        self._last_status: bool | None = None
        self._no_meter = no_meter
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Dashboard(no_meter=self._no_meter)
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
        session_label = (
            status.get("session_label")
            or status.get("session_name")
            or status.get("session_id")
        )
        
        # Only update if status changed to avoid redundant updates
        if is_recording != self._last_status:
            self._last_status = is_recording
            status_panel = self.query_one(StatusPanel)
            if is_recording:
                status_panel.update_status("Recording", session_label)
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
                # Reset VU meter when recording stops (if meter is enabled)
                if not self._no_meter:
                    vu_panel = self.query_one(VUMeterPanel)
                    vu_panel.update_level(-60.0, enabled=False)

    def _sync_info_panel(self, status: dict | None = None) -> None:
        """Sync the info panel with recorder config.

        Args:
            status: Optional pre-fetched status dict. If None, fetches from recorder.
        """
        if self.recorder is None:
            return

        if status is None:
            status = self.recorder.get_status()
        info_panel = self.query_one(InfoPanel)

        # Format segment duration as human-readable
        segment_secs = status.get("segment_duration_seconds", 300)
        if segment_secs >= 60:
            segment_str = f"{segment_secs // 60} min"
        else:
            segment_str = f"{segment_secs} sec"

        # Format disk space as human-readable
        disk_free_bytes = status.get("disk_free_bytes", 0)
        if disk_free_bytes >= 1024 * 1024 * 1024:
            disk_str = f"{disk_free_bytes / (1024 * 1024 * 1024):.1f} GB free"
        elif disk_free_bytes >= 1024 * 1024:
            disk_str = f"{disk_free_bytes / (1024 * 1024):.0f} MB free"
        else:
            disk_str = "-- GB free"

        # Format time limit as human-readable (e.g., "2h", "30m")
        time_limit_secs = status.get("time_limit_seconds", 0)
        time_limit_str = ""
        if time_limit_secs > 0:
            if time_limit_secs >= 3600:
                hours = time_limit_secs // 3600
                time_limit_str = f"{hours}h"
            elif time_limit_secs >= 60:
                mins = time_limit_secs // 60
                time_limit_str = f"{mins}m"
            else:
                time_limit_str = f"{time_limit_secs}s"

        # Format time limit remaining as human-readable (e.g., "1h 30m left")
        time_limit_remaining_secs = status.get("time_limit_remaining_seconds", 0)
        time_limit_remaining_str = ""
        if time_limit_secs > 0 and status.get("recording", False):
            if time_limit_remaining_secs >= 3600:
                hours = time_limit_remaining_secs // 3600
                mins = (time_limit_remaining_secs % 3600) // 60
                if mins > 0:
                    time_limit_remaining_str = f"{hours}h {mins}m"
                else:
                    time_limit_remaining_str = f"{hours}h"
            elif time_limit_remaining_secs >= 60:
                mins = time_limit_remaining_secs // 60
                time_limit_remaining_str = f"{mins}m"
            else:
                time_limit_remaining_str = f"{time_limit_remaining_secs}s"

        info_panel.update_info(
            device=status.get("device_name", "Not selected"),
            format=status.get("format", "OGG/Opus"),
            sample_rate=f"{status.get('sample_rate', '16000')} Hz",
            segment_duration=segment_str,
            disk_free=disk_str,
            disk_free_bytes=disk_free_bytes,
            time_limit=time_limit_str,
            time_limit_remaining=time_limit_remaining_str
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
        
        # Update disk space (reuse status to avoid extra call)
        self._sync_info_panel(status)
        
        # Update session log entries
        self._sync_log_panel(status)

        # Update VU meter
        self._sync_vu_meter(status)

    def _sync_vu_meter(self, status: dict | None = None) -> None:
        """Sync the VU meter panel with audio level from recorder."""
        if self._no_meter:
            return

        if self.recorder is None:
            return

        if status is None:
            status = self.recorder.get_status()

        is_recording = status.get("recording", False)
        audio_level_db = status.get("audio_level_db", -60.0)

        vu_panel = self.query_one(VUMeterPanel)
        vu_panel.update_level(audio_level_db, enabled=is_recording)

    def _sync_log_panel(self, status: dict | None = None) -> None:
        """Sync the log panel with session log entries from recorder."""
        if self.recorder is None:
            return
        
        if status is None:
            status = self.recorder.get_status()
        
        log_entries = status.get("log_entries", [])
        log_panel = self.query_one(LogPanel)
        log_panel.update_session_log(log_entries)
    
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
        # Check if recording is active - show confirmation dialog
        if self.recorder is not None and self.recorder.is_recording():
            self.push_screen(QuitConfirmModal(), self._on_quit_confirmed)
        else:
            self.exit()

    def _on_quit_confirmed(self, confirmed: bool) -> None:
        """Callback when quit confirmation dialog is dismissed."""
        if not confirmed:
            # User cancelled - return to dashboard
            log_panel = self.query_one(LogPanel)
            log_panel.add_entry("Quit cancelled")
            return

        # User confirmed - stop recording then exit
        log_panel = self.query_one(LogPanel)

        if self.recorder is not None and self.recorder.is_recording():
            session_id = self.recorder.get_status().get("session_id", "unknown")
            log_panel.add_entry(f"Stopping recording before quit: {session_id}")

            try:
                success = self.recorder.stop_recording()
                if success:
                    log_panel.add_entry(f"Recording stopped: {session_id}")
                else:
                    log_panel.add_entry("WARNING: Failed to stop recording cleanly")
            except Exception as e:
                log_panel.add_entry(f"WARNING: Error stopping recording: {e}")

        # Exit the application
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
        self.push_screen(SessionNameModal(default_value=self._default_session_name()), self._on_session_name_submitted)

    def _default_session_name(self) -> str:
        """Generate a default session name for the start-recording prompt."""
        return datetime.now().strftime("rec_%Y%m%d_%H%M%S")
    
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
        """Stop the current recording."""
        log_panel = self.query_one(LogPanel)
        
        if self.recorder is None:
            log_panel.add_entry("ERROR: No recorder available")
            return
        
        # Check if recording is active
        if not self.recorder.is_recording():
            log_panel.add_entry("No active recording to stop")
            return
        
        session_id = self.recorder.get_status().get("session_id", "unknown")
        log_panel.add_entry(f"Stopping recording: {session_id}")
        
        try:
            success = self.recorder.stop_recording()
            if success:
                log_panel.add_entry(f"Recording stopped: {session_id}")
                # Force immediate status sync
                self._last_status = None
                self._sync_recorder_status()
            else:
                log_panel.add_entry("ERROR: Failed to stop recording")
        except Exception as e:
            log_panel.add_entry(f"ERROR: {e}")
    
    def action_select_device(self) -> None:
        """Open device selection screen."""
        log_panel = self.query_one(LogPanel)

        if self.recorder is None:
            log_panel.add_entry("ERROR: No recorder available")
            return

        # Get available devices
        devices = self.recorder.detect_audio_devices()
        if not devices:
            log_panel.add_entry("No audio devices found")
            return

        # Get current configured device
        current_device = self.recorder.config.get('audio', 'device_name', fallback='')

        # Show device selection screen
        self.push_screen(
            DeviceSelectionScreen(devices, current_device),
            self._on_device_selected
        )

    def _on_device_selected(self, device_name: str) -> None:
        """Callback when a device is selected from the device selection screen."""
        log_panel = self.query_one(LogPanel)

        if not device_name:
            log_panel.add_entry("Device selection cancelled")
            return

        if self.recorder is None:
            log_panel.add_entry("ERROR: No recorder available")
            return

        # Update the recorder config with the selected device
        if not self.recorder.config.has_section('audio'):
            self.recorder.config.add_section('audio')
        self.recorder.config.set('audio', 'device_name', device_name)
        self.recorder.config.set('audio', 'auto_detect_device', 'false')

        log_panel.add_entry(f"Device set: {device_name}")

        # Update info panel to show the new device
        self._sync_info_panel()

    def action_edit_session_label(self) -> None:
        """Edit the user-facing session name/label while recording (display-only)."""
        log_panel = self.query_one(LogPanel)

        if self.recorder is None:
            log_panel.add_entry("ERROR: No recorder available")
            return

        if not self.recorder.is_recording():
            log_panel.add_entry("No active recording to rename")
            return

        status = self.recorder.get_status()
        current = status.get("session_label") or status.get("session_name") or ""
        self.push_screen(
            SessionNameModal(default_value=str(current), title="Edit session name (display only):"),
            self._on_session_label_submitted,
        )

    def _on_session_label_submitted(self, new_label: str) -> None:
        """Callback when session label is edited."""
        log_panel = self.query_one(LogPanel)

        if not new_label:
            log_panel.add_entry("Rename cancelled")
            return

        if self.recorder is None:
            log_panel.add_entry("ERROR: No recorder available")
            return

        try:
            # Display-only label; does not rename on disk.
            self.recorder.set_session_label(new_label)
            log_panel.add_entry(f"Session label set: {new_label}")
            self._last_status = None
            self._sync_recorder_status()
        except Exception as e:
            log_panel.add_entry(f"ERROR: {e}")
    
    def action_show_help(self) -> None:
        """Show help overlay with keyboard shortcuts."""
        self.push_screen(HelpModal())


def run_tui(recorder: "EchologRecorder | None" = None, no_meter: bool = False) -> None:
    """Entry point to run the TUI application.

    Args:
        recorder: Optional EchologRecorder instance to integrate with.
                  If provided, TUI will sync status from the recorder.
        no_meter: If True, hide the VU meter panel to reduce CPU usage.
    """
    app = EchologTUI(recorder=recorder, no_meter=no_meter)
    app.run()


if __name__ == "__main__":
    run_tui()
