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
