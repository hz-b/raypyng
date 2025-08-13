from raypyng.vls_grating import calculate_vls_coeff

calculate_vls_coeff(alpha_g_deg=89.778, beta_g_deg=85.5733,
                        N0_lpm=2400,  # lines per mm
                        m=1, en_eV=1000,
                        source_vls_distance=81,
                        vls_image_distance=35,
                        verbose=True)