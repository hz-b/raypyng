import math
from typing import Optional

import numpy as np


def calculate_vls_coeff(
    alpha_g_deg=89.778,
    beta_g_deg=85.5733,
    N0_lpm=2400.0,
    m=1,
    en_eV=1000.0,
    source_vls_distance=81.0,
    vls_image_distance=35.0,
    verbose=True,
):
    """
    Calculate B2–B5 coefficients for a Variable Line Spacing (VLS) grating
    using normal incidence and diffraction angles.

    The coefficients correspond to terms in the groove density expansion:
        n(z) = N0 * (1 + 2*B2*z + 3*B3*z^2 + 4*B4*z^3 + 5*B5*z^4 + ...)
    where:
        - B2  : Cancels primary defocus
        - B3  : Cancels primary coma
        - B4  : Reduces spherical aberration
        - B5  : Cancels secondary coma

    Parameters
    ----------
    alpha_g_deg : float
        Normal incidence angle [degrees from the grating normal].
    beta_g_deg : float
        Normal diffraction (exit) angle [degrees from the grating normal].
    N0_lpm : float
        Central groove density [lines/mm].
    m : int
        Diffraction order (positive for same side, negative for opposite side).
    en_eV : float
        Photon energy [eV].
    source_vls_distance : float
        Source-to-grating distance [m].
    vls_image_distance : float
        Grating-to-image distance [m].
    verbose : bool
        If True, prints a detailed recap of input parameters and results.

    Returns
    -------
    B2 : float
        Dimensionless coefficient for defocus correction.
    B3 : float
        Dimensionless coefficient for primary coma correction.
    B4 : float
        Dimensionless coefficient for spherical aberration correction.
    B5 : float
        Dimensionless coefficient for secondary coma correction.
    """
    # Distances & wavelength in mm
    r = source_vls_distance * 1000.0
    rprime = vls_image_distance * 1000.0
    lam_mm = (1239.841984 / en_eV) * 1e-6  # nm → mm

    # Convert to radians (already grazing-from-surface)
    alpha = np.deg2rad(alpha_g_deg)
    beta = np.deg2rad(beta_g_deg)

    # B2 (defocus cancellation)
    a = (np.cos(alpha) ** 2) / r
    b = (np.cos(beta) ** 2) / rprime
    n1 = (a + b) / (m * lam_mm)  # [1/mm^2]
    B2 = n1 / (2.0 * N0_lpm)

    # B3 (primary coma cancellation)
    term_a = (np.cos(alpha) ** 2) * np.tan(alpha) / (r**2)
    term_b = (np.cos(beta) ** 2) * np.tan(beta) / (rprime**2)
    n2 = (term_a + term_b) / (m * lam_mm)  # [1/mm^3]
    B3 = n2 / (3.0 * N0_lpm)

    # B4  (spherical term)
    n3 = (np.cos(alpha) ** 2) * (np.tan(alpha) ** 2) / (m * lam_mm * r**3) + (
        np.cos(beta) ** 2
    ) * (np.tan(beta) ** 2) / (
        m * lam_mm * rprime**3
    )  # [1/mm^4]
    B4 = n3 / (4.0 * N0_lpm)

    # n4 → B5  (secondary coma term)
    n4 = (np.cos(alpha) ** 2) * (np.tan(alpha) ** 3) / (m * lam_mm * r**4) + (
        np.cos(beta) ** 2
    ) * (np.tan(beta) ** 3) / (
        m * lam_mm * rprime**4
    )  # [1/mm^5]
    B5 = n4 / (5.0 * N0_lpm)

    if verbose:
        print("=== VLS Grating Parameters Recap ===")
        print(f"Photon energy :      {en_eV} [eV]")
        print(f"Wavelength :         {lam_mm:.6e} [mm]")
        print(f"Line density N0 :    {N0_lpm} [l/mm]")
        print(f"Diffraction order:   {m}")
        print(f"Alpha_g :            {alpha_g_deg} [deg]")
        print(f"Beta_g :             {beta_g_deg} [deg]")
        print(f"Source distance r :  {r/1000:.2f} [m]")
        print(f"Image distance r' :  {rprime/1000:.2f} [m]")
        print("--- Results ---")
        print(f"B2 - defocus:        {B2:.6e}")
        print(f"B3 - primary coma:   {B3:.6e}")
        print(f"B4 - spherical:      {B4:.6e}")
        print(f"B5 - secondary coma: {B5:.6e}")
        print("===============================")

    return B2, B3, B4, B5


def N1_to_b2(N1, k):
    """
    Convert SHADOW N1 coefficient to paper b2 coefficient.

    Parameters
    ----------
    N1 : float
        SHADOW linear coefficient [lines / cm^2]
    k : float
        Central groove density [lines / mm]

    Returns
    -------
    b2 : float
        VLS coefficient b2 [1 / m]
    """
    N1_l_per_mm2 = N1 / 100.0
    return N1_l_per_mm2 / (2.0 * k)


def cff_for_fixed_focus(
    B2: float,
    en_eV: float,
    N0_lpmm: float,
    source_vls_distance_m: float = 81.0,
    vls_image_distance_m: float = 35.0,
    r_override: Optional[float] = None,
    verbose: bool = False,
) -> float:
    """
    Compute the CFF (c-value) required to keep the image (focus) position fixed
    when scanning photon energy with a plane VLS grating.

    This function determines the value of the included-angle parameter

        c = cos(beta) / cos(alpha)

    such that the *defocus term* of the optical path function vanishes
    (M_20 = 0). Physically, this enforces that the focal plane (e.g. exit slit,
    detector) remains at a fixed longitudinal position while the photon energy is varied.

    The calculation implements the closed-form solution derived by
    Reininger & de Castro (NIM A 538, 2005) for plane variable-line-spacing
    (VLS) gratings. It is applicable to both:

    - collimated-beam geometries (r = rB / rA = 0), as used in the SRC beamline,
    - finite-distance geometries (r > 0), as used in LNLS-type designs.

    In practice, this function answers the question:

        “How must the CFF be adjusted as a function of photon energy
         so that the focus does not move?”

    Parameters
    ----------
    B2 : float
        VLS defocus coefficient in units of 1/mm.
        This corresponds to the quadratic term in the groove-density expansion.
    en_eV : float
        Photon energy in electron-volts.
    N0_lpmm : float
        Central groove density of the grating in lines/mm.
    source_vls_distance_m : float, optional
        Distance from source (or virtual source) to the grating, in meters.
        Used only if `r_override` is None.
    vls_image_distance_m : float, optional
        Distance from the grating to the image plane (exit slit), in meters.
    r_override : float, optional
        If provided, explicitly sets r = rB / rA.
        Use r_override = 0.0 for collimated-beam operation.
    verbose : bool, optional
        If True, print intermediate optical quantities for diagnostics.

    Returns
    -------
    float
        The physically valid CFF (c > 1) that maintains a fixed focus position.
        Returns NaN if no real solution exists for the given parameters.

    Notes
    -----
    - The function automatically selects the physical algebraic branch
      corresponding to beta > alpha (c > 1).
    - All internal calculations are performed in SI units.
    - The returned CFF is dimensionless.
    """

    # --------------------------
    # Unit conversions & basics
    # --------------------------
    k_l_per_m = float(N0_lpmm) * 1000.0  # lines / m
    wavelength_m = 1239.841984e-9 / float(en_eV)  # photon wavelength in meters
    rA = float(source_vls_distance_m)
    rB = float(vls_image_distance_m)
    b2_1_per_m = float(B2) * 1000.0  # convert B2 (1/mm) -> b2 (1/m)

    # compute r (allow override for e.g. collimated case r=0)
    if r_override is not None:
        r = float(r_override)
    else:
        # protect against division by zero
        r = (rB / rA) if (rA != 0.0) else 0.0

    # dimensionless combinations
    A0 = k_l_per_m * wavelength_m
    if A0 == 0.0:
        if verbose:
            print("A0 (k*lambda) is zero -> no physical solution. Returning NaN.")
        return np.nan

    A2 = k_l_per_m * wavelength_m * rB * b2_1_per_m

    # --------------------------
    # Build L, S, DEN (line_1, S, line_3)
    # --------------------------
    A2_over_A0 = A2 / A0

    # L term
    line_1 = 2.0 * A2 + 4.0 * (A2_over_A0**2) + (4.0 + 2.0 * A2 - A0**2) * r

    # inner sqrt for S
    inner_S = (1.0 + r) ** 2 + 2.0 * A2 * (1.0 + r) - (A0**2) * r
    if inner_S < 0.0:
        if verbose:
            print("Inner S argument negative -> no real S. Returning NaN.")
            print(f"inner_S = {inner_S:.6e}; A0={A0:.6e}, A2={A2:.6e}, r={r:.6e}")
        return np.nan
    S = math.sqrt(inner_S)

    # denominator
    line_3 = -4.0 + (A0**2) + 4.0 * A2 + 4.0 * (A2_over_A0**2)
    if line_3 == 0.0:
        if verbose:
            print("Denominator (line_3) is exactly zero -> singular. Returning NaN.")
        return np.nan

    # Numerators: we compute both conceptual pieces for clarity
    # line_2 (the - prefactor times S) is useful for diagnostics
    # but not directly used in final selection here
    line_2 = -4.0 * A2_over_A0 * S

    # final ratio selecting the '+' algebraic branch
    numerator_plus = line_1 + 4.0 * A2_over_A0 * S
    ratio = numerator_plus / line_3

    # check final ratio is non-negative to take sqrt
    if ratio < 0.0 or np.isnan(ratio):
        if verbose:
            print(
                "Final ratio (numerator_plus / line_3) is negative or NaN -> no real c. \
                Returning NaN."
            )
            print(
                f"ratio = {ratio:.6e}; numerator_plus = {numerator_plus:.6e}; line_3 = {line_3:.6e}"
            )
        return np.nan

    c = math.sqrt(ratio)

    # --------------------------
    # Verbose diagnostics (if requested)
    # --------------------------
    if verbose:
        print("=== CFF from B2 Calculation ===")
        print(f"Photon energy :         {en_eV} [eV]")
        print(f"Wavelength :            {wavelength_m:.6e} [m]")
        print(f"Line density N0 :       {k_l_per_m:.6e} [l/m]  ({N0_lpmm} l/mm)")
        print(f"Source distance rA :    {rA:.2f} [m]")
        print(f"Image distance rB :     {rB:.2f} [m]")
        print(f"r (rB/rA or override) : {r:.6e}")
        print(f"B2 (input) :            {B2:.6e} [1/mm]  -> b2 = {b2_1_per_m:.6e} [1/m]")
        print(f"A0 = k*lambda :        {A0:.6e}")
        print(f"A2 = k*lambda*rB*b2 :  {A2:.6e}")
        print(f"line_1 (L) :           {line_1:.6e}")
        print(f"S (sqrt arg) :         {S:.6e}  (inner_S = {inner_S:.6e})")
        print(f"line_2 :                {line_2:.6e}")
        print(f"line_3 (DEN) :         {line_3:.6e}")
        print(f"numerator_plus :       {numerator_plus:.6e}")
        print(f"ratio (c^2) :         {ratio:.6e}")
        print(f"Calculated CFF (c) :   {c:.6e}")
        print("===============================")

    return float(c)
