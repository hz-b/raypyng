# Driving RAY-UI stream by hand from the terminal

These are the raw commands that `example_runner.py` sends under the hood
(`RayUIAPI.load` / `.trace` / `.rawdata`). You can paste them straight into a
RAY-UI stream build to load an rml file, trace it, and request `rawdata`.

You need a RAY-UI build that supports the background `rawdata` command (the
"stream" version, branch `feature/rawrays-stream`).

## 1. Start RAY-UI in background mode

The `-b` flag puts RAY-UI in background/stdin command mode. On Linux the binary
is `rayui.sh`; wrap it in `xvfb-run` if you want it headless.

```bash
RAY_PATH="/home/simone/Applications/Ray-UI-development-stream"

# visible:
"$RAY_PATH/rayui.sh" -b

# or headless (Linux, needs xvfb):
xvfb-run --auto-servernum --server-num=3000 "$RAY_PATH/rayui.sh" -b
```

RAY-UI now reads commands line by line from stdin. Type the following commands
one per line (each prints the command back as an ACK, then `success` / `failed`).

## 2. Load an rml file

```
load /home/simone/projects/raypyng/raypyng/examples/rml/dipole_beamline.rml
```

## 3. Trace

```
trace
```

(`trace noanalyze` to skip ray analysis — `a.trace(analyze=False)`.)

## 4. rawdata — stream raw rays into stdout, no file written

Syntax: `rawdata "<element>" <item_id>`
where `<item_id>` is one of `RawRaysOutgoing`, `RawRaysIncoming`, `RawRaysBeam`.

```
rawdata "DetectorAtFocus" RawRaysOutgoing
```

RAY-UI replies with:
1. the command ACK + `success`
2. a line containing the number of bytes
3. that many bytes of a raw numpy `.npy` blob
   (columns: RN RS RO OX OY OZ DX DY DZ EN PL S0 S1 S2 S3, all float64).

The blob is binary, so in a normal terminal step 3 will look like garbage —
that's expected. `RayUIAPI.rawdata()` reads the byte count and decodes the blob
with `numpy.load`.

## 5. Quit

```
quit
```

---

### One-shot pipe (non-interactive)

Feed all commands at once via a heredoc. The binary `rawdata` output is
redirected to a file so it doesn't corrupt your terminal:

```bash
RAY_PATH="/home/simone/Applications/Ray-UI-development-stream"
RML="/home/simone/projects/raypyng/raypyng/examples/rml/dipole_beamline.rml"

"$RAY_PATH/rayui.sh" -b <<EOF > rawdata_output.bin
load $RML
trace
rawdata "DetectorAtFocus" RawRaysOutgoing
quit
EOF
```
