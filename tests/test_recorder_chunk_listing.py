from pathlib import Path

from echolog import EchologRecorder


def test_get_status_lists_chunks_even_with_underscores_in_session_name(tmp_path: Path) -> None:
    cfg_path = tmp_path / "echolog.conf"
    r = EchologRecorder(str(cfg_path))

    # Configure output/session state without starting ffmpeg.
    r.session_name = "meeting_2026_01_11"
    r.session_label = r.session_name
    r.session_id = f"{r.session_name}_20260111_101010"
    r._session_dir = tmp_path / r.session_name
    r._session_dir.mkdir(parents=True, exist_ok=True)

    fmt = r.config.get("recording", "format", fallback="ogg")
    chunk1 = r._session_dir / f"{r.session_id}_chunk_001.{fmt}"
    chunk2 = r._session_dir / f"{r.session_id}_chunk_002.{fmt}"
    chunk1.write_bytes(b"a" * 10)
    chunk2.write_bytes(b"b" * 20)

    # Mark chunk 001 finalized; chunk 002 still in-progress.
    r._finalized_chunks.add(chunk1.name)

    status = r.get_status()
    assert status["session_name"] == "meeting_2026_01_11"
    assert status["session_label"] == "meeting_2026_01_11"
    assert [c["filename"] for c in status["chunks"]] == [chunk1.name, chunk2.name]
    assert [c["finalized"] for c in status["chunks"]] == [True, False]


def test_check_recording_files_uses_session_id_prefix(tmp_path: Path) -> None:
    cfg_path = tmp_path / "echolog.conf"
    r = EchologRecorder(str(cfg_path))

    r.session_name = "my_session"
    r.session_id = "my_session_20260111_123000"
    r._session_dir = tmp_path / r.session_name
    r._session_dir.mkdir(parents=True, exist_ok=True)

    fmt = r.config.get("recording", "format", fallback="ogg")
    (r._session_dir / f"{r.session_id}_chunk_001.{fmt}").write_bytes(b"x")
    (r._session_dir / f"{r.session_id}_chunk_002.{fmt}").write_bytes(b"y")
    # Noise file from another run should not match.
    (r._session_dir / f"other_20260111_000000_chunk_001.{fmt}").write_bytes(b"z")

    files = r.check_recording_files()
    assert files == [
        f"{r.session_id}_chunk_001.{fmt}",
        f"{r.session_id}_chunk_002.{fmt}",
    ]
