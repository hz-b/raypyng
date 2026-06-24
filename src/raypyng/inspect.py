"""Tools for inspecting and visualising an RML beamline layout."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .rml import RMLFile


def world_position(element) -> tuple[str, str, str]:
    """Return the world-position (x, y, z) of an RML element as formatted strings.

    Returns ``("-", "-", "-")`` if the element has no worldPosition attribute.
    """
    if not hasattr(element, "worldPosition"):
        return "-", "-", "-"
    position = element.worldPosition
    return (
        f"{float(position.x.cdata):.2f}",
        f"{float(position.y.cdata):.2f}",
        f"{float(position.z.cdata):.2f}",
    )


def build_tables(
    rml_path: str | Path,
    mirror_name_pattern: str = r"^M\d+",
    special_names: tuple[str, ...] = ("dipole",),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a beamline-elements table and a mirror/dipole sub-table from an RML file.

    Args:
        rml_path: Path to the ``.rml`` file.
        mirror_name_pattern: Regex matched against element names to identify mirrors.
            Defaults to ``r"^M\\d+"`` (names starting with M followed by digits).
        special_names: Element names (case-insensitive) always included in the mirror
            table regardless of the name pattern.  Defaults to ``("dipole",)``.

    Returns:
        ``(mirror_table, beamline_table)`` as DataFrames.
        ``mirror_table`` has columns ``name, type, x, y, z, grazingIncAngle, azimuthalAngle``.
        ``beamline_table`` has columns ``name, type, x, y, z``.
    """
    pattern = re.compile(mirror_name_pattern)
    special = {n.lower() for n in special_names}

    rml = RMLFile(None, template=str(rml_path))
    mirror_rows: list[list[str]] = []
    beamline_rows: list[list[str]] = []

    for element in rml.beamline.children():
        name = element.get_attribute("name") or "-"
        element_type = element.get_attribute("type") or "-"
        pos_x, pos_y, pos_z = world_position(element)

        beamline_rows.append([name, element_type, pos_x, pos_y, pos_z])

        if name.lower() in special or pattern.match(name):
            grazing_inc_angle = (
                f"{float(element.grazingIncAngle.cdata):.2f}"
                if hasattr(element, "grazingIncAngle")
                else "-"
            )
            azimuthal_angle = (
                f"{float(element.azimuthalAngle.cdata):.2f}"
                if hasattr(element, "azimuthalAngle")
                else "-"
            )
            mirror_rows.append(
                [name, element_type, pos_x, pos_y, pos_z, grazing_inc_angle, azimuthal_angle]
            )

    mirror_table = pd.DataFrame(
        mirror_rows,
        columns=["name", "type", "x", "y", "z", "grazingIncAngle", "azimuthalAngle"],
    )
    beamline_table = pd.DataFrame(
        beamline_rows,
        columns=["name", "type", "x", "y", "z"],
    )
    return mirror_table, beamline_table


def save_tables(
    mirror_table: pd.DataFrame,
    beamline_table: pd.DataFrame,
    tables_dir: str | Path,
) -> tuple[Path, Path]:
    """Save mirror and beamline tables as CSV files.

    Args:
        mirror_table: DataFrame returned by :func:`build_tables`.
        beamline_table: DataFrame returned by :func:`build_tables`.
        tables_dir: Directory in which to write the CSV files (created if absent).

    Returns:
        ``(mirror_path, beamline_path)`` — paths of the written files.
    """
    tables_dir = Path(tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    mirror_path = tables_dir / "mirror_table.csv"
    beamline_path = tables_dir / "beamline_elements_table.csv"
    mirror_table.to_csv(mirror_path, index=False)
    beamline_table.to_csv(beamline_path, index=False)
    return mirror_path, beamline_path


def plot_beamline_views(
    beamline_table: pd.DataFrame,
    mirror_table: pd.DataFrame,
    output_path: str | Path,
    title: str = "Beamline Layout",
    show_plot: bool = False,
) -> None:
    """Produce top-view, side-view, and 3D plots of the beamline layout.

    Args:
        beamline_table: DataFrame with columns ``name, type, x, y, z``.
        mirror_table: DataFrame with columns
            ``name, type, x, y, z, grazingIncAngle, azimuthalAngle``.
        output_path: Where to save the figure (PNG recommended).
        title: Figure super-title.  Defaults to ``"Beamline Layout"``.
        show_plot: If ``True``, call ``plt.show()`` after saving.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError(
            "matplotlib is required for plot_beamline_views. "
            "Install it with: pip install matplotlib"
        ) from e

    beamline = beamline_table.copy()
    beamline[["x", "y", "z"]] = beamline[["x", "y", "z"]].astype(float)

    mirrors = mirror_table.copy()
    mirrors = mirrors[mirrors["azimuthalAngle"] != "-"].copy()
    mirrors[["x", "y", "z", "azimuthalAngle"]] = mirrors[["x", "y", "z", "azimuthalAngle"]].astype(
        float
    )
    mirror_names = set(mirrors["name"])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(18, 10), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=[2.4, 1.2], height_ratios=[1, 1])

    ax_top = fig.add_subplot(grid[0, 0])
    ax_side = fig.add_subplot(grid[1, 0], sharex=ax_top)
    ax_3d = fig.add_subplot(grid[:, 1], projection="3d")

    arrow_length = max(
        (beamline["z"].max() - beamline["z"].min()) * 0.035,
        (beamline["x"].max() - beamline["x"].min()) * 0.06,
    )

    def draw_mirror_symbol(ax, z_value, axis_value, azimuthal_angle, mirror_type):
        if "PlaneMirror" in mirror_type:
            if azimuthal_angle in (0.0, 180.0):
                dz1, da1 = -arrow_length * 0.10, -arrow_length * 0.10
                dz2, da2 = arrow_length * 0.10, arrow_length * 0.10
            else:
                dz1, da1 = -arrow_length * 0.10, arrow_length * 0.10
                dz2, da2 = arrow_length * 0.10, -arrow_length * 0.10
            ax.plot(
                [z_value + dz1, z_value + dz2],
                [axis_value + da1, axis_value + da2],
                color="red",
                linewidth=5,
                solid_capstyle="butt",
                zorder=4,
            )
        else:
            ax.scatter([z_value], [axis_value], s=160, marker="s", color="red", zorder=4)

    def draw_projection(ax, vertical_axis, subplot_title, axis_label):
        ax.plot(beamline["z"], beamline[vertical_axis], color="#f4a12f", linewidth=1.0, zorder=1)
        non_mirrors = beamline[~beamline["name"].isin(mirror_names)]
        ax.scatter(non_mirrors["z"], non_mirrors[vertical_axis], color="black", s=12, zorder=3)

        for _, row in beamline.iterrows():
            z_value = row["z"]
            axis_value = row[vertical_axis]
            name = row["name"]
            if name in mirror_names:
                mirror = mirrors.loc[mirrors["name"] == name].iloc[0]
                draw_mirror_symbol(ax, z_value, axis_value, mirror["azimuthalAngle"], row["type"])
            y_shift = 10 if name in mirror_names else -14
            x_shift = 0 if name in mirror_names else 2
            ax.annotate(
                name,
                (z_value, axis_value),
                xytext=(x_shift, y_shift),
                textcoords="offset points",
                fontsize=7,
                ha="center" if name in mirror_names else "left",
                alpha=0.9,
            )
        ax.set_title(subplot_title, loc="left", fontsize=14)
        ax.set_xlabel("optical axis / mm")
        ax.set_ylabel(axis_label)
        ax.grid(False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_alpha(0.25)
        ax.spines["bottom"].set_alpha(0.25)
        ax.tick_params(axis="both", labelsize=9, color="0.5")

    draw_projection(ax_top, "x", "top view, sagittal beam", "x / mm")
    draw_projection(ax_side, "y", "side view, meridional beam", "y / mm")

    ax_3d.plot(
        beamline["z"],
        beamline["x"],
        beamline["y"],
        color="tab:green",
        linewidth=1.2,
        alpha=0.8,
    )
    ax_3d.scatter(
        beamline["z"],
        beamline["x"],
        beamline["y"],
        color="tab:green",
        s=28,
        depthshade=False,
    )
    for z_value, x_value, y_value, name in zip(
        beamline["z"], beamline["x"], beamline["y"], beamline["name"], strict=False
    ):
        ax_3d.text(z_value, x_value, y_value, name, fontsize=8)

    for _, mirror in mirrors.iterrows():
        dz, dx = 0.0, 0.0
        az = mirror["azimuthalAngle"]
        if az == 0.0:
            dx = arrow_length
        elif az == 180.0:
            dx = -arrow_length
        elif az == 90.0:
            dz = -arrow_length
        elif az == 270.0:
            dz = arrow_length
        ax_3d.quiver(
            mirror["z"],
            mirror["x"],
            mirror["y"],
            dz,
            dx,
            0.0,
            color="crimson",
            linewidth=1.6,
            arrow_length_ratio=0.25,
            alpha=0.85,
        )

    ax_3d.set_title("3D View")
    ax_3d.set_xlabel("z")
    ax_3d.set_ylabel("x")
    ax_3d.set_zlabel("y")
    ax_3d.view_init(elev=22, azim=-64)

    fig.suptitle(title, fontsize=16)
    fig.savefig(output_path, dpi=250, bbox_inches="tight")
    if show_plot:
        plt.show()
    plt.close(fig)
