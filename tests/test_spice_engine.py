"""TDD for the Lab 4 ngspice adapter.

These tests are written before spice_engine.py exists so the first run fails.
Run: py -m unittest discover -s tests -v
"""
import unittest
from unittest.mock import patch

import spice_engine


RAW = {
    "vcc": "12", "r1": "100000", "r2": "22000", "rc": "2200",
    "re": "1000", "rl": "10000", "cin": "10", "cout": "10",
    "amp": "10", "freq": "1", "fstart": "100", "fstop": "1000000",
    "tstop": "2", "tstep": "1",
}


class ValidateParamsTest(unittest.TestCase):
    def test_default_fixture_is_normalised_to_si(self):
        p = spice_engine.validate_params("transient", RAW)
        self.assertEqual(p["vcc"], 12.0)
        self.assertAlmostEqual(p["cin"], 10e-6)
        self.assertEqual(p["amp"], 10e-3)
        self.assertEqual(p["freq"], 1000.0)
        self.assertEqual(p["tstop"], 2e-3)

    def test_re_zero_is_rejected(self):
        bad = dict(RAW, re="0")
        with self.assertRaises(ValueError):
            spice_engine.validate_params("dc", bad)

    def test_non_numeric_and_negative_are_rejected(self):
        with self.assertRaises(ValueError):
            spice_engine.validate_params("ac", dict(RAW, rc="abc"))
        with self.assertRaises(ValueError):
            spice_engine.validate_params("ac", dict(RAW, rl="-10"))

    def test_ac_sweep_bounds_are_checked(self):
        with self.assertRaises(ValueError):
            spice_engine.validate_params("ac", dict(RAW, fstop="50"))

    def test_transient_step_checked(self):
        with self.assertRaises(ValueError):
            spice_engine.validate_params("transient", dict(RAW, tstep="3000"))


class NetlistTest(unittest.TestCase):
    def test_dc_has_op_only(self):
        netlist = spice_engine.build_netlist("dc", spice_engine.validate_params("dc", RAW))
        self.assertIn(".OP", netlist)
        self.assertNotIn(".AC", netlist)
        self.assertNotIn(".TRAN", netlist)
        self.assertIn("BF=100", netlist)

    def test_ac_has_ac_and_both_references(self):
        netlist = spice_engine.build_netlist("ac", spice_engine.validate_params("ac", RAW))
        self.assertIn(".AC DEC", netlist)
        self.assertIn("VDB(VIN)", netlist)
        self.assertIn("VDB(VOUT)", netlist)
        self.assertNotIn(".TRAN", netlist)

    def test_transient_has_tran_and_sin_source(self):
        netlist = spice_engine.build_netlist("transient", spice_engine.validate_params("transient", RAW))
        self.assertIn(".TRAN", netlist)
        self.assertIn("SIN(0 0.01 1000)", netlist)
        self.assertNotIn(".AC", netlist)


class ParserTest(unittest.TestCase):
    OP_LOG = """
Node Voltage
---- -------
emitter 1.289454e+00
collector 9.189410e+00
base 1.949112e+00
vcc 1.200000e+01
Source Current
"""

    AC_LOG = """
Index frequency vdb(vin) vp(vin)
0 1.000000e+02 -4.00000e+01 0.000000e+00
1 1.000000e+03 -4.00000e+01 0.000000e+00
Index frequency vdb(vout) vp(vout)
0 1.000000e+02 -3.51414e+01 -3.118230e+00
1 1.000000e+03 -3.51402e+01 -3.139260e+00
"""

    TRAN_LOG = """
Index time v(vin) v(vout)
0 0.000000e+00 0.000000e+00 0.000000e+00
1 1.000000e-08 6.283185e-07 -2.419620e-05
"""

    def test_parse_op_nodes(self):
        p = spice_engine.validate_params("dc", RAW)
        result = spice_engine.parse_op(self.OP_LOG, p)
        self.assertAlmostEqual(result["vb"], 1.949112, places=5)
        self.assertAlmostEqual(result["vcc"], 12.0, places=5)
        self.assertAlmostEqual(result["ic_ma"], (12 - 9.189410) / 2200 * 1e3, places=4)

    def test_parse_ac_merges_reference_and_computes_gain_phase(self):
        result = spice_engine.parse_ac(self.AC_LOG)
        self.assertEqual(len(result["series"]), 2)
        first = result["series"][0]
        self.assertAlmostEqual(first["gain_db"], -35.1414 + 40.0, places=4)
        self.assertAlmostEqual(first["phase_deg"], -3.11823, places=4)
        self.assertEqual(result["vin_reference"], "VDB(VIN) / VP(VIN)")

    def test_parse_tran_merges_paginated_headers(self):
        # ngspice repeats the table header every ~58 rows in batch mode.
        log = self.TRAN_LOG + """
Index time v(vin) v(vout)
--------------------------------------------------------------------------------
2 2.000000e-07 1.256637e-05 -4.900000e-05
"""
        result = spice_engine.parse_tran(log)
        self.assertEqual(len(result["series"]), 3)
        self.assertAlmostEqual(result["series"][2]["time_s"], 2e-7)

    def test_parse_tran_reads_waveforms(self):
        result = spice_engine.parse_tran(self.TRAN_LOG)
        self.assertEqual(len(result["series"]), 2)
        self.assertAlmostEqual(result["series"][1]["vin_v"], 6.283185e-7, places=10)
        self.assertLess(result["series"][1]["vout_v"], 0)


class EngineFailureTest(unittest.TestCase):
    def test_missing_executable_raises_spice_error(self):
        with patch.object(spice_engine, "find_ngspice", return_value=None):
            with self.assertRaises(spice_engine.SpiceEngineError):
                spice_engine.run_simulation("dc", RAW)

    def test_failed_process_never_returns_success(self):
        fake = spice_engine.subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="boom"
        )
        with patch.object(spice_engine, "find_ngspice", return_value="ngspice.exe"), \
             patch.object(spice_engine.subprocess, "run", return_value=fake), \
             patch.object(spice_engine, "_write_netlist", return_value=None):
            with self.assertRaises(spice_engine.SpiceEngineError):
                spice_engine.run_simulation("dc", RAW)


if __name__ == "__main__":
    unittest.main()
