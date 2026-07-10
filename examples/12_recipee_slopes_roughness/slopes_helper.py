import matplotlib.pyplot as plt
import pandas as pd

def make_slopes_params(param_dict):
    """Build a parameter matrix-like dict from a dict of (values, base) tuples.

    For each key in ``param_dict``, this creates a list that starts with a 0,
    then the "base" value (index 1 of the input tuple), followed by one entry
    per element in that key's value-list (index 0 of the input tuple). For each
    of those elements, the current key receives the element value, while all
    other keys receive 0. The result is a dict of lists aligned across keys.

    Example:
        If ``param_dict = {"A": ([1, 2], 10), "B": ([5], 20)}``, then the
        resulting lists will have the same length for keys "A" and "B":
        - both start with ``[0, base]``
        - then for each element in "A"'s list, "A" gets that value and "B" gets 0
        - then for each element in "B"'s list, "B" gets that value and "A" gets 0

    Args:
        param_dict (dict[str, tuple[list[float], float]]): Mapping where each
            value is a tuple of (list_of_values, base_value). The function
            assumes index 0 is an iterable of numbers and indsimulation/characterizationex 1 is a single
            numeric base value.

    Returns:
        dict[str, list[float]]: A dictionary with the same keys as
        ``param_dict``. Each value is a list of numbers constructed as
        described above.

    Raises:
        TypeError: If the structure of ``param_dict`` values is not
            a tuple-like with a list at index 0.
        KeyError: If iteration over keys relies on missing entries.
    """
    new_dict = {}
    for key, value in param_dict.items():
        new_dict[key] = [0]
        new_dict[key].append(value[1])  # single value for the parameter
    for key,value_tuple in param_dict.items():
        values = value_tuple[0]
        for value in values:
            for new_key in new_dict.keys():
                if new_key == key:
                    new_dict[new_key].append(value)
                else:
                    new_dict[new_key].append(0)     
    return new_dict

def filter_df(df, cols=None, col_to_set=None, value=None):
    """Filter rows where all selected columns are zero, with one optional exception.

    Builds a boolean mask requiring all columns in ``cols`` to be equal to 0.
    If ``col_to_set`` and ``value`` are provided and ``col_to_set`` is in
    ``cols``, the condition for that specific column is replaced with
    equality to ``value`` instead of 0.

    Args:
        df (pd.DataFrame): Input DataFrame to filter.
        cols (list[str] | None): Columns to check. If None, this will raise
            since the code indexes ``df[cols]`` directly.
        col_to_set (str | None): Optional name of a column in ``cols`` whose
            equality condition should be ``== value`` instead of ``== 0``.
        value (Any | None): The value used for ``col_to_set`` comparison
            when provided.

    Returns:
        pd.DataFrame: A filtered view of ``df`` where the row-wise conditions
        hold across all specified columns.

    Raises:
        KeyError: If any column in ``cols`` is not present in ``df``.
        TypeError: If ``cols`` is None or not list-like.
    """
    mask = (df[cols] == 0)
    if col_to_set is not None and value is not None and col_to_set in cols:
        mask[col_to_set] = (df[col_to_set] == value)
    filtered_df = df[mask.all(axis=1)]
    return filtered_df

def filter_df_by_values(df, col_values, cols=None, atol=1e-8, debug=False):
    """Filter rows by exact equality for specified {column: value} pairs.

    Note:
        This function performs exact equality checks (``==``) and ignores
        ``cols`` and ``atol`` parameters. Despite the name, no tolerance-based
        matching is applied. When ``debug`` is True, it prints simple counts
        of matches for each specified column and the final number of rows.

    Args:
        df (pd.DataFrame): Input DataFrame to filter.
        col_values (dict[str, Any]): Mapping of column names to exact values
            to match. Rows must satisfy all pairs to be kept.
        cols (Any, optional): Ignored. Present but not used.
        atol (float, optional): Ignored. Present but not used.
        debug (bool): If True, prints counts of matches and final row count.

    Returns:
        pd.DataFrame: A filtered DataFrame containing only rows that satisfy
        all exact equality checks in ``col_values``.

    Raises:
        KeyError: If a column in ``col_values`` does not exist in ``df``.
    """
    mask = pd.Series([True] * len(df), index=df.index)
    if debug:
        print("DEBUG: Unique values and matches per column:")
    for col, val in col_values.items():
        count = (df[col] == val).sum()
        df = df[df[col] == val]
        if debug:
            print(f"{col} looking for {val} | found: {count} matches")
    if debug:
        print(f"DEBUG: Final number of matching rows: {mask.sum()}")
    return df

def extract_and_plot(dataframe, axs, label):
    """Extract selected columns and plot four diagnostics on given axes.

    Plots the following series from ``dataframe``:
      - ``axs[0]``: photon energy vs transmitted bandwidth
      - ``axs[1]``: photon energy vs resolving power (energy/bandwidth)
      - ``axs[2]``: photon energy vs horizontal focus FWHM in micrometers
      - ``axs[3]``: photon energy vs vertical focus FWHM in micrometers

    Expected columns:
      - ``'CPMU20.photonEnergy'``
      - ``'PhotonFlux1'`` (extracted but not plotted)
      - ``'Bandwidth'``
      - ``'VerticalFocusFWHM'`` (meters, converted to micrometers)
      - ``'HorizontalFocusFWHM'`` (meters, converted to micrometers)

    Args:
        dataframe (pd.DataFrame): Source data containing the required columns.
        axs (Sequence[matplotlib.axes.Axes]): A sequence with at least
            four Matplotlib Axes to plot into.
        label (str): Label used in the legend for all four plotted lines.

    Returns:
        None

    Raises:
        KeyError: If any of the expected columns are missing from ``dataframe``.
        IndexError: If ``axs`` does not contain at least four axes.
    """
    energy = dataframe['CPMU20.photonEnergy']
    abs_flux = dataframe['PhotonFlux1']
    bw = dataframe['Bandwidth']
    vfoc = dataframe['VerticalFocusFWHM']*1000  # convert to um
    hfoc = dataframe['HorizontalFocusFWHM']*1000  # convert to um
    axs[0].plot(energy,bw, label=f'{label}')
    axs[1].plot(energy,energy/bw, label=f'{label}')
    axs[2].plot(energy,hfoc, label=f'{label}')
    axs[3].plot(energy,vfoc, label=f'{label}')

def decorate_and_save_plot(axs, title=None, savepath=None, showplot=False):
    """Decorate a 4-panel figure with labels, titles, grid, and save to file.

    This function configures axis labels, titles, and grids for four axes:
    bandwidth, resolving power, horizontal focus, and vertical focus. It then
    applies a figure-level title, tight layout, saves the figure to
    ``savepath``, optionally shows it, and finally closes the figure.

    Args:
        axs (Sequence[matplotlib.axes.Axes]): Sequence of four Axes objects in
            the order expected by the function (bandwidth, resolving power,
            horizontal focus, vertical focus).
        title (str | None): Figure-level title passed to ``plt.suptitle``.
        savepath (str | bytes | os.PathLike | None): File path where the
            figure will be saved via ``plt.savefig``. If None, saving will
            fail.
        showplot (bool): If True, calls ``plt.show()`` before closing.

    Returns:
        None

    Raises:
        ValueError: If ``savepath`` is None or invalid for ``plt.savefig``.
        IndexError: If ``axs`` does not contain at least four axes.
    """
    # BANDWIDTH
    ax = axs[0]
    ax.set_xlabel('Energy [eV]')
    ax.set_ylabel('Transmitted Bandwidth [eV]')
    ax.set_title('Transmitted bandwidth (tbw)')
    ax.grid(which='both', axis='both')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    # BANDWIDTH
    ax = axs[1]
    ax.set_xlabel('Energy [eV]')
    ax.set_ylabel('Resolving Power [a.u.]')
    ax.set_title('Resolving Power')
    ax.grid(which='both', axis='both')

    # HORIZONTAL FOCUS
    ax = axs[2]
    ax.set_xlabel('Energy [eV]')
    ax.set_ylabel('Focus Size [um]')
    ax.set_title('Horizontal focus')
    ax.grid(which='both', axis='both')
    # ax.set_ylim(4, 16)


    # VERTICAL FOCUS
    ax = axs[3]
    ax.set_xlabel('Energy [eV]')
    ax.set_ylabel('Focus Size [um]')
    ax.set_title('Vertical focus')
    ax.grid(which='both', axis='both')
    # ax.set_ylim(4, 16)

    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(savepath)
    if showplot:
        plt.show()
    plt.close()


