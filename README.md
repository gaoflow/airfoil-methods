# Airfoil Methods — model hierarchy against NASA measurements

This study implements three low-order aerodynamic levels for a NACA 0012 section and tests what each can—and cannot—predict against public wind-tunnel data:

1. incompressible thin-airfoil theory;
2. Prandtl–Glauert compressibility correction at $M=0.15$;
3. a geometry-resolved Hess–Smith source/vortex panel method with cosine spacing and a trailing-edge Kutta condition.

The validation source is Table I of Charles L. Ladson's NASA TM-4074: free-transition NACA 0012 measurements at $M=0.15$ and $Re=5.97\times10^6$. The committed CSV is a direct transcription of the public table and keeps the report URL beside every generated result.

## Reproduce

Requires Python 3.11+, NumPy, and Matplotlib.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/analyse.py
```

The analysis writes `results/analysis.json` and three SVG figures, then exits nonzero unless the geometry, linear-lift agreement, panel-refinement, and explicitly declared inviscid-drag checks pass.

## Verified results

- NASA linear-range slope: 0.10684 per degree from $-4.1^\circ$ to $10.2^\circ$.
- Hess–Smith + Prandtl–Glauert slope: 0.12162 per degree, 13.83% high.
- Linear-range lift RMSE: 0.0824 for the panel model.
- 160-to-240-panel change in $C_l$ at $4^\circ$: 0.0307%.
- Full-range lift RMSE rises to 0.225 because the inviscid models continue linearly through the measured stall region.
- The panel method's near-zero pressure drag is shown beside NASA wake-survey drag; it is a model limitation, not a successful drag prediction.

The simplest thin-airfoil result is closer to the measured integral lift slope than the thickness-resolving panel result. The panel method earns its complexity by providing surface $C_p$ and geometry sensitivity—not by universally improving every scalar metric.

## Structure

- `src/airfoil_methods.py` — NACA geometry, thin-airfoil theory, Prandtl–Glauert correction, and Hess–Smith solver.
- `data/` — transcribed NASA TM-4074 measurement table.
- `tests/` — geometry, symmetry, lift-slope, d'Alembert, and panel-refinement contracts.
- `scripts/analyse.py` — validation, acceptance gates, and evidence generation.
- `results/` — committed machine-readable metrics and figures.

---

## Portfolio case study

Read the [full engineering case study](https://binggao.dev/projects/airfoil-methods/).
