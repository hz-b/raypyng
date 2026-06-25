import os
import time

from raypyng.runner import RayUIAPI, RayUIRunner

# Point at the stream build of RAY-UI (the one that supports the `rawdata`
# command). Set to None to use the auto-detected default installation instead.
RAY_PATH = "/home/simone/Applications/Ray-UI-development-stream"

if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))

    r = RayUIRunner(ray_path=RAY_PATH, hide=True)
    a = RayUIAPI(r)

    # Start a RAY-UI instance
    r.run()

    # Confirm that it is running and print the process id
    print("Confirm that RAY-UI is running:", r.isrunning)
    print("RAY-UI is running with pid", r.pid)

    # load an rml file
    print("Loading rml file")
    a.load(os.path.join(this_file_dir, "..", "rml", "dipole_beamline.rml"))

    print("Trace...")
    a.trace(analyze=True)

    # print("Exporting")
    # a.export("Dipole,DetectorAtFocus", "RawRaysOutgoing", this_file_dir, "test_export")

    # ------------------------------------------------------------------
    # rawdata: stream the raw rays straight into memory as a numpy array,
    # WITHOUT writing any file. This requires a RAY-UI build that supports
    # the `rawdata` background command (the "stream" version).
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Testing the rawdata command (zero-file ray streaming)")
    print("=" * 60)
    try:
        # Short timeout so a build WITHOUT rawdata fails fast instead of hanging.
        rays = a.rawdata("DetectorAtFocus", "RawRaysOutgoing", timeout=20)
        print("rawdata SUCCESS — received rays directly in memory!")
        print(f"  type           : {type(rays).__name__}")
        print(f"  number of rays : {len(rays)}")
        print(f"  columns        : {', '.join(rays.dtype.names)}")
        if len(rays) > 0:
            print(f"  first ray OX/OY/OZ : "
                  f"{rays['OX'][0]:.6g}, {rays['OY'][0]:.6g}, {rays['OZ'][0]:.6g}")
            print(f"  energy range [eV]  : "
                  f"{rays['EN'].min():.4g} .. {rays['EN'].max():.4g}")
    except Exception as exc:
        print("rawdata FAILED — no data received.")
        print(f"  error: {exc!r}")
        print("  Hint: this RAY-UI build probably does not support 'rawdata'.")
        print("  Rebuild/install RAY-UI from branch 'feature/rawrays-stream'.")
    print("=" * 60 + "\n")

    print("Killing the RAY-UI process")
    r.kill()
    # sometime it takes a while to kill the process
    time.sleep(2)
    print("Confirm that RAY-UI is running:", r.isrunning)
