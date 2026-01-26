# Computing the cff for a Fixed Focus with a Plane VLS Grating  
*(notes and lessons learned during the implementation)*

This note documents what was done to compute the cff (cos β / cos α) required to keep the focus position fixed while scanning photon energy in a plane VLS-grating monochromator, following Reininger & de Castro (NIM A 538, 2005). It also highlights the non-obvious pitfalls encountered along the way.

The final result is the function `cff_for_fixed_focus`, which returns the physically correct cff as a function of photon energy for a given VLS grating and geometry.

---

## 1. What problem is being solved

When scanning photon energy with a plane VLS grating, the image plane (typically the exit slit, or the detector) will generally move unless the included angle is adjusted. The goal is therefore:

> For each photon energy, compute the value of `cff` such that the defocus term vanishes, so the focus position does not move.

This is equivalent to enforcing the condition `M20 = 0` in the optical path function.

---

## 2. Parallel-beam geometry: the `r = 0` condition

One of the first and most important assumptions is related to the geometry.

The paper explicitly states that for the SRC beamline the grating is illuminated by a *collimated (parallel) beam*. In this case:

- The source distance rA is effectively infinite
- The ratio r = rB / rA must be set to **zero**

---

## 3. Groove density vs groove label (a frequent source of confusion)

Another major source of confusion is the meaning of the quantity expanded in equation (2) of the paper.

- The paper writes an expansion for `n(w)`
- Here, `n(w)` is **not** the groove density
- It is the **groove label (groove number)**

The groove density is the derivative of the groove label:

- Groove label → integrated quantity
- Groove density → derivative of the groove label

This matters because:

- SHADOW and ray-tracing codes use **groove density**

---

## 4. Equation (9): two square roots, two hidden choices

Equation (9) in the paper contains *two different square roots*, and each of them hides a choice.

The inner square root originates from solving the grating equation and geometry together.

- Algebraically, it has a ± ambiguity
- Physically, only **one sign corresponds to the intended geometry**

In practice, equation (9) could be rewritten as:

```python
c = ± sqrt((L ± 4*A2/A0 * sqrt(S))/D)
```

* The correct choice of the inner sign of the square root of S is minus
* The outer square root, determining c, is always positive

