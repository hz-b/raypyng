"""Question for rayx developer: how to correctly select surviving rays at the last element?

Context
-------
We wrap rayx inside raypyng to run parameter sweeps over a synchrotron beamline.
After tracing, we export the rays at each optical element (source + all optical elements)
and compute statistics (FWHM of spot size, flux, bandwidth, ...).

The core question is: given the full rays DataFrame returned by rays_to_df(), what is
the correct way to select only the rays that *survived* the beamline and ended up on the
last element (DetectorAtFocus in this example) via the intended optical path?

This matters because the detector collects many stray/scattered rays in addition to the
primary beam, and including those inflates the spot size.

Run this script and show the plots to the developer.
"""

import os

import matplotlib.pyplot as plt
import rayx
import rayx.core as rc

# ── Load and trace ────────────────────────────────────────────────────────────

this_dir = os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_dir, "../rayx_comparison/test_dipole.rml")

beamline = rc.import_beamline(rml_file)
rays = beamline.trace()
df = rayx.rays_to_df(rays)

# ── Beamline layout ───────────────────────────────────────────────────────────

source_names = [s.name for s in beamline.sources]
element_names = [e.name for e in beamline.elements]

# object_id assignment: sources first (0..n_sources-1), then elements
n_sources = len(source_names)
name_to_id = {name: i for i, name in enumerate(source_names)}
name_to_id.update({name: n_sources + i for i, name in enumerate(element_names)})

print("Sources:", source_names)
print("Elements:", element_names)
print("name → object_id:", name_to_id)
print()
print("DataFrame columns:", list(df.columns))
print(f"Total rows in DataFrame: {len(df)}")
print()

# ── Rays at the last element ──────────────────────────────────────────────────

last_element = element_names[-1]   # "DetectorAtFocus"
last_id = name_to_id[last_element] # e.g. 8 for this beamline

at_detector = df[df["object_id"] == last_id]
print(f"All rows with object_id == {last_id} ({last_element}): {len(at_detector)}")
print()

# Distribution of path_event_id values at the detector
print("path_event_id distribution at detector:")
print(at_detector["path_event_id"].value_counts().sort_index().to_string())
print()

# ── Approach A: all rows at the detector ─────────────────────────────────────
# Problem: includes stray/scattered rays that arrived via shorter paths.

sel_A = at_detector

# ── Approach B: only rows where path_event_id == object_id ───────────────────
# Assumption: a ray following the full intended path visits exactly one element
# per step, so its sequential counter equals the element's object_id.
# Problem: gives 0 rays at off-design energies where the beam does not traverse
# all optical elements in sequence.

sel_B = at_detector[at_detector["path_event_id"] == last_id]

# ── Approach C: path_id chain intersection ────────────────────────────────────
# Keep only rays whose path_id appears at the target element AND at every
# preceding element (0 … last_id-1). This selects rays that physically hit
# every optical surface along the intended path, regardless of path_event_id.

surviving_ids = set(at_detector["path_id"])
for preceding in range(last_id):
    surviving_ids &= set(df.loc[df["object_id"] == preceding, "path_id"])
sel_C = at_detector[at_detector["path_id"].isin(surviving_ids)]

print(f"Approach A (all at detector):              {len(sel_A):>7} rays")
print(f"Approach B (path_event_id == object_id):   {len(sel_B):>7} rays")
print(f"Approach C (path_id chain intersection):   {len(sel_C):>7} rays")
print()

if "event_type" in df.columns:
    print("EventType values at detector:", at_detector["event_type"].value_counts().to_dict())

# ── Scatter plot: compare the three selections ────────────────────────────────

MAX_PTS = 3000


def subsample(sub):
    if len(sub) > MAX_PTS:
        return sub.sample(MAX_PTS, random_state=0)
    return sub


fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle(f"Ray positions at {last_element}", fontsize=12)

for ax, sel, title in [
    (axes[0], sel_A, f"A: all at detector\n({len(sel_A)} rays)"),
    (axes[1], sel_B, f"B: path_event_id == object_id ({last_id})\n({len(sel_B)} rays)"),
    (axes[2], sel_C, f"C: path_id chain intersection\n({len(sel_C)} rays)"),
]:
    sub = subsample(sel)
    if len(sub) > 0:
        ax.scatter(sub["position_x"], sub["position_y"], s=1, alpha=0.3)
    else:
        ax.text(0.5, 0.5, "0 rays", ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("position_x (mm)")
    ax.set_ylabel("position_y (mm)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, alpha=0.3)

fig.tight_layout()
out = os.path.join(this_dir, "surviving_rays_question.png")
fig.savefig(out, dpi=150)
print(f"Saved: {out}")
plt.show()
