from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from airfoil_methods import (  # noqa: E402
    build_panel_influences,
    naca_4_digit,
    prandtl_glauert,
    solve_hess_smith,
    thin_airfoil_lift,
)

geometry = naca_4_digit("0012", panels=160)
influences = build_panel_influences(geometry)
alphas = np.arange(-4, 18.01, 0.5)
solutions = [
    solve_hess_smith(geometry, float(alpha), mach=0.15, influences=influences)
    for alpha in alphas
]
with (PROJECT_ROOT / "data" / "nasa_tm_4074_m0p15_re5p97e6.csv").open() as source:
    rows = list(csv.DictReader(source))
output = {
    "alphas": alphas.tolist(),
    "geometry": [[round(float(value), 6) for value in point] for point in geometry.control_points],
    "pressureCoefficients": [
        [round(float(value), 5) for value in solution.pressure_coefficients] for solution in solutions
    ],
    "panelLift": [round(solution.lift_coefficient, 6) for solution in solutions],
    "thinLift": [round(prandtl_glauert(thin_airfoil_lift(float(alpha)), 0.15), 6) for alpha in alphas],
    "nasa": [
        {"alpha": float(row["alpha_deg"]), "cl": float(row["cl"]), "cd": float(row["cd"])}
        for row in rows
    ],
    "conditions": {"airfoil": "NACA 0012", "mach": 0.15, "reynolds": 5.97e6},
}
(PROJECT_ROOT / "demo" / "data.json").write_text(json.dumps(output, separators=(",", ":")))
print(f"Wrote {len(alphas)} panel solutions for the airfoil explorer")
