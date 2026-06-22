"""Compare RAY-UI vs RAYX simulation results for the dipole beamline.

Run simulation_rayui.py and simulation_rayx.py first to generate the data.
Produces comparison_plots.png, scatter_per_energy.png, and grating_efficiency.png
in this folder.
"""

import os
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import pandas as pd

this_dir = os.path.dirname(os.path.realpath(__file__))

# ── Load aggregated results ───────────────────────────────────────────────────

def load(sim_name, element, export_type="RawRaysOutgoing"):
    path = os.path.join(
        this_dir, f"RAYPy_Simulation_{sim_name}", f"{element}_{export_type}.csv"
    )
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing: {path}\n"
            f"Run simulation_{sim_name}.py first."
        )
    df = pd.read_csv(path, index_col=0)
    df.columns = df.columns.str.strip()
    return df


ALL_ELEMENTS = [
    "Dipole",
    "M1",
    "PremirrorM2",
    "PG",
    "M3",
    "ExitSlit",
    "KB1_hor",
    "KB2_ver",
    "DetectorAtFocus",
]

elements = ["Dipole", "DetectorAtFocus"]
data = {("rayui", el): load("rayui", el) for el in elements}
data.update({("rayx",  el): load("rayx",  el) for el in elements})

energy_col = "Dipole.photonEnergy"

# ── Raw ray helpers ───────────────────────────────────────────────────────────

MAX_SCATTER_PTS = 2000


def _read_raw(path, element, max_pts=MAX_SCATTER_PTS):
    """Return (ox, oy) arrays from a per-simulation raw ray CSV, or (None, None)."""
    try:
        with open(path) as fh:
            first = fh.readline()
        # rayx: "# rayx export\n"; rayui: "sep=\t\n"
        skiprows = 1 if not first.startswith("#") else None
        df = pd.read_csv(path, sep="\t", comment="#", header=0, skiprows=skiprows)
        ox_col, oy_col = f"{element}_OX", f"{element}_OY"
        if ox_col in df.columns and len(df) > 0:
            if len(df) > max_pts:
                df = df.sample(max_pts, random_state=0)
            return df[ox_col].values, df[oy_col].values
    except Exception:
        pass
    return None, None


def load_scatter(sim_name, element, sim_idx=0):
    path = os.path.join(
        this_dir,
        f"RAYPy_Simulation_{sim_name}", "round_0",
        f"{sim_idx}_{element}-RawRaysOutgoing.csv",
    )
    return _read_raw(path, element)


# ── Load simulation index → energy mapping ────────────────────────────────────

def load_looper(sim_name):
    path = os.path.join(this_dir, f"RAYPy_Simulation_{sim_name}", "looper.csv")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


looper = load_looper("rayx")
sim_indices = looper["Simulation Number"].astype(int).tolist()
energies_eV  = looper["Dipole.photonEnergy"].astype(float).tolist()

# ── Figure 1: metrics + single-energy scatter ─────────────────────────────────

# Scatter at lowest energy for the summary figure
scatter = {}
for element in elements:
    for engine in ("rayui", "rayx"):
        scatter[(engine, element)] = load_scatter(engine, element, sim_idx=0)

metrics = [
    ("PercentageRaysSurvived", "Flux (%)"),
    ("PhotonFlux",            "Photon flux (ph/s)"),
    ("HorizontalFocusFWHM",   "Horizontal focus FWHM (mm)"),
    ("VerticalFocusFWHM",     "Vertical focus FWHM (mm)"),
    ("Bandwidth",             "Bandwidth (eV)"),
]

n_metric_rows = len(metrics)
n_cols = len(elements)
n_rows = n_metric_rows + 1

fig1, axes = plt.subplots(
    n_rows, n_cols,
    figsize=(6 * n_cols, 3.5 * n_metric_rows + 4),
    squeeze=False,
    gridspec_kw={"height_ratios": [1] * n_metric_rows + [1.2]},
)
fig1.suptitle("RAY-UI vs RAYX — dipole beamline", fontsize=13)

for col_idx, element in enumerate(elements):
    axes[0, col_idx].set_title(element, fontsize=11)
    for row_idx, (metric, ylabel) in enumerate(metrics):
        ax = axes[row_idx, col_idx]
        df_ui = data[("rayui", element)]
        df_rx = data[("rayx",  element)]
        ax.plot(df_ui[energy_col], df_ui[metric], color="C0", ls="-",  marker="o", ms=4, label="RAY-UI")
        ax.plot(df_rx[energy_col], df_rx[metric], color="C1", ls="--", marker="s", ms=4, label="RAYX")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    axes[n_metric_rows - 1, col_idx].set_xlabel("Photon energy (eV)")

for col_idx, element in enumerate(elements):
    ax = axes[n_metric_rows, col_idx]
    has_data = False
    for engine, color, label in [("rayui", "C0", "RAY-UI"), ("rayx", "C1", "RAYX")]:
        ox, oy = scatter[(engine, element)]
        if ox is not None and len(ox) > 0:
            ax.scatter(ox, oy, s=2, alpha=0.4, color=color, label=f"{label} ({len(ox)} pts)")
            has_data = True
    if has_data:
        ax.set_xlabel("OX (mm)")
        ax.set_ylabel("OY (mm)")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, markerscale=4)
    else:
        ax.text(0.5, 0.5, "No raw ray data\n(re-run with remove_rawrays=False)",
                ha="center", va="center", transform=ax.transAxes, fontsize=9, color="gray")
        ax.axis("off")
    ax.set_title(f"{element} — ray positions @ {energies_eV[0]:.0f} eV", fontsize=10)

fig1.tight_layout()
out1 = os.path.join(this_dir, "comparison_plots.png")
fig1.savefig(out1, dpi=150)
print(f"Saved: {out1}")

# ── Figure 2: scatter per energy ──────────────────────────────────────────────

n_energies = len(energies_eV)
fig2, axes2 = plt.subplots(
    2, n_energies,
    figsize=(4 * n_energies, 8),
    squeeze=False,
)
fig2.suptitle("Ray positions per energy — RAY-UI vs RAYX", fontsize=13)

row_elements = ["Dipole", "DetectorAtFocus"]

for col_idx, (sim_idx, energy) in enumerate(zip(sim_indices, energies_eV)):
    for row_idx, element in enumerate(row_elements):
        ax = axes2[row_idx, col_idx]
        has_data = False
        for engine, color, label in [("rayui", "C0", "RAY-UI"), ("rayx", "C1", "RAYX")]:
            ox, oy = load_scatter(engine, element, sim_idx=sim_idx)
            if ox is not None and len(ox) > 0:
                ax.scatter(ox, oy, s=1, alpha=0.4, color=color,
                           label=f"{label} ({len(ox)})")
                has_data = True
        if has_data:
            ax.set_aspect("equal", adjustable="datalim")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=6, markerscale=5)
        else:
            ax.text(0.5, 0.5, "no data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=8, color="gray")
            ax.axis("off")
        if row_idx == 0:
            ax.set_title(f"{energy:.0f} eV", fontsize=10)
        if col_idx == 0:
            ax.set_ylabel(f"{element}\nOY (mm)", fontsize=9)
        if row_idx == 1:
            ax.set_xlabel("OX (mm)", fontsize=9)

fig2.tight_layout()
out2 = os.path.join(this_dir, "scatter_per_energy.png")
fig2.savefig(out2, dpi=150)
print(f"Saved: {out2}")

# ── Figure 3: grating efficiency — graxpy vs RAY-UI ──────────────────────────

GRATING_NAME = "PG"


def _read_rayui_pg_efficiency(sim_idx, grating_name=GRATING_NAME):
    """Extract reflectivityParallel for *grating_name* from a saved RAY-UI RML."""
    rml_path = os.path.join(
        this_dir, "RAYPy_Simulation_rayui", "round_0", f"{sim_idx}_rayui.rml"
    )
    if not os.path.exists(rml_path):
        return None
    tree = ET.parse(rml_path)
    for obj in tree.getroot().iter("object"):
        if obj.get("name") == grating_name:
            for param in obj.iter("param"):
                if param.get("id") == "reflectivityParallel" and param.get("enabled") == "T":
                    try:
                        return float(param.text)
                    except (TypeError, ValueError):
                        return None
    return None


def _read_graxpy_efficiency(sim_idx, grating_name=GRATING_NAME):
    """Read efficiency_p for *grating_name* from a graxpy CSV."""
    csv_path = os.path.join(
        this_dir, "RAYPy_Simulation_rayx", "round_0",
        f"{sim_idx}_rayx_graxpy_efficiency.csv",
    )
    if not os.path.exists(csv_path):
        return None
    df = pd.read_csv(csv_path)
    row = df[df["grating_name"] == grating_name]
    if row.empty:
        return None
    return float(row["efficiency_p"].iloc[0])


eff_rayui  = [_read_rayui_pg_efficiency(i) for i in sim_indices]
eff_graxpy = [_read_graxpy_efficiency(i)   for i in sim_indices]

fig3, ax3 = plt.subplots(figsize=(7, 4))
fig3.suptitle(f"Grating efficiency — {GRATING_NAME}", fontsize=13)

if any(v is not None for v in eff_rayui):
    e_ui = [(e, v) for e, v in zip(energies_eV, eff_rayui) if v is not None]
    ax3.plot(*zip(*e_ui), color="C0", ls="-", marker="o", ms=5, label="RAY-UI (reflectivityParallel)")

if any(v is not None for v in eff_graxpy):
    e_gx = [(e, v) for e, v in zip(energies_eV, eff_graxpy) if v is not None]
    ax3.plot(*zip(*e_gx), color="C1", ls="--", marker="s", ms=5, label="graxpy (RCWA, p-pol)")

ax3.set_xlabel("Photon energy (eV)")
ax3.set_ylabel("Efficiency")
ax3.legend()
ax3.grid(True, alpha=0.3)

fig3.tight_layout()
out3 = os.path.join(this_dir, "grating_efficiency.png")
fig3.savefig(out3, dpi=150)
print(f"Saved: {out3}")

# ── Figure 4: per-element metrics — RAY-UI vs RAYX ───────────────────────────

per_elem_metrics = [
    ("PercentageRaysSurvived", "Flux (%)"),
    ("NumberRaysSurvived",     "Rays survived"),
    ("HorizontalFocusFWHM",   "Hor. FWHM (mm)"),
    ("VerticalFocusFWHM",     "Ver. FWHM (mm)"),
    ("Bandwidth",             "Bandwidth (eV)"),
]

n_elem_cols = len(ALL_ELEMENTS)
n_elem_rows = len(per_elem_metrics)

fig4, axes4 = plt.subplots(
    n_elem_rows, n_elem_cols,
    figsize=(3.5 * n_elem_cols, 3 * n_elem_rows),
    squeeze=False,
)
fig4.suptitle("RAY-UI vs RAYX — per element", fontsize=13)

for col_idx, element in enumerate(ALL_ELEMENTS):
    axes4[0, col_idx].set_title(element, fontsize=9)

    try:
        df_ui = load("rayui", element)
    except FileNotFoundError:
        df_ui = None
    try:
        df_rx = load("rayx", element)
    except FileNotFoundError:
        df_rx = None

    for row_idx, (metric, ylabel) in enumerate(per_elem_metrics):
        ax = axes4[row_idx, col_idx]

        if df_ui is not None and metric in df_ui.columns:
            ax.plot(
                df_ui[energy_col], df_ui[metric],
                color="C0", ls="-", marker="o", ms=3, label="RAY-UI",
            )
        if df_rx is not None and metric in df_rx.columns:
            ax.plot(
                df_rx[energy_col], df_rx[metric],
                color="C1", ls="--", marker="s", ms=3, label="RAYX",
            )

        if col_idx == 0:
            ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3)
        if row_idx == 0 and col_idx == 0:
            ax.legend(fontsize=7)
        if row_idx == n_elem_rows - 1:
            ax.set_xlabel("Energy (eV)", fontsize=8)

fig4.tight_layout()
out4 = os.path.join(this_dir, "per_element_metrics.png")
fig4.savefig(out4, dpi=150)
print(f"Saved: {out4}")
