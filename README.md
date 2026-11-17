# BJT DC Bias Web App — Lab 03 (3 วงจรไบอัส)

เว็บแอป Flask ที่คำนวณ **DC Operating Point** ของ BJT NPN Common-Emitter ได้ 3 แบบในหน้าเดียว
ต่อยอดจาก Lab 02 (Voltage Divider Bias) โดยผลของโหมดเดิมยังเหมือนเดิมทุกประการ

วิชา ENG29 2121 · Lab 03 · แบบจำลอง Forward-Active (β และ VBE คงที่, ไม่ใช่ SPICE)

## วงจรที่รองรับ

| เลือกโหมด | ช่องที่ใช้ | สมการ IB |
|-----------|------------|-----------|
| Voltage Divider Bias (เดิม) | VCC, R1, R2, RC, RE, β, VBE | `(VTH − VBE)/(RTH + (β+1)RE)` |
| Fixed Bias | VCC, RB, RC, β, VBE | `(VCC − VBE)/RB` · `VE = 0 V` |
| Emitter Bias (แหล่งจ่ายเดียว) | VCC, RB, RC, RE, β, VBE | `(VCC − VBE)/(RB + (β+1)RE)` |

ค่าที่แสดงทุกโหมด: `VB, VE, VC, VCE` (V), `IC, IE` (mA), `IB` (µA)
**หน่วยที่กรอกคือ Ω และ V** (เช่น 1 MΩ → `1000000`, 2.2 kΩ → `2200`)

เลือกวงจรจาก dropdown แล้วกด **เปลี่ยนวงจร** (โหลดฟอร์มใหม่ ไม่ใช้ JavaScript)
ฟอร์มจะโชว์เฉพาะช่องที่โหมดนั้นใช้

## โครงสร้างไฟล์

```
app.py                  Flask routes + เลือกโหมดด้วย if/elif + ตรวจอินพุต
dc_bias.py              สมการล้วน: calculate(), calculate_fixed(), calculate_emitter()
templates/index.html    dropdown เลือกวงจร + ฟอร์ม + ตารางผล (Jinja)
static/style.css        หน้าตาเว็บ
tests/                  ชุดทดสอบเดิม Lab 02 (22 tests) — ยังผ่านอยู่
docs/validation.md      ตาราง A1–A5 + ค่าอ้างอิงอิสระ + หลักฐานจาก Browser
docs/evidence/          ภาพหน้าจอผลการตรวจ
requirements.txt        Flask
opencode.json           ตั้งค่า Playwright MCP (OpenCode V2)
```

## การติดตั้ง

ต้องมี Python 3.10 ขึ้นไป (พัฒนา/ทดสอบบน Python 3.14.2)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> ถ้าเครื่องขึ้น *"Python was not found"* จาก Microsoft Store ให้ใช้ `py -m venv .venv`
> แล้วรันคำสั่งต่อไปด้วย `.venv\Scripts\python.exe` แทน `python`

## การรันเว็บ

```powershell
python -m flask --app app run --debug
```

เปิด `http://127.0.0.1:5000/` แล้วเลือกโหมด กรอกค่า กด **Calculate DC Bias**

### ตัวอย่างค่าที่ใช้ตรวจ (VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V)

| กรณี | อินพุต | ผลที่คาดหวัง |
|------|--------|--------------|
| A1 Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | IC ≈ 1.230 mA, VCE ≈ 8.05 V |
| A2 Fixed | RB=1 MΩ | IC ≈ 1.130 mA, VCE ≈ 9.51 V |
| A3 Emitter | RB=1 MΩ, RE=1 kΩ | IC ≈ 1.026 mA, VCE ≈ 8.71 V |
| A4 Emitter | RB=1 MΩ, RE=2 kΩ | IC ≈ 0.940 mA, VCE ≈ 8.03 V (IC ลดจาก A3) |
| A5 Fixed | RB=0 | แจ้ง `RB ต้องมากกว่า 0` และไม่แสดงผลเก่า |

รายละเอียดการคำนวณมือ ผลจริง วิธีตรวจ และสถานะดูที่ [`docs/validation.md`](docs/validation.md)

## การรัน tests เดิม

```powershell
python -m unittest discover -s tests -v
```

ต้องได้ `OK` 22 tests (unit 10 + web 12) — ใบงาน Lab 03 ไม่ต้องสร้าง unittest เพิ่ม

## การตรวจผ่าน Browser / MCP

- `opencode.json` ใส่ Playwright MCP ตามตัวอย่าง OpenCode V2 (`mcp.servers.playwright`)
- ต้องมี Node.js 18+ และ `npx` ก่อน restart OpenCode; ถ้าใช้ OpenCode V1 ให้ย้ายรายการไปใต้ `mcp` ตรง ๆ ตามใบงาน
- เครื่องที่พัฒนานี้ไม่มี `node`/`npx` → Playwright MCP **NOT RUN** และใช้ **OpenCode Browser** ตรวจ A1–A5 แทน
  (ใบงานให้คะแนนเท่ากัน แต่ต้องระบุวิธีจริง)

## แบบจำลองและข้อจำกัด

```
Fixed    IB = (VCC − VBE)/RB                         VE = 0
Emitter  IB = (VCC − VBE)/(RB + (β+1)RE)            VE = IE·RE
Divider  VTH = VCC·R2/(R1+R2), RTH = R1·R2/(R1+R2)
         IB = (VTH − VBE)/(RTH + (β+1)RE)           VE = IE·RE
IC = β·IB     IE = (β+1)·IB
VB = VE + VBE     VC = VCC − IC·RC     VCE = VC − VE
```

- Divider คงพฤติกรรม Lab 02 เดิม รวม `VCE_SAT = 0.3 V` และการรายงานกรณี cutoff แบบเดิม
- Fixed/Emitter จะเตือนเมื่อ `IB ≤ 0` หรือ `VCE ≤ 0.2 V` ตามใบงาน Lab 03 (ไม่ได้คำนวณค่าจริงใน cutoff/saturation)
- อินพุตที่ขาด/ไม่ใช่ตัวเลข/ไม่จำกัด/ค่าที่ต้องเป็นบวกแต่ ≤ 0 → แจ้งข้อผิดพลาด ไม่แสดงผลรอบก่อน

## หมายเหตุความปลอดภัย

Flask Debug Server ใช้ในเครื่องเท่านั้น (`127.0.0.1`) ห้ามเปิดสู่เครือข่ายภายนอก
และห้าม commit `.venv/`, `.env`, credential
