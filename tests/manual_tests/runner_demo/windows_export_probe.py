from __future__ import annotations

import os
import tempfile
from pathlib import Path

from raypyng.runner import RayUIAPI, RayUIRunner


def main():
    repo_root = Path(__file__).resolve().parents[3]
    rml_path = repo_root / "tests" / "rml" / "dipole.rml"
    out_dir = Path(tempfile.gettempdir()) / "raypyng_windows_export_probe"
    out_dir.mkdir(parents=True, exist_ok=True)

    ray_path = os.environ.get("RAYUI_PATH")
    runner = RayUIRunner(ray_path=ray_path, hide=True)
    api = RayUIAPI(runner)
    transcript: list[str] = []

    try:
        runner.run()
        print("Runner PID:", runner.pid)
        print("Output directory:", out_dir)

        print("Loading...")
        api.load(str(rml_path), cbNewLine=transcript.append)

        print("Tracing...")
        api.trace(analyze=False, cbNewLine=transcript.append)

        print("Single-object export...")
        api.export(
            "Dipole",
            "RawRaysOutgoing",
            str(out_dir),
            "single_",
            cbNewLine=transcript.append,
        )

        print("Detector export...")
        api.export(
            "DetectorAtFocus",
            "RawRaysOutgoing",
            str(out_dir),
            "detector_",
            cbNewLine=transcript.append,
        )

        print("Multi-object export...")
        api.export(
            "Dipole,DetectorAtFocus",
            "RawRaysOutgoing",
            str(out_dir),
            "multi_",
            cbNewLine=transcript.append,
        )
    finally:
        transcript_path = out_dir / "runner_api_transcript.log"
        transcript_path.write_text("\n".join(transcript), encoding="utf8")
        print("Transcript saved to:", transcript_path)
        try:
            api.quit()
        except Exception:
            runner.kill()


if __name__ == "__main__":
    main()
