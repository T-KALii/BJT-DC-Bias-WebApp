import unittest

from app import app

REF_FORM = {
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}


class FormPageTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_form_returns_200_with_all_fields(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)


class CalculateRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_post_reference_values_shows_results(self):
        response = self.client.post("/calculate", data=REF_FORM)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("8.05", body)  # VCE
        self.assertIn("1.23", body)  # IC (mA)
        self.assertIn("Active", body)

    def test_post_scientific_notation_is_accepted(self):
        data = {**REF_FORM, "r1": "1e5", "r2": "2.2e4"}
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("8.05", response.get_data(as_text=True))


    def test_post_saturation_shows_warning(self):
        response = self.client.post("/calculate", data={**REF_FORM, "rc": "12000"})
        body = response.get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("Forward-Active", body)


class InvalidInputTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def assert_error_page(self, data):
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="error"', body)
        return body

    def test_zero_resistance_shows_error(self):
        body = self.assert_error_page({**REF_FORM, "r1": "0"})
        self.assertIn("ความต้านทานต้องมากกว่า 0", body)

    def test_empty_field_shows_error(self):
        body = self.assert_error_page({**REF_FORM, "vcc": ""})
        self.assertIn("กรุณากรอกค่าให้ครบทุกช่อง", body)

    def test_non_numeric_shows_error(self):
        body = self.assert_error_page({**REF_FORM, "beta": "abc"})
        self.assertIn("กรุณากรอกเป็นตัวเลขเท่านั้น", body)

    def test_comma_separated_number_shows_error(self):
        body = self.assert_error_page({**REF_FORM, "r1": "100,000"})
        self.assertIn("กรุณากรอกเป็นตัวเลขเท่านั้น", body)

    def test_missing_field_shows_error(self):
        data = {k: v for k, v in REF_FORM.items() if k != "beta"}
        body = self.assert_error_page(data)
        self.assertIn("กรุณากรอกค่าให้ครบทุกช่อง", body)

    def test_non_finite_input_shows_error(self):
        for bad in ("nan", "NaN", "inf", "-inf"):
            with self.subTest(bad=bad):
                body = self.assert_error_page({**REF_FORM, "vcc": bad})
                self.assertIn("ช่วงที่คำนวณได้", body)

    def test_overflowing_input_shows_error(self):
        body = self.assert_error_page(
            {**REF_FORM, "vcc": "1e308", "r1": "1e308", "r2": "1e308"}
        )
        self.assertIn("ช่วงที่คำนวณได้", body)

    def test_extreme_but_valid_values_are_finite(self):
        data = {
            "vcc": "1e9",
            "r1": "1e9",
            "r2": "1e9",
            "rc": "1e9",
            "re": "1e9",
            "beta": "100",
            "vbe": "0.7",
        }
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn("nan", body.lower())
        self.assertNotIn("inf", body.lower())


if __name__ == "__main__":
    unittest.main()
