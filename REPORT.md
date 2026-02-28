# Airfoil Methods: where low-order models earn and lose trust

## Objective

A method hierarchy should expose capability boundaries, not imply that more machinery always gives a better answer. This study implements analytical and panel methods for the NACA 0012 and compares them with one internally consistent public wind-tunnel series. It asks four concrete questions:

1. Does the implementation reproduce symmetry and the expected linear lift scale?
2. Does geometry-resolved potential flow converge with panel refinement?
3. How closely do the models match measured lift in the attached-flow range?
4. Which requested outputs are structurally outside an inviscid model's scope?

## Public reference

The measurements come from Table I of NASA TM-4074, *Effects of Independent Variation of Mach and Reynolds Numbers on the Low-Speed Aerodynamic Characteristics of the NACA 0012 Airfoil Section*, by Charles L. Ladson (1988) [1]. The selected series uses free transition, $M=0.15$, and $Re=5.97\times10^6$. NASA Langley's pressure tunnel provided lift and pitching moment from integrated surface pressures and drag from a wake survey. The report states repeatability of $C_d$ within 0.0002, normal-force coefficient within 0.004, and moment coefficient within 0.0002 for repeated zero-angle points.

Sixteen tabulated points from $-4.05^\circ$ through $17.35^\circ$ are transcribed into the repository. No plotted curve was digitised and no values from a different Reynolds number or transition condition were merged.

## Level 1: thin-airfoil theory

For a symmetric airfoil,

$$C_l=2\pi\alpha,$$

with $\alpha$ in radians. At $M=0.15$, the Prandtl–Glauert factor $1/\sqrt{1-M^2}$ is applied. This level has almost no geometric resolution beyond camber and zero-lift angle. It predicts a linear slope but no stall, viscous drag, or detailed surface loading.

## Level 2: geometry-resolved panel method

The NACA four-digit equation generates a closed 12%-thick profile with cosine-spaced surface points. The Hess–Smith formulation assigns one constant source strength to every panel and one global vortex-sheet strength. Collocation enforces zero normal velocity; the sum of upper and lower trailing-edge tangential velocities enforces the Kutta condition.

Influence integrals use 12-point Gauss–Legendre quadrature. Analytical half-jump terms handle each panel's self influence. Surface velocity gives

$$C_p=1-\left(V_t/V_\infty\right)^2,$$

followed by the same Prandtl–Glauert scaling. Integrating pressure over the surface gives lift, pressure drag, and quarter-chord moment.

This level adds inspectable $C_p(x)$ and geometry sensitivity. It still solves inviscid, irrotational flow outside the prescribed vortex sheet.

## Verification before data comparison

Five behavioral tests guard the implementation:

- the NACA 0012 polygon closes, is symmetric, and is within 0.2 percentage points of 12% thickness;
- zero angle gives zero lift to numerical precision;
- zero-angle pressure drag remains below 0.001;
- the small-angle lift slope is within 15% of $2\pi$ per radian;
- doubling from 80 to 160 panels changes $C_l$ at $4^\circ$ by less than 1%.

The production refinement sequence uses 40, 80, 160, and 240 panels. The 160-to-240 change at $4^\circ$ is 0.0307%, so the subsequent comparison uses 160 panels.

## Measurement comparison

A least-squares fit from $-4.1^\circ$ to $10.2^\circ$ gives:

| Quantity | NASA TM-4074 | Thin airfoil + P–G | Hess–Smith + P–G |
|---|---:|---:|---:|
| Lift slope, per degree | 0.10684 | 0.11092 | 0.12162 |
| Slope error | — | 3.81% | 13.83% |
| Linear-range $C_l$ RMSE | — | 0.0226 | 0.0824 |

The analytical line is closer to measured integral lift than the panel model. That is not a reason to discard the panel method: thickness-resolving potential flow supplies a surface pressure distribution, but its inviscid assumptions increase the lift slope relative to the experiment. The result is a warning against ranking methods on complexity alone.

Across the full tabulated range, panel-model lift RMSE rises to 0.225. NASA's measured $C_l$ reaches 1.660 at $17.35^\circ$; the inviscid solution continues its nearly linear rise and returns 2.085. Separation and stall are absent from the governing model.

## Drag is a declared blind spot

NASA drag rises from roughly 0.0065 near zero lift to 0.0275 at $17.35^\circ$. The panel result remains near zero apart from discretisation error. This is d'Alembert's paradox in the delivered evidence, not agreement.

Reporting the near-zero curve beside the wake-survey data prevents a common presentation failure: treating an unavailable viscous output as a weakly accurate one. Drag prediction requires at least a boundary-layer/transition model or a viscous CFD method, and stall requires separation physics beyond this hierarchy.

## Acceptance and limits

The executable study exits nonzero unless:

- geometry thickness is within 0.002 of 0.12;
- linear-range panel $C_l$ RMSE is below 0.1;
- panel lift slope is within 15% of the measured slope;
- the 160-to-240-panel $C_l$ change is below 1%;
- near-zero inviscid pressure drag and greater-than-0.02 measured drag coexist, proving that the blind spot remains explicit.

The comparison is one airfoil, one Mach number, one Reynolds number, and one transition condition. It does not validate other geometries, laminar bubbles, roughness, or post-stall flow. Its purpose is to demonstrate model selection, implementation checks, measurement provenance, and honest failure boundaries.

## Reference

1. Ladson, C. L. (1988). *Effects of Independent Variation of Mach and Reynolds Numbers on the Low-Speed Aerodynamic Characteristics of the NACA 0012 Airfoil Section*. NASA TM-4074. https://ntrs.nasa.gov/citations/19880019495
