import unittest

from dc_bias import calculate

REF = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.7)


class ReferenceCaseTest(unittest.TestCase):
    def test_reference_case_is_active(self):
        r = calculate(**REF)
        self.assertEqual(r.region, "active")
        self.assertAlmostEqual(r.vth, 2.163934, places=6)
        self.assertAlmostEqual(r.rth, 18032.7869, places=3)
        self.assertAlmostEqual(r.ib * 1e6, 12.29858, places=4)
        self.assertAlmostEqual(r.ic * 1e3, 1.229858, places=5)
        self.assertAlmostEqual(r.ie * 1e3, 1.242157, places=5)
        self.assertAlmostEqual(r.ve, 1.242157, places=5)
        self.assertAlmostEqual(r.vb, 1.942157, places=5)
        self.assertAlmostEqual(r.vc, 9.294312, places=5)
        self.assertAlmostEqual(r.vce, 8.052155, places=5)
        self.assertEqual(r.warnings, ())


class ValidationTest(unittest.TestCase):
    def test_rejects_non_positive_resistance(self):
        for key in ("r1", "r2", "rc", "re"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                calculate(**{**REF, key: 0.0})

    def test_rejects_non_positive_beta(self):
        with self.assertRaises(ValueError):
            calculate(**{**REF, "beta": 0.0})

    def test_rejects_non_positive_vcc(self):
        with self.assertRaises(ValueError):
            calculate(**{**REF, "vcc": 0.0})

    def test_rejects_zero_total_divider_resistance(self):
        with self.assertRaises(ValueError):
            calculate(**{**REF, "r1": 0.0, "r2": 0.0})

    def test_rejects_vbe_outside_valid_range(self):
        for vbe in (-0.1, 12.0, 13.0):
            with self.subTest(vbe=vbe), self.assertRaises(ValueError):
                calculate(**{**REF, "vbe": vbe})


class RegionWarningTest(unittest.TestCase):
    def test_cutoff_reports_zero_currents_and_warns(self):
        r = calculate(**{**REF, "r2": 4_000.0})  # VTH = 0.4615 V < VBE
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ie, 0.0)
        self.assertEqual(r.ve, 0.0)
        self.assertAlmostEqual(r.vb, r.vth, places=9)
        self.assertEqual(r.vc, 12.0)
        self.assertEqual(r.vce, 12.0)
        self.assertTrue(any("Forward-Active" in w for w in r.warnings))

    def test_saturation_warns(self):
        r = calculate(**{**REF, "rc": 12_000.0})
        self.assertEqual(r.region, "saturation")
        self.assertLess(r.vce, 0.3)
        self.assertTrue(any("VCE" in w for w in r.warnings))

    def test_rejects_non_finite_inputs(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                calculate(**{**REF, "vcc": bad})

    def test_rejects_overflowing_intermediates(self):
        with self.assertRaises(ValueError):
            calculate(**{**REF, "vcc": 1e308, "r1": 1e308, "r2": 1e308})


if __name__ == "__main__":
    unittest.main()
