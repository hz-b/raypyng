from __future__ import annotations

import re
from pathlib import Path

import pytest

TEST_RML = Path(__file__).resolve().parents[1] / "data" / "rml" / "dipole.rml"

pytestmark = pytest.mark.requires_ray_ui


def _write_small_rml(tmp_path: Path) -> Path:
    text = TEST_RML.read_text(encoding="utf8")
    text = re.sub(
        r'(<param id="numberRays" enabled="T">)\s*100000(\s*</param>)',
        r"\g<1>1000\g<2>",
        text,
        count=1,
    )
    rml_path = tmp_path / "dipole_small.rml"
    rml_path.write_text(text, encoding="utf8")
    return rml_path


def _command_with_transcript(api, tmp_path: Path, command_name: str, func, *args, **kwargs):
    transcript: list[str] = []
    original_readline = api._runner._readline_with_timeout

    def _capturing_readline(timeout=None):
        line = original_readline(timeout=timeout)
        if line is not None:
            transcript.append(line)
        return line

    api._runner._readline_with_timeout = _capturing_readline
    try:
        result = func(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        transcript_path = tmp_path / f"{command_name}_transcript.log"
        transcript_path.write_text("\n".join(transcript), encoding="utf8")
        raise AssertionError(
            f"{command_name} failed; transcript saved to {transcript_path}\n"
            + "\n".join(transcript)
        ) from exc
    finally:
        api._runner._readline_with_timeout = original_readline
    return result, transcript


def test_runner_start_stop(rayui_api):
    runner, _api = rayui_api

    runner.run()

    assert runner.isrunning is True
    assert runner.pid is not None

    runner.kill()

    assert runner.isrunning is False


def test_api_load(rayui_api, tmp_path: Path):
    runner, api = rayui_api
    rml_path = _write_small_rml(tmp_path)
    runner.run()

    result, _transcript = _command_with_transcript(api, tmp_path, "load", api.load, str(rml_path))

    assert result is True


def test_api_trace_no_analyze(rayui_api, tmp_path: Path):
    runner, api = rayui_api
    rml_path = _write_small_rml(tmp_path)
    runner.run()
    _command_with_transcript(api, tmp_path, "load", api.load, str(rml_path))

    result, _transcript = _command_with_transcript(
        api, tmp_path, "trace_noanalyze", api.trace, analyze=False
    )

    assert result is True


def test_api_save(rayui_api, tmp_path: Path):
    runner, api = rayui_api
    rml_path = _write_small_rml(tmp_path)
    save_dir = tmp_path / "save_output"
    save_dir.mkdir()
    save_path = save_dir / "saved copy.rml"
    runner.run()
    _command_with_transcript(api, tmp_path, "load", api.load, str(rml_path))

    result, _transcript = _command_with_transcript(api, tmp_path, "save", api.save, str(save_path))

    assert result is True
    assert save_path.exists()


def test_api_export_single_object(rayui_api, tmp_path: Path):
    runner, api = rayui_api
    rml_path = _write_small_rml(tmp_path)
    export_dir = tmp_path / "export_output"
    export_dir.mkdir()
    runner.run()
    _command_with_transcript(api, tmp_path, "load", api.load, str(rml_path))
    _command_with_transcript(api, tmp_path, "trace_noanalyze", api.trace, analyze=False)

    result, _transcript = _command_with_transcript(
        api,
        tmp_path,
        "export_single_dipole",
        api.export,
        "Dipole",
        "RawRaysOutgoing",
        str(export_dir),
        "single_",
    )

    assert result is True
    assert (export_dir / "single_Dipole-RawRaysOutgoing.csv").is_file()


def test_api_export_detector_object(rayui_api, tmp_path: Path):
    runner, api = rayui_api
    rml_path = _write_small_rml(tmp_path)
    export_dir = tmp_path / "detector_output"
    export_dir.mkdir()
    runner.run()
    _command_with_transcript(api, tmp_path, "load", api.load, str(rml_path))
    _command_with_transcript(api, tmp_path, "trace_noanalyze", api.trace, analyze=False)

    result, _transcript = _command_with_transcript(
        api,
        tmp_path,
        "export_detector",
        api.export,
        "DetectorAtFocus",
        "RawRaysOutgoing",
        str(export_dir),
        "detector_",
    )

    assert result is True
    assert (export_dir / "detector_DetectorAtFocus-RawRaysOutgoing.csv").is_file()


def test_api_export_multi_object(rayui_api, tmp_path: Path):
    runner, api = rayui_api
    rml_path = _write_small_rml(tmp_path)
    export_dir = tmp_path / "multi_output"
    export_dir.mkdir()
    runner.run()
    _command_with_transcript(api, tmp_path, "load", api.load, str(rml_path))
    _command_with_transcript(api, tmp_path, "trace_noanalyze", api.trace, analyze=False)

    result, _transcript = _command_with_transcript(
        api,
        tmp_path,
        "export_multi",
        api.export,
        "Dipole,DetectorAtFocus",
        "RawRaysOutgoing",
        str(export_dir),
        "multi_",
    )

    assert result is True
    assert (export_dir / "multi_Dipole-RawRaysOutgoing.csv").is_file()
    assert (export_dir / "multi_DetectorAtFocus-RawRaysOutgoing.csv").is_file()
