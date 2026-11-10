# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App หลายไฟล์ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC Operating Point ของ BJT Voltage-Divider Bias ด้วย Python พร้อม validation, region warning และ automated tests

**Architecture:** Server-rendered single page: `POST /calculate` → `app.py` parse ฟอร์ม → `dc_bias.calculate()` (ฟังก์ชันบริสุทธิ์) → Jinja render ผลใน `index.html` ไม่มี JavaScript คำนวณ ไม่มีฐานข้อมูล

**Tech Stack:** Python 3.14.2, Flask (dependency เดียว), `unittest` (stdlib), HTML/CSS ธรรมดา

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- Python 3.14.2; dependency เดียวที่อนุญาตคือ `Flask` (ห้ามเพิ่ม library อื่น)
- หน่วยอินพุต: V, Ω (ตัวเลขล้วน ไม่รับ suffix `k`), β ไม่มีหน่วย, VBE เป็น V
- หน่วยเอาต์พุต: V สำหรับ VB/VE/VC/VCE, mA สำหรับ IC/IE, µA สำหรับ IB
- `VCE_SAT = 0.3` (V) ประกาศเป็นค่าคงที่ใน `dc_bias.py` และอ้างถึงใน README
- `dc_bias.py` ห้าม import flask, ห้ามมี HTML/HTTP, ห้ามฝังสมการใน template
- route: `GET /` และ `POST /calculate` เท่านั้น; ตอบ HTTP 200 ทั้งกรณีสำเร็จและ error
- ภาษา UI ไทย + สัญลักษณ์อังกฤษ; ไม่มี JavaScript framework, ไม่มี CDN
- รัน test ด้วย `python -m unittest discover -s tests -v`
- Commit ทำผ่าน **GitHub Desktop** (ไม่ใช้ `git commit` ใน terminal): ติ๊กไฟล์ → Summary → Commit to main → Push origin
- ค่าคงที่อ้างอิง: VCC=12, R1=100000, R2=22000, RC=2200, RE=1000, β=100, VBE=0.70
- ผลอ้างอิง: VTH≈2.1639, RTH≈18032.8, IB≈12.298 µA, IC≈1.2299 mA, IE≈1.2421 mA, VE≈1.2421, VB≈1.9421, VC≈9.2943, VCE≈8.0522 (Active)

## Review Focus

อินพุต/สภาวะที่ spec ไม่ได้เขียนถึงแต่ผู้ใช้จริงมีโอกาสเจอ — ทุกข้อมี test ใน Task ที่ระบุ:

1. **ช่องว่างหรือ field หาย** → ต้องขึ้น error "กรุณากรอกค่าให้ครบ" ไม่ใช่ 500 (Task 2, 5)
2. **ข้อความที่ไม่ใช่ตัวเลข** (`abc`, `12,000`, `1e3` ที่มี comma) → error อ่านรู้เรื่อง ไม่ล้ม (Task 2, 5)
3. **`R1 + R2 = 0`** → หารด้วยศูนย์ใน VTH/RTH ต้องถูกดักก่อนคำนวณ (Task 2)
4. **VBE ติดลบ หรือ VBE ≥ VCC** → ค่าไม่physical ต้องถูกปฏิเสธ (Task 2)
5. **ค่าสุดขั้ว/เลขยกกำลัง** (`1e9`, ทศนิยมละเอียด) → คำนวณได้ ไม่ crash และ format ไม่พัง (Task 3)

---

## File Structure

| ไฟล์ | ความรับผิดชอบ |
|------|----------------|
| `dc_bias.py` | `DcBiasResult`, `calculate()`, validation ทางไฟฟ้า, region classification — ไม่รู้จัก Flask |
| `app.py` | Flask app, route, parse ฟอร์มเป็น float, แปลง error เป็นข้อความ, ส่ง context ให้ template |
| `templates/index.html` | ฟอร์ม + ตารางผล + กล่อง error/warning (Jinja) |
| `static/style.css` | layout, สี region badge, responsive |
| `tests/test_dc_bias.py` | unit tests ของสมการ/validation/region |
| `tests/test_web.py` | Flask test client tests |
| `requirements.txt` | `Flask` |
| `README.md` | วิธีติดตั้ง/รัน/test + ค่า VCE_SAT |
| `AGENTS.md` | กติกาโค้ดของ repo |
| `docs/validation.md` | ตารางค่าอ้างอิง vs ผลจริง + เคส cutoff/saturation |
| `docs/design-note.md` | สรุป design + เหตุผล |
| `docs/reflection.md` | โครงคำถาม 4 ข้อ + เฉลยเชิงเทคนิค (นักศึกษาเรียบเรียงเอง) |

---

### Task 1: โครงโปรเจกต์ + หน้าฟอร์ม (GET /)

**Files:**
- Create: `requirements.txt`, `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`

**Interfaces:**
- Produces: `app.app` (Flask instance) ที่มี route `GET /`; ชื่อ field ในฟอร์ม: `vcc, r1, r2, rc, re, beta, vbe` (ตัวพิมพ์เล็กทั้งหมด) — Task 3/4/5 ใช้ชื่อนี้

- [ ] **Step 1: สร้าง venv และติดตั้ง Flask**

Run:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install flask
python -c "import flask; print(flask.__version__)"
```
Expected: พิมพ์เวอร์ชัน Flask ได้ (ถ้าติดตั้งไม่ผ่านบน Python 3.14 ให้รายงานทันที ห้ามเลี่ยงด้วย library อื่น)

- [ ] **Step 2: เขียน requirements.txt**

```
Flask>=3.0
```

- [ ] **Step 3: เขียน failing test `tests/test_web.py`**

```python
import unittest

from app import app


class FormPageTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_form_returns_200_with_all_fields(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: รัน test ให้เห็นว่าล้ม**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 5: สร้าง `app.py` และ `templates/index.html` ให้ test ผ่าน**

`app.py` (โครงขั้นต่ำ):
```python
from flask import Flask, render_template

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
```

`templates/index.html` ต้องมี `<form method="post" action="/calculate">` และ `<input name="...">` ครบ 7 ชื่อ
พร้อม label ภาษาไทย + หน่วย + ตัวอย่างค่า เช่น `R1 (Ω) เช่น 100000` (ยังไม่ต้องมีตารางผล)
`static/style.css` ใส่ layout พื้นฐานและ `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`

- [ ] **Step 6: รัน test ให้ผ่าน**

Run: `python -m unittest tests.test_web -v`
Expected: `OK` 1 test

- [ ] **Step 7: ตรวจด้วยตา**

Run: `python -m flask --app app run --debug` แล้วเปิด `http://127.0.0.1:5000/`
Expected: เห็นฟอร์ม 7 ช่อง มีหน่วยและตัวอย่างค่า

- [ ] **Step 8: Commit (GitHub Desktop)**

Files: `.gitignore`, `requirements.txt`, `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`, `docs/superpowers/specs/...`
Summary: `Add Flask form skeleton for DC bias`
Expected: History มี commit ใหม่; **ห้าม** มี `.venv/` ในรายการไฟล์

---

### Task 2: ตรรกะวิศวกรรม `dc_bias.calculate()` + validation

**Files:**
- Create: `dc_bias.py`, `tests/test_dc_bias.py`

**Interfaces:**
- Produces:
  - `VCE_SAT: float = 0.3`
  - `DcBiasResult` (frozen dataclass) fields: `vth, rth, ib, ic, ie, vb, ve, vc, vce: float`, `region: str` (`"active" | "cutoff" | "saturation"`), `warnings: tuple[str, ...]`
  - `calculate(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> DcBiasResult` — raise `ValueError` เมื่ออินพุตไม่physical
- Consumes: ไม่มี (โมดูลบริสุทธิ์)

- [ ] **Step 1: เขียน failing tests (reference + validation)**

```python
import unittest

from dc_bias import calculate

REF = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.7)


class ReferenceCaseTest(unittest.TestCase):
    def test_reference_case_is_active(self):
        r = calculate(**REF)
        self.assertEqual(r.region, "active")
        self.assertAlmostEqual(r.vth, 2.16393, places=4)
        self.assertAlmostEqual(r.rth, 18032.7869, places=3)
        self.assertAlmostEqual(r.ib, 12.2985e-6, places=9)
        self.assertAlmostEqual(r.ic, 1.22985e-3, places=8)
        self.assertAlmostEqual(r.ie, 1.24215e-3, places=8)
        self.assertAlmostEqual(r.ve, 1.24215, places=4)
        self.assertAlmostEqual(r.vb, 1.94215, places=4)
        self.assertAlmostEqual(r.vc, 9.29433, places=4)
        self.assertAlmostEqual(r.vce, 8.05218, places=4)
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: รันให้เห็นว่าล้ม**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: เขียน `dc_bias.py`**

Signature ตาม Interfaces ด้านบน; ลำดับการทำงาน:
1. validate: `vcc <= 0` → `ValueError("VCC ต้องมากกว่า 0")`; `r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0` → "ค่าความต้านทานต้องมากกว่า 0"; `r1 + r2 <= 0` → "R1 + R2 ต้องมากกว่า 0"; `beta <= 0` → "β ต้องมากกว่า 0"; `vbe < 0 or vbe >= vcc` → "VBE ต้องอยู่ระหว่าง 0 ถึง VCC"
2. `vth = vcc * r2 / (r1 + r2)`, `rth = r1 * r2 / (r1 + r2)`
3. `ib = (vth - vbe) / (rth + (beta + 1) * re)`
4. `ic = beta * ib`, `ie = (beta + 1) * ib`, `ve = ie * re`, `vb = ve + vbe`, `vc = vcc - ic * rc`, `vce = vc - ve`
5. `region`: `"cutoff"` ถ้า `ib <= 0`; `"saturation"` ถ้า `vce <= VCE_SAT`; อย่างอื่น `"active"` (Task 4 เติม warnings)

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: `OK` (6 tests; เคส reference ต้องได้ region `active`)

- [ ] **Step 5: Commit (GitHub Desktop)**

Files: `dc_bias.py`, `tests/test_dc_bias.py`
Summary: `Add DC bias calculation with input validation`

---

### Task 3: ต่อ POST /calculate + ตารางผลและหน่วย

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`
- Modify: `tests/test_web.py`

**Interfaces:**
- Consumes: `dc_bias.calculate(**kwargs)` และ `DcBiasResult` จาก Task 2
- Produces: route `POST /calculate`; template context: `result` (`DcBiasResult | None`), `error` (`str | None`), `values` (`dict[str, str]` ค่าที่ผู้ใช้กรอกเพื่อ refill ฟอร์ม)

- [ ] **Step 1: เขียน failing tests**

เพิ่มใน `tests/test_web.py`:

```python
REF_FORM = {"vcc": "12", "r1": "100000", "r2": "22000", "rc": "2200", "re": "1000", "beta": "100", "vbe": "0.7"}


class CalculateRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_post_reference_values_shows_results(self):
        response = self.client.post("/calculate", data=REF_FORM)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("8.05", body)   # VCE
        self.assertIn("1.23", body)   # IC (mA)
        self.assertIn("Active", body)

    def test_post_scientific_notation_is_accepted(self):
        data = {**REF_FORM, "r1": "1e5", "r2": "2.2e4"}
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("8.05", response.get_data(as_text=True))
```

- [ ] **Step 2: รันให้เห็นว่าล้ม**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — 404 (ยังไม่มี route `/calculate`)

- [ ] **Step 3: เพิ่ม route และ template**

`app.py`:
```python
from flask import Flask, render_template, request
from dc_bias import calculate

FIELD_NAMES = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")


@app.post("/calculate")
def calculate_view():
    values = {name: request.form.get(name, "") for name in FIELD_NAMES}
    try:
        parsed = {name: float(values[name]) for name in FIELD_NAMES}
    except ValueError:
        return render_template("index.html", error="กรุณากรอกตัวเลขให้ครบทุกช่อง", result=None, values=values), 200
    try:
        result = calculate(**parsed)
    except ValueError as exc:
        return render_template("index.html", error=str(exc), result=None, values=values), 200
    return render_template("index.html", result=result, error=None, values=values)
```

`templates/index.html`: เพิ่มตารางผลที่แสดง `{{ "%.2f"|format(result.vb) }} V` ฯลฯ, IB เป็น µA (`result.ib * 1e6`), IC/IE เป็น mA (`* 1e3`), badge region และ `<input value="{{ values.get('vcc','') }}">` เพื่อ refill

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `python -m unittest tests.test_web -v`
Expected: `OK` 3 tests

- [ ] **Step 5: ตรวจด้วยตา**

Run: `python -m flask --app app run --debug` → กรอกค่าอ้างอิง → Calculate
Expected: เห็น VB 1.94 V, VE 1.24 V, VC 9.29 V, VCE 8.05 V, IC 1.23 mA, IB 12.3 µA, IE 1.24 mA

- [ ] **Step 6: Commit (GitHub Desktop)**

Files: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`
Summary: `Wire POST /calculate to render DC bias results`

---

### Task 4: Warning และ region badge (Cutoff / Saturation)

**Files:**
- Modify: `dc_bias.py`, `templates/index.html`, `static/style.css`
- Modify: `tests/test_dc_bias.py`, `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate()` จาก Task 2, context `result` จาก Task 3
- Produces: `warnings` ที่มีข้อความเมื่อ `region != "active"`; `region` ใช้เป็น class ของ badge (`region-active`, `region-cutoff`, `region-saturation`)

- [ ] **Step 1: เขียน failing tests (cutoff + saturation)**

```python
class RegionWarningTest(unittest.TestCase):
    def test_cutoff_reports_zero_currents_and_warns(self):
        r = calculate(**{**REF, "r2": 4_000.0})   # VTH = 0.4615 V < VBE
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
```

เพิ่มใน `tests/test_web.py`:
```python
    def test_post_saturation_shows_warning(self):
        response = self.client.post("/calculate", data={**REF_FORM, "rc": "12000"})
        body = response.get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("Forward-Active", body)
```

- [ ] **Step 2: รันให้เห็นว่าล้ม**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — cutoff ยังคืนค่าติดลบ/warnings ว่าง, ไม่มีคำว่า Saturation ในหน้าเว็บ

- [ ] **Step 3: ปรับ `dc_bias.py`**

- ถ้า `ib <= 0`: ตั้ง `ib = ic = ie = 0.0`, `ve = 0.0`, `vb = vth`, `vc = vcc`, `vce = vcc`, `region = "cutoff"`, `warnings = ("VTH ≤ VBE: ทรานซิสเตอร์ไม่นำกระแส แบบจำลอง Forward-Active ใช้ไม่ได้",)`
- ถ้า `vce <= VCE_SAT`: `region = "saturation"`, `warnings = ("VCE ใกล้/ต่ำกว่า VCE(sat) = 0.3 V: ผล DC Bias ไม่แม่นตามแบบจำลอง Forward-Active",)` (ไม่ clamp ค่า)
- `active`: `warnings = ()`

- [ ] **Step 4: ปรับ template ให้แสดง warning + badge**

`<span class="badge region-{{ result.region }}">{{ result.region|capitalize }}</span>` และ `{% for w in result.warnings %}<div class="warn">{{ w }}</div>{% endfor %}`; CSS ใส่สี 3 สถานะ

- [ ] **Step 5: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: `OK` 12 tests (unit 8 + web 4)

- [ ] **Step 6: Commit (GitHub Desktop)**

Files: `dc_bias.py`, `templates/index.html`, `static/style.css`, `tests/test_dc_bias.py`, `tests/test_web.py`
Summary: `Warn when bias leaves forward-active region`

---

### Task 5: Validation ฝั่งหน้าเว็บ (error box) + ค่าที่ทำให้หน้าไม่ล้ม

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`
- Modify: `tests/test_web.py`

**Interfaces:**
- Consumes: `error` จาก context (Task 3)
- Produces: error box ที่แสดง `{{ error }}` เหนือฟอร์ม; หน้าเว็บยัง HTTP 200

- [ ] **Step 1: เขียน failing tests**

```python
class InvalidInputTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def assert_error_page(self, data):
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("error", body.lower())
        return body

    def test_zero_resistance_shows_error(self):
        self.assert_error_page({**REF_FORM, "r1": "0"})

    def test_empty_field_shows_error(self):
        body = self.assert_error_page({**REF_FORM, "vcc": ""})
        self.assertIn("กรอก", body)

    def test_non_numeric_shows_error(self):
        body = self.assert_error_page({**REF_FORM, "beta": "abc"})
        self.assertIn("ตัวเลข", body)
```

- [ ] **Step 2: รันให้เห็นว่าล้ม**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — `test_empty_field_shows_error` / `test_non_numeric_shows_error` ไม่พบคำที่คาด

- [ ] **Step 3: ปรับ `app.py` ให้นับช่องว่างเป็น error ที่อ่านรู้เรื่อง**

ถ้ามีช่องใดเป็น `""` ให้ `error = "กรุณากรอกค่าให้ครบทุกช่อง (VCC, R1, R2, RC, RE, β, VBE)"` ก่อนพยายาม `float()`; ค่าที่ไม่ใช่ตัวเลขใช้ข้อความ "กรุณากรอกเป็นตัวเลขเท่านั้น"

- [ ] **Step 4: ปรับ `templates/index.html`**

`{% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}` เหนือฟอร์ม (ก่อนตารางผล) และ `aria-invalid` ที่ช่องที่ผิดถ้าส่งมาได้

- [ ] **Step 5: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: `OK` 15 tests

- [ ] **Step 6: ตรวจด้วยตา**

Run: `python -m flask --app app run --debug` → ใส่ `R1=0` แล้ว Calculate
Expected: กล่อง error สีแดง ข้อความไทย หน้าไม่ล้ม ไม่ขึ้น traceback

- [ ] **Step 7: Commit (GitHub Desktop)**

Files: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`
Summary: `Show readable errors for invalid inputs`

---

### Task 6: เอกสาร, README และการตรวจรับ

**Files:**
- Create: `README.md`, `AGENTS.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: ผลจาก Task 1–5 (คำสั่งรัน, ค่าอ้างอิง)
- Produces: เอกสารที่ทำให้ A7 ผ่าน

- [ ] **Step 1: เขียน `README.md`**

ต้องมี: ภาพรวม, โครงสร้างไฟล์, วิธีติดตั้ง (`python -m venv .venv`, activate ตาม OS, `pip install -r requirements.txt`), วิธีรัน (`python -m flask --app app run --debug`, เปิด `http://127.0.0.1:5000/`), วิธีรัน test (`python -m unittest discover -s tests -v`), สมมติฐาน Forward-Active + `VCE_SAT = 0.3 V`, ข้อจำกัด (ไม่ใช่ SPICE)

- [ ] **Step 2: เขียน `AGENTS.md`**

กติกา: แยก `dc_bias.py` (ฟิสิกส์) ออกจาก `app.py` (HTTP); ห้ามฝังสมการใน template; ทุกฟีเจอร์ต้องมี test; รัน `python -m unittest discover -s tests -v` ก่อน commit; commit ผ่าน GitHub Desktop

- [ ] **Step 3: เขียน `docs/validation.md`**

ตาราง 3 เคส: reference (active), cutoff (`r2=4000`), saturation (`rc=12000`) — คอลัมน์ "คำนวณมือ", "ผลจากแอป", "ผลต่าง/หมายเหตุ" พร้อมค่าจริงที่วัดได้จากการรัน test

- [ ] **Step 4: เขียน `docs/design-note.md`**

สรุป 1 หน้า: ทางเลือก A/B/C, เหตุผลที่เลือก server-rendered, การรับหน่วย Ω, region logic

- [ ] **Step 5: เขียน `docs/reflection.md` เป็นโครงให้อาจารย์เห็นว่านักศึกษาตอบเอง**

ใส่ 4 คำถามท้ายใบงาน + ช่อง `> คำตอบ:` และภาคผนวก "เฉลยเชิงเทคนิคโดยย่อ" (คนละส่วนกับคำตอบ)
ห้ามเขียนคำตอบแทนนักศึกษา

- [ ] **Step 6: รันชุดทดสอบสุดท้าย**

Run: `python -m unittest discover -s tests -v`
Expected: `OK` 15 tests (หรือมากกว่า) ไม่มี failure/error

- [ ] **Step 7: ทดสอบตามเกณฑ์ A1–A7 ด้วยมือ**

ไล่: เปิดหน้า (A1) → กรอกค่าอ้างอิง (A2/A3) → ใส่ `R1=0` (A4) → `rc=12000` (A5) → ดู test log (A6) → อ่าน README แล้วทำตาม (A7)

- [ ] **Step 8: Commit + Push (GitHub Desktop)**

Files: `README.md`, `AGENTS.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`
Summary: `Document setup, validation results and lab reflection`
จากนั้น **Push origin** และคัดลอก commit SHA ไปส่ง Moodle

---

## Self-Review

- **Spec coverage:** A1→Task 1, A2/A3→Task 2–3, A4→Task 2, 5, A5→Task 4, A6→Task 2–5 (15 tests), A7→Task 6, docs ตาม §8 → Task 6 ครบ
- **Step scan:** ทุก step มีคำสั่งหรือ signature ที่ลงมือได้ทันที; ไม่มี "handle edge cases" ลอย ๆ
- **Type consistency:** `calculate()` kwargs ตรงกับ `FIELD_NAMES` ใน `app.py`; `DcBiasResult` fields ใช้ชื่อเดียวกันใน template และ tests
- **Review Focus:** ครบ 5 ข้อ มี test ใน Task 2 (ข้อ 1,2,3,4) และ Task 3 (ข้อ 5)
- **Proportion:** แผนยาวกว่า spec เล็กน้อยเพราะมี test code ตามที่ skill กำหนด แต่ไม่มี implementation body ยกเว้น validation messages
