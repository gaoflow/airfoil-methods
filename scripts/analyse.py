from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

RESULTS_DIRECTORY = PROJECT_ROOT / "results"
RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
with (PROJECT_ROOT / "data" / "nasa_tm_4074_m0p15_re5p97e6.csv").open() as source:
    measurements = list(csv.DictReader(source))
alpha_measured = np.array([float(row["alpha_deg"]) for row in measurements])
cl_measured = np.array([float(row["cl"]) for row in measurements])
cd_measured = np.array([float(row["cd"]) for row in measurements])
mach = 0.15
reynolds = 5.97e6

started = time.perf_counter()
geometry = naca_4_digit("0012", panels=160)
influences = build_panel_influences(geometry)
alpha_curve = np.linspace(-6, 20, 105)
panel_solutions = [
    solve_hess_smith(geometry, alpha, mach=mach, influences=influences) for alpha in alpha_curve
]
cl_panel = np.array([solution.lift_coefficient for solution in panel_solutions])
cd_panel = np.array([solution.pressure_drag_coefficient for solution in panel_solutions])
cl_thin = np.array([prandtl_glauert(thin_airfoil_lift(alpha), mach) for alpha in alpha_curve])

measurement_panel = np.array([
    solve_hess_smith(geometry, alpha, mach=mach, influences=influences).lift_coefficient
    for alpha in alpha_measured
])
measurement_thin = np.array([prandtl_glauert(thin_airfoil_lift(alpha), mach) for alpha in alpha_measured])
linear_mask = (alpha_measured >= -4.1) & (alpha_measured <= 10.2)
nasa_slope, nasa_intercept = np.polyfit(alpha_measured[linear_mask], cl_measured[linear_mask], 1)
panel_slope, panel_intercept = np.polyfit(alpha_measured[linear_mask], measurement_panel[linear_mask], 1)
thin_slope, thin_intercept = np.polyfit(alpha_measured[linear_mask], measurement_thin[linear_mask], 1)
linear_panel_rmse = float(np.sqrt(np.mean((measurement_panel[linear_mask] - cl_measured[linear_mask]) ** 2)))
linear_thin_rmse = float(np.sqrt(np.mean((measurement_thin[linear_mask] - cl_measured[linear_mask]) ** 2)))
full_panel_rmse = float(np.sqrt(np.mean((measurement_panel - cl_measured) ** 2)))

panel_counts = [40, 80, 160, 240]
refinement_lift = []
refinement_drag = []
for panel_count in panel_counts:
    refinement_geometry = naca_4_digit("0012", panels=panel_count)
    result = solve_hess_smith(
        refinement_geometry,
        4,
        mach=mach,
        influences=build_panel_influences(refinement_geometry),
    )
    refinement_lift.append(result.lift_coefficient)
    refinement_drag.append(result.pressure_drag_coefficient)
refinement_change = abs(refinement_lift[-1] - refinement_lift[-2]) / abs(refinement_lift[-1])
analysis_seconds = time.perf_counter() - started

summary = {
    "project": "Airfoil Methods",
    "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "reference": {
        "report": "NASA TM-4074, Charles L. Ladson, 1988",
        "url": "https://ntrs.nasa.gov/citations/19880019495",
        "table": "Table I, free transition",
        "airfoil": "NACA 0012",
        "mach": mach,
        "reynolds": reynolds,
        "measurementCount": len(measurements),
        "linearRangeDegrees": [-4.1, 10.2],
    },
    "geometry": {
        "panels": geometry.lengths.size,
        "maximumThicknessRatio": float(np.ptp(geometry.points[:, 1])),
    },
    "linearLift": {
        "nasaSlopePerDegree": float(nasa_slope),
        "nasaZeroLiftDegrees": float(-nasa_intercept / nasa_slope),
        "hessSmithSlopePerDegree": float(panel_slope),
        "hessSmithZeroLiftDegrees": float(-panel_intercept / panel_slope),
        "thinAirfoilSlopePerDegree": float(thin_slope),
        "hessSmithRmse": linear_panel_rmse,
        "thinAirfoilRmse": linear_thin_rmse,
        "hessSmithSlopeRelativeError": float(abs(panel_slope - nasa_slope) / nasa_slope),
    },
    "outsideLinearRange": {
        "hessSmithFullRangeLiftRmse": full_panel_rmse,
        "measuredPeakLift": float(cl_measured.max()),
        "measuredPeakLiftAlphaDegrees": float(alpha_measured[np.argmax(cl_measured)]),
        "modelLiftAtMeasuredPeakAlpha": float(measurement_panel[np.argmax(cl_measured)]),
        "maximumModelPressureDrag": float(np.max(np.abs(cd_panel))),
        "interpretation": "Inviscid models remain nearly linear and cannot predict viscous drag or stall.",
    },
    "panelRefinementAtFourDegrees": {
        "panelCounts": panel_counts,
        "liftCoefficients": refinement_lift,
        "pressureDragCoefficients": refinement_drag,
        "relativeChange160To240": refinement_change,
    },
    "performance": {"analysisSeconds": analysis_seconds},
    "acceptance": {
        "geometryWithinTwoTenthsPercentThickness": bool(abs(np.ptp(geometry.points[:, 1]) - 0.12) < 0.002),
        "linearLiftRmseBelowPointOne": bool(linear_panel_rmse < 0.1),
        "linearSlopeWithinFifteenPercent": bool(abs(panel_slope - nasa_slope) / nasa_slope < 0.15),
        "refinementChangeBelowOnePercent": bool(refinement_change < 0.01),
        "inviscidDragBlindSpotIsExplicit": bool(
            np.max(np.abs(cd_panel)) < 0.005 and cd_measured.max() > 0.02
        ),
    },
}
(RESULTS_DIRECTORY / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n")

plt.style.use("dark_background")
accent = "#0f766e"
figure, axis = plt.subplots(figsize=(9.5, 5.4))
figure.patch.set_facecolor("#ffffff")
axis.set_facecolor("#ffffff")
axis.axvspan(-4.1, 10.2, color=accent, alpha=0.06, label="linear validation range")
axis.plot(alpha_curve, cl_thin, linestyle="--", color="#64748b", label="thin airfoil + P–G")
axis.plot(alpha_curve, cl_panel, color=accent, label="Hess–Smith + P–G")
axis.scatter(alpha_measured, cl_measured, color="#c2410c", zorder=4, label="NASA TM-4074")
axis.set(xlabel="Angle of attack [deg]", ylabel="$C_l$", title="NACA 0012 lift: model hierarchy and breakdown")
axis.grid(color="#e2e8f0", alpha=0.45)
axis.legend(frameon=False)
figure.tight_layout()
figure.savefig(RESULTS_DIRECTORY / "lift-validation.svg")
plt.close(figure)

figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.5))
figure.patch.set_facecolor("#ffffff")
for axis in axes:
    axis.set_facecolor("#ffffff")
    axis.grid(color="#e2e8f0", alpha=0.35)
for alpha, color in [(0, "#64748b"), (4, accent), (8, "#c2410c")]:
    solution = solve_hess_smith(geometry, alpha, mach=mach, influences=influences)
    upper = geometry.control_points[:, 1] >= 0
    axes[0].plot(geometry.control_points[upper, 0], solution.pressure_coefficients[upper], color=color, label=f"{alpha}° upper")
    axes[0].plot(geometry.control_points[~upper, 0], solution.pressure_coefficients[~upper], color=color, linestyle="--", alpha=0.8)
axes[0].invert_yaxis()
axes[0].set(xlabel="$x/c$", ylabel="$C_p$", title="Geometry-resolved pressure distribution")
axes[0].legend(frameon=False, ncol=1)
axes[1].plot(panel_counts, refinement_lift, "o-", color=accent, label="$C_l$ at 4°")
axes[1].axhline(refinement_lift[-1], color="#64748b", linestyle="--", alpha=0.7)
axes[1].set(xlabel="Surface panels", ylabel="$C_l$", title="Panel refinement")
axes[1].legend(frameon=False)
figure.tight_layout()
figure.savefig(RESULTS_DIRECTORY / "pressure-and-refinement.svg")
plt.close(figure)

figure, axis = plt.subplots(figsize=(9.5, 4.8))
figure.patch.set_facecolor("#ffffff")
axis.set_facecolor("#ffffff")
axis.plot(alpha_curve, np.abs(cd_panel), color=accent, label="panel pressure drag")
axis.scatter(alpha_measured, cd_measured, color="#c2410c", label="NASA wake-survey drag")
axis.set(xlabel="Angle of attack [deg]", ylabel="$C_d$", title="The explicit blind spot: an inviscid method does not predict drag")
axis.grid(color="#e2e8f0", alpha=0.45)
axis.legend(frameon=False)
figure.tight_layout()
figure.savefig(RESULTS_DIRECTORY / "drag-blind-spot.svg")
plt.close(figure)

print(json.dumps({
    "nasaSlopePerDegree": nasa_slope,
    "panelSlopePerDegree": panel_slope,
    "panelLinearRmse": linear_panel_rmse,
    "panelFullRangeRmse": full_panel_rmse,
    "refinementChange": refinement_change,
    "acceptance": summary["acceptance"],
}, indent=2))
if not all(summary["acceptance"].values()):
    raise SystemExit(1)
