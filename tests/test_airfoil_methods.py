import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from airfoil_methods import (  # noqa: E402
    build_panel_influences,
    naca_4_digit,
    prandtl_glauert,
    solve_hess_smith,
    thin_airfoil_lift,
)


class AirfoilMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry = naca_4_digit("0012", panels=80)
        cls.influences = build_panel_influences(cls.geometry)

    def test_naca_0012_is_closed_symmetric_and_twelve_percent_thick(self):
        np.testing.assert_allclose(self.geometry.points[0], self.geometry.points[-1], atol=1e-12)
        thickness = np.ptp(self.geometry.points[:, 1])
        self.assertAlmostEqual(thickness, 0.12, delta=0.002)
        self.assertAlmostEqual(np.sum(self.geometry.lengths * self.geometry.normals[:, 0]), 0, places=10)
        self.assertAlmostEqual(np.sum(self.geometry.lengths * self.geometry.normals[:, 1]), 0, places=10)

    def test_zero_angle_has_zero_lift_and_negligible_pressure_drag(self):
        result = solve_hess_smith(self.geometry, 0, influences=self.influences)
        self.assertAlmostEqual(result.lift_coefficient, 0, places=10)
        self.assertLess(abs(result.pressure_drag_coefficient), 0.001)

    def test_panel_lift_curve_is_linear_and_near_thin_airfoil_slope(self):
        alphas = np.array([-4, -2, 0, 2, 4])
        lifts = np.array([
            solve_hess_smith(self.geometry, alpha, influences=self.influences).lift_coefficient
            for alpha in alphas
        ])
        slope = np.polyfit(np.deg2rad(alphas), lifts, 1)[0]
        self.assertAlmostEqual(lifts[0], -lifts[-1], places=10)
        self.assertLess(abs(slope - 2 * np.pi) / (2 * np.pi), 0.15)

    def test_panel_refinement_changes_four_degree_lift_by_less_than_one_percent(self):
        coarse = solve_hess_smith(self.geometry, 4, influences=self.influences).lift_coefficient
        fine_geometry = naca_4_digit("0012", panels=160)
        fine = solve_hess_smith(
            fine_geometry, 4, influences=build_panel_influences(fine_geometry)
        ).lift_coefficient
        self.assertLess(abs(fine - coarse) / abs(fine), 0.01)

    def test_analytical_corrections_enforce_domain(self):
        self.assertAlmostEqual(thin_airfoil_lift(4), 2 * np.pi * np.deg2rad(4))
        self.assertGreater(prandtl_glauert(1, 0.3), 1)
        with self.assertRaises(ValueError):
            prandtl_glauert(1, 1)


if __name__ == "__main__":
    unittest.main()
