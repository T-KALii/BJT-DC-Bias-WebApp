"""TDD for the Lab 4 Flask simulator routes (no real solver required)."""
import unittest
from unittest.mock import patch

import app as flask_app
import spice_engine


DC_RESULT = {
    "status": "success", "engine": "ngspice", "version": "47", "mode": "dc",
    "model": ".MODEL QNPN NPN(IS=1E-14 BF=100 VAF=100)",
    "vb": 1.949, "ve": 1.289, "vc": 9.189, "vce": 7.900, "ic_ma": 1.278,
    "netlist": "* netlist", "log_excerpt": "* log", "series": [],
}
AC_RESULT = {
    **DC_RESULT, "mode": "ac",
    "series": [{"frequency_hz": 100, "gain_db": 4.86, "phase_deg": -3.1}],
}
TRAN_RESULT = {
    **DC_RESULT, "mode": "transient",
    "series": [
        {"time_s": 0.0, "vin_v": 0.0, "vout_v": 0.0},
        {"time_s": 0.001, "vin_v": 0.01, "vout_v": -0.02},
    ],
}


class SimulatorRouteTest(unittest.TestCase):
    def setUp(self):
        flask_app.app.config.update(TESTING=True)
        self.client = flask_app.app.test_client()

    def test_get_form_has_all_three_modes(self):
        response = self.client.get("/simulator")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        for label in ("DC · .op", "AC · .ac", "Transient · .tran"):
            self.assertIn(label, text)

    def test_lab3_page_links_to_simulator(self):
        text = self.client.get("/").get_data(as_text=True)
        self.assertIn("/simulator", text)

    def test_root_shows_both_workspaces_on_one_page(self):
        text = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="lab3"', text)
        self.assertIn('id="lab4"', text)
        self.assertIn('action="/calculate"', text)
        self.assertIn('action="/simulator/run"', text)

    def test_simulator_alias_shows_both_workspaces(self):
        text = self.client.get("/simulator").get_data(as_text=True)
        self.assertIn('id="lab3"', text)
        self.assertIn('id="lab4"', text)
        self.assertIn('id="run-status"', text)

    def test_lab3_post_keeps_simulator_workspace(self):
        text = self.client.post("/calculate", data={
            "circuit": "divider", "vcc": "12", "r1": "100000",
            "r2": "22000", "rc": "2200", "re": "1000",
            "beta": "100", "vbe": "0.70",
        }).get_data(as_text=True)
        self.assertIn("DC Bias Results", text)
        self.assertIn("Run Simulation", text)

    def test_simulator_post_keeps_lab3_workspace(self):
        with patch.object(flask_app.spice_engine, "run_simulation", return_value=DC_RESULT):
            text = self.client.post("/simulator/run", data={"mode": "dc"}).get_data(as_text=True)
        self.assertIn("SUCCESS", text)
        self.assertIn("Calculate DC Bias", text)

    def test_running_status_element_and_script(self):
        text = self.client.get("/simulator").get_data(as_text=True)
        self.assertIn('id="run-status"', text)
        self.assertIn("static/app.js", text)
        with self.client.get("/static/app.js") as script_response:
            self.assertIn("RUNNING", script_response.get_data(as_text=True))

    def test_running_script_only_targets_simulator_forms(self):
        with self.client.get("/static/app.js") as script_response:
            script = script_response.get_data(as_text=True)
        self.assertIn("form[action='/simulator/run']", script)

    def test_invalid_re_shows_error_without_success(self):
        response = self.client.post("/simulator/run", data={"mode": "dc", "re": "0"})
        text = response.get_data(as_text=True)
        self.assertIn("RE", text)
        self.assertNotIn("SUCCESS", text)

    def test_engine_error_is_not_reported_as_success(self):
        with patch.object(
            flask_app.spice_engine, "run_simulation",
            side_effect=spice_engine.SpiceEngineError("ngspice not found"),
        ):
            text = self.client.post("/simulator/run", data={"mode": "dc"}).get_data(as_text=True)
        self.assertIn("ngspice not found", text)
        self.assertNotIn("SUCCESS", text)

    def test_dc_success_shows_spice_and_analytical_labels(self):
        with patch.object(flask_app.spice_engine, "run_simulation", return_value=DC_RESULT):
            text = self.client.post("/simulator/run", data={"mode": "dc"}).get_data(as_text=True)
        self.assertIn("SUCCESS", text)
        self.assertIn("SPICE", text)
        self.assertIn("LAB 03", text)
        self.assertIn("1.949", text)

    def test_ac_success_renders_real_svg(self):
        with patch.object(flask_app.spice_engine, "run_simulation", return_value=AC_RESULT):
            text = self.client.post("/simulator/run", data={"mode": "ac"}).get_data(as_text=True)
        self.assertIn("<svg", text)
        self.assertIn("Bode", text)
        self.assertIn("Frequency (Hz, log)", text)

    def test_transient_success_renders_waveform(self):
        with patch.object(flask_app.spice_engine, "run_simulation", return_value=TRAN_RESULT):
            text = self.client.post("/simulator/run", data={"mode": "transient"}).get_data(as_text=True)
        self.assertIn("Vin (V) teal", text)
        self.assertIn("mVpp", text)


if __name__ == "__main__":
    unittest.main()
