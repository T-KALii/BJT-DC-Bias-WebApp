# BJT DC Bias Web App — Voltage Divider Bias

เว็บแอปพลิเคชัน Flask สำหรับคำนวณ **DC Operating Point** ของ BJT แบบ NPN
วงจร Common-Emitter ที่ไบอัสด้วย Voltage Divider (R1, R2) — งาน Lab 02
วิชา ENG29 2121

ค่าที่คำนวณ: `VTH, RTH, IB, IC, IE, VB, VE, VC, VCE` พร้อมหน่วยและการเตือน
เมื่อผลอยู่นอกช่วงที่แบบจำลอง Forward-Active ใช้ได้

## โครงสร้างไฟล์

```
app.py                  Flask routes (GET /, POST /calculate)
dc_bias.py              สมการวิศวกรรมล้วน (ไม่รู้จัก Flask/HTML)
templates/index.html    ฟอร์ม + ตารางผล (Jinja)
static/style.css        หน้าตาเว็บ
tests/test_dc_bias.py   unit tests ของสมการ
tests/test_web.py       HTTP tests ด้วย Flask test client
requirements.txt        Flask
docs/design-note.md     สรุปการออกแบบ
docs/validation.md      ผลตรวจสอบกับค่าคำนวณมือ
docs/reflection.md      คำถามรายบุคคล (นักศึกษาเขียนเอง)
```

## การติดตั้ง

ต้องมี Python 3.10 ขึ้นไป (พัฒนาและทดสอบบน Python 3.14.2)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

## การรันเว็บ

```powershell
python -m flask --app app run --debug
```

เปิด `http://127.0.0.1:5000/` ใน Browser แล้วกรอกค่า VCC, R1, R2, RC, RE,
β และ VBE (หน่วย V และ Ω) จากนั้นกด **Calculate DC Bias**

ตัวอย่างค่าทดลอง: `VCC=12, R1=100000, R2=22000, RC=2200, RE=1000, β=100, VBE=0.70`

ผลที่คาดหวัง: `VB≈1.94 V, VE≈1.24 V, VC≈9.29 V, VCE≈8.05 V, IC≈1.230 mA`

## การรัน tests

```powershell
python -m unittest discover -s tests -v
```

ต้องได้ `OK` 22 tests (unit 10 + web 12)

## แบบจำลองและข้อจำกัด

ใช้ Forward-Active approximation: β คงที่, VBE คงที่, ไม่คำนวณ Early effect

```
VTH = VCC·R2/(R1+R2)      RTH = R1·R2/(R1+R2)
IB  = (VTH − VBE)/(RTH + (β+1)·RE)
IC  = β·IB                 IE = (β+1)·IB
VE  = IE·RE                VB = VE + VBE
VC  = VCC − IC·RC          VCE = VC − VE
```

- `VCE_SAT = 0.3 V` (ค่าคงที่ใน `dc_bias.py`) — ถ้า `VCE ≤ 0.3 V` จะเตือนว่า
  อยู่นอกแบบจำลอง Forward-Active
- ถ้า `VTH ≤ VBE` ทรานซิสเตอร์อยู่ใน **Cutoff** ระบบรายงาน `IB = IC = IE = 0`,
  `VB = VTH`, `VC = VCE = VCC` พร้อมคำเตือน
- เครื่องมือนี้ **ไม่ใช่ SPICE** และไม่ครอบคลุม AC, Transient, Bode Plot หรือ
  Bias แบบอื่นใน Lab 2

## หมายเหตุความปลอดภัย

Flask Debug Server ใช้สำหรับพัฒนาในเครื่องเท่านั้น (`127.0.0.1`) ไม่ควรเปิด
ให้เครือข่ายภายนอกเข้าถึง และห้าม commit `.venv/`, `.env` หรือ credential
