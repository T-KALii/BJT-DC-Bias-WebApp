# BJT DC Bias Web App — Design (ENG29 2121 · Lab 02)

วันที่: 2026-11-10
ขอบเขต: Lab 02 เท่านั้น (W2) — DC Bias, Voltage-Divider Bias, Forward-Active approximation

## 1. Intent และเหตุผล

นักศึกษาปี 2 วิศวกรรมไฟฟ้าต้องส่งงานภายในคาบ 3 ชั่วโมง: เว็บ Flask ที่คำนวณ DC Operating Point
ของ BJT Common-Emitter แบบ Voltage-Divider Bias ได้จริง เปิดผ่าน Browser, มี tests และ commit ขึ้น
GitHub เป้าหมายการเรียนรู้ไม่ใช่แค่ "เว็บสวย" แต่คือการเห็นว่า HTML เป็นเพียง template ที่ Server
ส่งมา และตัวเลขทั้งหมดมาจาก Python จริง

## 2. Goals

| ID | เป้าหมาย | ตรงกับเกณฑ์ |
|----|----------|--------------|
| G1 | เปิด `http://127.0.0.1:5000/` แล้วเห็นฟอร์ม (HTTP 200) | A1 |
| G2 | POST แล้ว Python คำนวณและแสดง DC Bias ใน HTML (ไม่ใช่ค่าฮาร์ดโค้ด) | A2 |
| G3 | ค่าที่ได้ตรงกับสมการในใบงาน (VB, VE, VC, VCE, IC) พร้อมหน่วย | A3 |
| G4 | อินพุตผิด (R≤0, β≤0, VCC≤0, ไม่ใช่ตัวเลข, ว่าง) แสดง error ชัดเจนและหน้าไม่ล้ม | A4 |
| G5 | เตือนเมื่ออยู่นอก Forward-Active (Cutoff / Saturation) | A5 |
| G6 | ≥3 unit tests ทางวิศวกรรม + ≥1 Flask test client test | A6 |
| G7 | README ทำให้ clone → ติดตั้ง → รัน → test ได้ | A7 |

## 3. Non-goals (ตามใบงาน)

- ไม่มี Fixed Bias / Emitter Bias / Bias template อื่น (W3)
- ไม่มี SPICE/ngspice, DC Load Line (W4)
- ไม่มี AC small-signal, Gain, Bode Plot (W5)
- ไม่มี Transient, Signal Generator, Amplitude/Frequency knob (W6)
- ไม่มี Interactive schematic, Overlay animation (W7)
- ไม่มีฐานข้อมูล, ระบบ login, JavaScript framework

## 4. Anti-goals (ทำงานเสร็จแต่ถือว่าล้มเหลว)

- หน้าเว็บที่แสดงเลขคงที่หรือคำนวณฝั่ง JavaScript แทน Python
- เปิดด้วย `file://` แล้วอ้างว่ารัน Flask
- รายงานผลเป็นค่าที่เชื่อถือได้ทั้งที่อยู่นอก Active Region โดยไม่มี warning
- หน้าล้ม (HTTP 500) เมื่อผู้ใช้กรอกค่าผิด
- commit `.venv/`, `.env`, credential

## 5. Constraints

- Python 3.14.2 (ติดตั้งแล้ว), Flask + unittest จาก standard library
- repo เดิม: `C:\Users\B6829773\Documents\GitHub\BJT DC Bias WebApp` (branch `main`)
- commit/push ผ่าน GitHub Desktop (ไม่ใช้ CLI commit)
- งบเวลาพัฒนา ~75 นาที ในคาบเดียว
- อินเทอร์เน็ตใช้อ่าน docs ได้ แต่แอปต้องรันได้แบบ local

## 6. Approaches ที่พิจารณา

| ทาง | ลักษณะ | แลกกับอะไร | สรุป |
|-----|--------|-------------|------|
| **A. Server-rendered single page + `POST /calculate`** | ฟอร์มและผลลัพธ์อยู่ใน `index.html` เดียว, Jinja render ผลหลัง POST | ต้อง refresh หน้า แต่โค้ดน้อยที่สุด ตรง rubric ที่ต้องการ Python คำนวณ | **เลือก** |
| B. JSON API + `fetch()` | `/api/calculate` คืน JSON, JS วาดผล | UI ลื่นกว่า แต่เพิ่ม JS + จัดการ error สองที่ + test ยากขึ้น | ตัดทิ้ง |
| C. คำนวณฝั่ง Client ด้วย JS | ไม่ต้องมี backend | ขัดเจตนาของโจทย์ (ต้องมี Python Backend) และไม่ผ่าน A2 | ตัดทิ้ง |

**Decision: A** — เพราะ rubric ให้คะแนน "Flask รับ request → Python คำนวณ → template แสดงผล"
และเวลาเหลือน้อย การมี route เดียวที่ทดสอบด้วย Flask test client ได้ตรง ๆ คือความเสี่ยงต่ำสุด

## 7. Design

### 7.1 Routes

| Method | Path | ทำอะไร |
|--------|------|--------|
| GET | `/` | render `index.html` พร้อมฟอร์มว่าง (placeholder ตัวอย่างค่า) |
| POST | `/calculate` | parse ฟอร์ม → validate → เรียก `dc_bias.calculate()` → render `index.html` พร้อมผลหรือ error (HTTP 200 ทั้งสองกรณี) |

ไม่มี route อื่นในขอบเขต Lab 2

### 7.2 Module boundary

- `dc_bias.py` — ฟังก์ชันบริสุทธิ์ ไม่ import Flask/Jinja ไม่รู้จัก HTTP
  - `calculate(vcc, r1, r2, rc, re, beta, vbe) -> DcBiasResult`
  - `DcBiasResult`: `vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warnings`
  - raise `ValueError` เมื่อค่าอยู่นอกสมมติฐานทางกายภาพ (R≤0, β≤0, VCC≤0, VBE<0 หรือ VBE≥VCC)
- `app.py` — แปลง string→float, จับ `ValueError`, ส่ง dict ให้ template
- `templates/index.html` — ฟอร์ม + ตารางผล + กล่อง error/warning (ไม่ฝังสมการ)
- `static/style.css` — responsive, unit hints, สีของ region badge

### 7.3 สมการ (ตามใบงาน ข้อ 06)

```
VTH = VCC * R2 / (R1 + R2)
RTH = R1 * R2 / (R1 + R2)
IB  = (VTH - VBE) / (RTH + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

หน่วยภายในใช้ SI ทั้งหมด: V, A, Ω แล้วแปลงเป็น mA / µA ตอนแสดงผลเท่านั้น

### 7.4 การรับหน่วย (Decision)

รับค่าตัวต้านทานเป็น **Ω ล้วน** ตามสเปก (`R1 (Ω)` พร้อมตัวอย่าง `เช่น 100000`) ไม่รับ suffix `k`
เหตุผล: ตรงใบงาน, parser สั้น, ลดชุด test ที่ต้องดูแล — ถ้าต้องการ `100k` ภายหลัง เพิ่ม parser
ชั้นเดียวโดยไม่กระทบ `dc_bias.py`

### 7.5 Region classification

ลำดับการตัดสิน (ใช้ค่าคงที่ `VCE_SAT = 0.3 V` ประกาศชัดในโค้ดและ README):

1. `IB <= 0` (เกิดเมื่อ `VTH <= VBE`) → `region = "cutoff"` + warning "VTH ≤ VBE: ทรานซิสเตอร์ไม่นำกระแส แบบจำลอง Forward-Active ใช้ไม่ได้"
2. `VCE <= VCE_SAT` → `region = "saturation"` + warning "VCE ใกล้/ต่ำกว่า VCE(sat): ผล DC Bias ไม่แม่นตามแบบจำลอง Forward-Active"
3. อื่น ๆ → `region = "active"` แสดงผลปกติโดยไม่ตีความเกินขอบเขต

กรณี cutoff ให้รายงาน **สภาวะทางกายภาพ** ไม่ใช่ค่าดิบจากสูตร: `IB = IC = IE = 0`, `VE = 0`,
`VB = VTH`, `VC = VCC`, `VCE = VCC` แล้วติดป้าย `cutoff` + warning ว่าแบบจำลอง Forward-Active
ใช้ไม่ได้ (ค่าดิบจากสูตรจะติดลบและทำให้ VC > VCC ซึ่งสื่อความหมายผิด)
กรณี saturation ให้รายงานค่าที่คำนวณได้ตามสมการตามจริง (ไม่ clamp) พร้อมป้าย `saturation` + warning
เพราะยังเป็น Operating point ที่คำนวณได้ แต่ไม่แม่นตามแบบจำลอง

### 7.6 UI (ข้อความ + โครง)

```
┌ BJT DC Bias Calculator · Voltage Divider ─────────────┐
│ VCC [V]   [12]        R1 [Ω] [100000]  R2 [Ω] [22000]│
│ RC  [Ω]   [2200]      RE [Ω] [1000]                   │
│ β         [100]       VBE [V] [0.70]                  │
│                    [ Calculate DC Bias ]              │
├ DC Bias Results ─────────────────────────────────────┤
│ VB 1.94 V │ VE 1.24 V │ VC 9.29 V │ VCE 8.05 V        │
│ IC 1.23 mA │ IB 12.3 µA │ IE 1.24 mA                  │
│ [Active Region]                                        │
└───────────────────────────────────────────────────────┘
```

- ภาษาไทยเป็นหลัก + สัญลักษณ์อังกฤษ (VB, VCE) กำกับ
- กล่อง error สีแดงเหนือฟอร์ม, กล่อง warning สีส้มใต้ตารางผล
- ไม่ใช้ JavaScript; ใช้ HTML form + `required` เบา ๆ เท่านั้น

### 7.7 ไฟล์ที่ส่ง

```
BJT DC Bias WebApp/
├── app.py
├── dc_bias.py
├── templates/index.html
├── static/style.css
├── tests/test_dc_bias.py
├── tests/test_web.py
├── requirements.txt
├── README.md
├── AGENTS.md
├── .gitignore
└── docs/
    ├── design-note.md
    ├── validation.md
    └── reflection.md
```

### 7.8 Tests (แผนขั้นต่ำ)

`tests/test_dc_bias.py` (unittest, ≥3)
1. Reference case: VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.7 → VB≈1.942, VE≈1.242, VC≈9.294, VCE≈8.052, IC≈1.230 mA (คลาดเคลื่อน < 1e-3), region=active
2. `R <= 0` และ `β <= 0` และ `VCC <= 0` → `ValueError`
3. Cutoff: `VTH <= VBE` → region=cutoff + มี warning
4. Saturation: ค่าอ้างอิงเดิมแต่เปลี่ยน `RC = 12 kΩ` → `VCE < 0.3 V` → region=saturation + มี warning (ตรวจแล้วว่า "RE ใหญ่" ไม่ทำให้อิ่มตัว เพราะ VE → VTH − VBE)

`tests/test_web.py` (Flask test client, ≥1)
1. `GET /` → 200 และมีชื่อ field ครบ 7 ตัว
2. `POST /calculate` ค่าอ้างอิง → 200 และเนื้อหามี `8.05` / `1.23`
3. `POST /calculate` ค่า `R1=0` → 200 และมีข้อความ error (ไม่ 500)

### 7.9 Acceptance mapping

| เกณฑ์ | องค์ประกอบที่รองรับ |
|-------|--------------------|
| A1 | route `GET /` + `templates/index.html` |
| A2 | route `POST /calculate` → `dc_bias.calculate()` |
| A3 | สมการ 7.3 + test reference case + `docs/validation.md` |
| A4 | validation 7.2 + error box 7.6 + web test 3 |
| A5 | region classification 7.5 + warning box |
| A6 | `tests/` ตาม 7.8 (รันด้วย `python -m unittest discover -s tests -v`) |
| A7 | `README.md` + `requirements.txt` + `.gitignore` |

## 8. เอกสารประกอบและผู้รับผิดชอบ

| ไฟล์ | เนื้อหา | ใครทำ |
|------|---------|-------|
| `README.md` | วิธีติดตั้ง/รัน/test ตาม A7 | agent ร่าง, นักศึกษาตรวจ |
| `docs/validation.md` | ตารางค่าอ้างอิงที่คำนวณมือ + ผลจริง + เคส cutoff/saturation | agent สร้างจาก tests |
| `docs/design-note.md` | สรุป Design นี้ + เหตุผลการเลือก | agent สรุปจากเอกสารนี้ |
| `docs/reflection.md` | ตอบคำถามรายบุคคล 4 ข้อท้ายใบงาน | **นักศึกษาเขียนเอง** — agent ให้โครงคำถาม + เฉลยเชิงเทคนิคเพื่อเรียบเรียง |
| `AGENTS.md` | กติกาโค้ดสั้น ๆ (แยกชั้น, ห้ามฝังสมการใน template, รัน test ก่อน commit) | agent |

## 9. สิ่งที่เหลือให้ผู้สร้างตัดสิน (ไม่ต้องถามเจ้าของงาน)

- โครง HTML/CSS จริง, การจัดวาง, ระดับความสวย
- จำนวนตำแหน่งทศนิยม (เลือก 2 ตำแหน่งสำหรับ V, 3 สำหรับ mA/µA)
- ถ้อยคำของข้อความ error/warning ให้อ่านง่าย (คงสาระตาม 7.5)
- โครงสร้างภายใน `DcBiasResult` (dataclass หรือ dict)
- วิธีรัน test ในเครื่อง และการตั้งชื่อ commit

## 10. ความเสี่ยง

| ความเสี่ยง | ผลกระทบ | ทางรับมือ |
|---|---|---|
| Flask บน Python 3.14 มีปัญหาความเข้ากันได้ | ติดตั้ง/รันไม่ได้ | ทดสอบ `pip install flask` ทันทีเป็นขั้นแรก ถ้าล้มให้ pin เวอร์ชันที่รองรับ |
| ค่าอินพุตอย่าง `1e3` หรือช่องว่างทำให้ parse ผิด | หน้าเว็บแสดง error ไม่ถูกจุด | ใช้ `float()` แล้วจับ `ValueError`, test ค่าที่ไม่ใช่ตัวเลข |
| ผู้ใช้กรอกค่าที่ทำให้เกิดหารด้วยศูนย์ (R1+R2=0) | หน้าเว็บล้ม | ตรวจ `R1+R2 > 0` ก่อนคำนวณ + test |
| เวลาไม่พอทำ UI สวย | เสียคะแนนเล็กน้อย | ทำ functionality + tests ให้ผ่านก่อน แล้วค่อยตกแต่ง |
