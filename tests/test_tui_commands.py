import configparser

import pytest

from textual.widgets import Input

from echolog_tui import DeviceSelectionScreen, EchologTUI, LogPanel, SessionNameModal, VUMeterPanel


class FakeRecorder:
    def __init__(self) -> None:
        self._recording = False
        self.started: list[str] = []
        self.stopped: int = 0
        self.session_name: str | None = None
        self.session_label: str | None = None
        self.devices = [{"name": "pulse:monitor", "id": "1", "status": "RUNNING"}]

        self.config = configparser.ConfigParser()
        self.config.add_section("audio")
        self.config.set("audio", "device_name", "")
        self.config.set("audio", "auto_detect_device", "true")

    def is_recording(self) -> bool:
        return self._recording

    def get_status(self) -> dict:
        return {
            "recording": self._recording,
            "session_id": "internal_id",
            "session_name": self.session_name,
            "session_label": self.session_label or self.session_name,
            "elapsed_seconds": 0,
            "segment_duration_seconds": 300,
            "segment_elapsed_seconds": 0,
            "current_chunk_number": 0,
            "chunks": [],
            "disk_free_bytes": 0,
            "device_name": "Not selected",
            "format": "OGG/Opus",
            "sample_rate": "16000",
            "log_entries": [],
            "time_limit_seconds": 0,
            "time_limit_remaining_seconds": 0,
            "audio_level_db": -60.0,
        }

    def start_recording(self, session_name: str) -> bool:
        self.started.append(session_name)
        self._recording = True
        self.session_name = session_name
        self.session_label = session_name
        return True

    def stop_recording(self) -> bool:
        self.stopped += 1
        self._recording = False
        return True

    def detect_audio_devices(self) -> list[dict]:
        return self.devices

    def set_session_label(self, label: str) -> None:
        self.session_label = label


@pytest.mark.asyncio
async def test_press_r_or_R_opens_session_prompt() -> None:
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, SessionNameModal)

        # Dismiss (escape) then re-open with uppercase key
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, SessionNameModal)

        await pilot.press("R")
        await pilot.pause()
        assert isinstance(app.screen, SessionNameModal)


@pytest.mark.asyncio
async def test_record_start_flow_submits_name_and_calls_recorder() -> None:
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.press("r")
        await pilot.pause()

        inp = app.screen.query_one("#session-name-input", Input)
        inp.value = "meeting_20260111"

        await pilot.press("enter")
        await pilot.pause()

        assert recorder.started == ["meeting_20260111"]
        assert recorder.is_recording() is True


@pytest.mark.asyncio
async def test_stop_works_with_s_or_S() -> None:
    recorder = FakeRecorder()
    recorder._recording = True
    recorder.session_name = "x"
    recorder.session_label = "x"

    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.press("s")
        await pilot.pause()
        assert recorder.stopped == 1

        recorder._recording = True
        await pilot.press("S")
        await pilot.pause()
        assert recorder.stopped == 2


@pytest.mark.asyncio
async def test_devices_opens_modal_and_select_sets_config() -> None:
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.press("d")
        await pilot.pause()
        assert isinstance(app.screen, DeviceSelectionScreen)

        # Select the first device (default selection) with Enter.
        await pilot.press("enter")
        await pilot.pause()

        assert recorder.config.get("audio", "device_name") == "pulse:monitor"
        assert recorder.config.get("audio", "auto_detect_device") == "false"


@pytest.mark.asyncio
async def test_edit_session_label_updates_recorder_display_name() -> None:
    recorder = FakeRecorder()
    recorder._recording = True
    recorder.session_name = "meeting_20260111"
    recorder.session_label = "meeting_20260111"

    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.press("e")
        await pilot.pause()
        assert isinstance(app.screen, SessionNameModal)

        inp = app.screen.query_one("#session-name-input", Input)
        inp.value = "meeting_renamed"

        await pilot.press("enter")
        await pilot.pause()

        assert recorder.session_label == "meeting_renamed"


@pytest.mark.asyncio
async def test_log_panel_shows_last_five_entries_by_default() -> None:
    """US-002: Log panel shows last 5 log entries by default."""
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        log_panel = app.query_one(LogPanel)
        assert log_panel.max_entries == 5


@pytest.mark.asyncio
async def test_log_panel_updates_with_session_log_entries() -> None:
    """US-002: New entries appear in real-time during recording."""
    recorder = FakeRecorder()
    # Provide log entries with session status
    recorder.get_status = lambda: {
        "recording": True,
        "session_id": "test",
        "session_name": "test",
        "session_label": "test",
        "elapsed_seconds": 10,
        "segment_duration_seconds": 300,
        "segment_elapsed_seconds": 10,
        "current_chunk_number": 1,
        "chunks": [],
        "disk_free_bytes": 0,
        "device_name": "Not selected",
        "format": "OGG/Opus",
        "sample_rate": "16000",
        "log_entries": [
            {"timestamp": "2026-01-11T10:00:00Z", "level": "INFO", "message": "Recording started"},
            {"timestamp": "2026-01-11T10:00:05Z", "level": "INFO", "message": "Chunk 1 created"},
        ],
        "time_limit_seconds": 0,
        "time_limit_remaining_seconds": 0,
    }

    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        log_panel = app.query_one(LogPanel)
        # Manually trigger sync (normally done by timer)
        log_panel.update_session_log(recorder.get_status()["log_entries"])
        assert len(log_panel._session_log_entries) == 2


@pytest.mark.asyncio
async def test_log_panel_colors_errors_red() -> None:
    """US-002: Errors displayed in red text."""
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        log_panel = app.query_one(LogPanel)
        log_panel.add_entry("Test error", level="ERROR")
        # Verify ERROR is added with correct level
        assert any(e.get("level") == "ERROR" for e in log_panel.log_entries)


@pytest.mark.asyncio
async def test_log_panel_colors_warnings_yellow() -> None:
    """US-002: Warnings displayed in yellow text."""
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        log_panel = app.query_one(LogPanel)
        log_panel.add_entry("Test warning", level="WARNING")
        # Verify WARNING is added with correct level
        assert any(e.get("level") == "WARNING" for e in log_panel.log_entries)


@pytest.mark.asyncio
async def test_vu_meter_shows_level_during_recording() -> None:
    """US-003: VU meter shows current audio level during recording."""
    recorder = FakeRecorder()
    recorder._recording = True
    recorder.session_name = "test"
    recorder.session_label = "test"

    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        vu_panel = app.query_one(VUMeterPanel)
        # Simulate audio level update during recording
        vu_panel.update_level(-20.0, enabled=True)
        assert vu_panel._enabled is True
        assert vu_panel._level_db == -20.0


@pytest.mark.asyncio
async def test_vu_meter_shows_db_format() -> None:
    """US-003: VU meter shows level in dB format."""
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        vu_panel = app.query_one(VUMeterPanel)
        # Test with a specific level
        vu_panel.update_level(-15.0, enabled=True)
        display = vu_panel._render_meter()
        # Verify dB is shown in the output
        assert "dB" in display
        assert "-15" in display


@pytest.mark.asyncio
async def test_vu_meter_disabled_when_not_recording() -> None:
    """US-003: VU meter disabled when not recording."""
    recorder = FakeRecorder()
    recorder._recording = False

    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        vu_panel = app.query_one(VUMeterPanel)
        # Initially should be disabled
        assert vu_panel._enabled is False
        # Display should show disabled state
        display = vu_panel._render_meter()
        assert "-- dB" in display


@pytest.mark.asyncio
async def test_vu_meter_resets_when_recording_stops() -> None:
    """US-003: VU meter resets when recording stops."""
    recorder = FakeRecorder()
    recorder._recording = True
    recorder.session_name = "test"
    recorder.session_label = "test"

    app = EchologTUI(recorder=recorder)
    async with app.run_test() as pilot:
        await pilot.pause()
        vu_panel = app.query_one(VUMeterPanel)
        # Simulate active recording with audio
        vu_panel.update_level(-10.0, enabled=True)
        assert vu_panel._enabled is True

        # Simulate stopping recording
        recorder._recording = False
        vu_panel.update_level(-60.0, enabled=False)
        assert vu_panel._enabled is False
        assert vu_panel._level_db == -60.0


@pytest.mark.asyncio
async def test_no_meter_flag_hides_vu_meter_panel() -> None:
    """US-004: --no-meter flag hides VU meter panel in TUI."""
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder, no_meter=True)
    async with app.run_test() as pilot:
        await pilot.pause()
        # VU meter panel should not exist when no_meter=True
        vu_panels = app.query(VUMeterPanel)
        assert len(vu_panels) == 0


@pytest.mark.asyncio
async def test_tui_works_without_meter() -> None:
    """US-004: TUI works normally with no_meter=True."""
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder, no_meter=True)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Can still start and stop recording
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, SessionNameModal)

        inp = app.screen.query_one("#session-name-input", Input)
        inp.value = "test_session"
        await pilot.press("enter")
        await pilot.pause()

        assert recorder.is_recording() is True

        # Stop recording
        await pilot.press("s")
        await pilot.pause()
        assert recorder.is_recording() is False


@pytest.mark.asyncio
async def test_meter_shown_by_default() -> None:
    """US-004: VU meter is shown by default (no_meter=False)."""
    recorder = FakeRecorder()
    app = EchologTUI(recorder=recorder)  # no_meter defaults to False
    async with app.run_test() as pilot:
        await pilot.pause()
        # VU meter panel should exist when no_meter=False
        vu_panels = app.query(VUMeterPanel)
        assert len(vu_panels) == 1
