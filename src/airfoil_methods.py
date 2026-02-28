from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class PanelGeometry:
    points: FloatArray
    control_points: FloatArray
    tangents: FloatArray
    normals: FloatArray
    lengths: FloatArray


@dataclass(frozen=True)
class PanelSolution:
    alpha_degrees: float
    lift_coefficient: float
    pressure_drag_coefficient: float
    moment_coefficient_quarter_chord: float
    pressure_coefficients: FloatArray
    tangential_velocity: FloatArray
    source_strengths: FloatArray
    vortex_sheet_strength: float


def naca_4_digit(code: str = "0012", panels: int = 160) -> PanelGeometry:
    """Return cosine-spaced NACA four-digit geometry ordered counter-clockwise."""
    if len(code) != 4 or not code.isdigit():
        raise ValueError("NACA code must contain four digits")
    if panels < 20 or panels % 2:
        raise ValueError("panel count must be even and at least 20")
    maximum_camber = int(code[0]) / 100
    camber_location = int(code[1]) / 10
    thickness = int(code[2:]) / 100
    theta = np.linspace(0, np.pi, panels // 2 + 1)
    x = (1 - np.cos(theta)) / 2
    yt = 5 * thickness * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1036 * x**4
    )
    yc = np.zeros_like(x)
    slope = np.zeros_like(x)
    if maximum_camber > 0:
        forward = x < camber_location
        yc[forward] = maximum_camber / camber_location**2 * (
            2 * camber_location * x[forward] - x[forward] ** 2
        )
        slope[forward] = 2 * maximum_camber / camber_location**2 * (camber_location - x[forward])
        aft = ~forward
        yc[aft] = maximum_camber / (1 - camber_location) ** 2 * (
            1 - 2 * camber_location + 2 * camber_location * x[aft] - x[aft] ** 2
        )
        slope[aft] = 2 * maximum_camber / (1 - camber_location) ** 2 * (camber_location - x[aft])
    surface_angle = np.arctan(slope)
    upper = np.column_stack((x - yt * np.sin(surface_angle), yc + yt * np.cos(surface_angle)))
    lower = np.column_stack((x + yt * np.sin(surface_angle), yc - yt * np.cos(surface_angle)))
    points = np.vstack((upper[::-1], lower[1:]))
    vectors = np.diff(points, axis=0)
    lengths = np.linalg.norm(vectors, axis=1)
    tangents = vectors / lengths[:, None]
    normals = np.column_stack((tangents[:, 1], -tangents[:, 0]))
    controls = (points[:-1] + points[1:]) / 2
    return PanelGeometry(points, controls, tangents, normals, lengths)


def thin_airfoil_lift(alpha_degrees: float, zero_lift_degrees: float = 0) -> float:
    return float(2 * np.pi * np.deg2rad(alpha_degrees - zero_lift_degrees))


def prandtl_glauert(value: float, mach: float) -> float:
    if not 0 <= mach < 1:
        raise ValueError("Prandtl-Glauert correction requires 0 <= Mach < 1")
    return float(value / np.sqrt(1 - mach**2))


def build_panel_influences(
    geometry: PanelGeometry, quadrature_order: int = 12
) -> tuple[FloatArray, FloatArray]:
    panel_count = geometry.lengths.size
    source_velocity = np.zeros((panel_count, panel_count, 2))
    vortex_velocity = np.zeros((panel_count, panel_count, 2))
    nodes, weights = np.polynomial.legendre.leggauss(quadrature_order)
    for source_index in range(panel_count):
        start = geometry.points[source_index]
        vector = geometry.points[source_index + 1] - start
        samples = start + ((nodes + 1) / 2)[:, None] * vector
        weighted_length = weights * geometry.lengths[source_index] / 2
        for target_index in range(panel_count):
            if source_index == target_index:
                continue
            displacement = geometry.control_points[target_index] - samples
            radius_squared = np.sum(displacement**2, axis=1)
            kernel = displacement / (2 * np.pi * radius_squared[:, None])
            source_velocity[target_index, source_index] = np.sum(kernel * weighted_length[:, None], axis=0)
            vortex_kernel = np.column_stack((-displacement[:, 1], displacement[:, 0])) / (
                2 * np.pi * radius_squared[:, None]
            )
            vortex_velocity[target_index, source_index] = np.sum(
                vortex_kernel * weighted_length[:, None], axis=0
            )
    indices = np.arange(panel_count)
    source_velocity[indices, indices] = 0.5 * geometry.normals
    vortex_velocity[indices, indices] = 0.5 * geometry.tangents
    return source_velocity, vortex_velocity


def solve_hess_smith(
    geometry: PanelGeometry,
    alpha_degrees: float,
    mach: float = 0,
    influences: tuple[FloatArray, FloatArray] | None = None,
) -> PanelSolution:
    """Solve constant-source panels plus one global vortex-sheet strength."""
    source_velocity, vortex_velocity = influences or build_panel_influences(geometry)
    panel_count = geometry.lengths.size
    flow_angle = np.deg2rad(alpha_degrees)
    freestream = np.array([np.cos(flow_angle), np.sin(flow_angle)])
    source_normal = np.einsum("ijk,ik->ij", source_velocity, geometry.normals)
    global_vortex_velocity = vortex_velocity.sum(axis=1)
    global_vortex_normal = np.sum(global_vortex_velocity * geometry.normals, axis=1)
    system = np.empty((panel_count + 1, panel_count + 1))
    right_hand_side = np.empty(panel_count + 1)
    system[:panel_count, :panel_count] = source_normal
    system[:panel_count, -1] = global_vortex_normal
    right_hand_side[:panel_count] = -(geometry.normals @ freestream)

    source_tangent = np.einsum("ijk,ik->ij", source_velocity, geometry.tangents)
    global_vortex_tangent = np.sum(global_vortex_velocity * geometry.tangents, axis=1)
    trailing_panels = (0, panel_count - 1)
    system[-1, :panel_count] = source_tangent[trailing_panels[0]] + source_tangent[trailing_panels[1]]
    system[-1, -1] = global_vortex_tangent[trailing_panels[0]] + global_vortex_tangent[trailing_panels[1]]
    right_hand_side[-1] = -freestream @ (
        geometry.tangents[trailing_panels[0]] + geometry.tangents[trailing_panels[1]]
    )
    strengths = np.linalg.solve(system, right_hand_side)
    source_strengths = strengths[:-1]
    vortex_strength = float(strengths[-1])
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        tangential_velocity = (
            geometry.tangents @ freestream
            + source_tangent @ source_strengths
            + global_vortex_tangent * vortex_strength
        )
    if not np.isfinite(tangential_velocity).all():
        raise FloatingPointError("panel solution produced non-finite surface velocity")
    pressure_coefficients = 1 - tangential_velocity**2
    if mach:
        pressure_coefficients /= np.sqrt(1 - mach**2)

    pressure_force = -np.sum(
        pressure_coefficients[:, None] * geometry.normals * geometry.lengths[:, None], axis=0
    )
    drag_direction = freestream
    lift_direction = np.array([-freestream[1], freestream[0]])
    drag = float(pressure_force @ drag_direction)
    lift = float(pressure_force @ lift_direction)
    relative = geometry.control_points - np.array([0.25, 0])
    force_panels = -pressure_coefficients[:, None] * geometry.normals * geometry.lengths[:, None]
    moment = float(np.sum(relative[:, 0] * force_panels[:, 1] - relative[:, 1] * force_panels[:, 0]))
    return PanelSolution(
        alpha_degrees,
        lift,
        drag,
        moment,
        pressure_coefficients,
        tangential_velocity,
        source_strengths,
        vortex_strength,
    )
