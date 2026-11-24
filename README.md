# BJT DC Bias Web App + CE Amplifier Simulator — Lab 03 / Lab 04

เว็บแอป Flask ที่คำนวณ **DC Operating Point** ของ BJT NPN Common-Emitter ได้ 3 แบบในหน้าเดียว
ต่อยอดจาก Lab 02 (Voltage Divider Bias) โดยผลของโหมดเดิมยังเหมือนเดิมทุกประการ

Lab 04 เพิ่มหน้า `/simulator` ที่เรียก **ngspice จริง** สำหรับ `.op`, `.ac` และ `.tran`
ของวงจร CE voltage-divider อ้างอิง โดยผล SPICE แยกป้ายออกจากผล Analytical Lab 03 อย่างชัดเจน

วิชา ENG29 2121 · Lab 03 (Forward-Active β/VBE คงที่) · Lab 04 (ngspice 47)

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
app.py                  Flask routes: /calculate และ /simulator, /simulator/run
dc_bias.py              สมการ Lab 03 ล้วน: calculate(), calculate_fixed(), calculate_emitter()
spice_engine.py         Lab 04: สร้าง netlist, เรียก ngspice, parse log, จัดการ error
charts.py               Lab 04: วาด SVG Bode/waveform จาก array ที่ parse จริง (ไม่มี dependency เพิ่ม)
templates/index.html    หน้า Lab 03 + ลิงก์ไป /simulator
templates/simulator.html หน้า Lab 04: mode, inputs, status, ผล SPICE/Analytical, netlist/log
static/app.js           เปลี่ยน status เป็น RUNNING ขณะรอ ngspice (ไม่สร้างตัวเลขผลลัพธ์)
static/style.css        หน้าตาเว็บและกราฟ
tests/                  44 tests (Lab 03 เดิม 22 + Lab 04 ใหม่ 22)
docs/validation.md      ตาราง A1–A5 (Lab 03) + B1–B8 (Lab 04) + ค่าอ้างอิง/หลักฐาน Browser
docs/evidence/          ภาพหน้าจอผลการตรวจ
requirements.txt        Flask (ไม่เพิ่ม plotting library)
opencode.json           ตั้งค่า Playwright MCP (OpenCode V2)
```

## การติดตั้ง

ต้องมี Python 3.10 ขึ้นไป (พัฒนา/ทดสอบบน Python 3.14.2) และ **ngspice 47** เฉพาะหน้า Lab 04

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> ถ้าเครื่องขึ้น *"Python was not found"* จาก Microsoft Store ให้ใช้ `py -m venv .venv`
> แล้วรันคำสั่งต่อไปด้วย `.venv\Scripts\python.exe` แทน `python`

### ติดตั้ง ngspice (Lab 04)

- เครื่องที่ใช้ตรวจติดตั้ง ngspice 47 ไว้ที่
  `%USERPROFILE%\Tools\ngspice-47\Spice64\bin\ngspice.exe`
- โค้ดจะหาตามลำดับ: `NGSPICE_EXECUTABLE` → `PATH` → path สำรองข้างบน
- ถ้าติดตั้งที่อื่น ให้ตั้งก่อนรัน Flask:

```powershell
$env:NGSPICE_EXECUTABLE = "C:\path\to\ngspice.exe"
```

- ไม่ต้องเพิ่ม matplotlib/plotly: กราฟเป็น SVG ที่สร้างจากค่าที่ ngspice พิมพ์มา
- หน้า Lab 03 ยังรันได้แม้ไม่มี ngspice; เฉพาะ `/simulator/run` ที่จะรายงาน `ERROR · ngspice`

## การรันเว็บ

```powershell
python -m flask --app app run --debug
```

เปิด [http://127.0.0.1:5000/](http://127.0.0.1:5000/) สำหรับ Lab 03 หรือ
[http://127.0.0.1:5000/simulator](http://127.0.0.1:5000/simulator) สำหรับ Lab 04
แล้วเลือกโหมด กรอกค่า กดปุ่มคำนวณ/รัน

> **ลิงก์เปิดไม่ได้?** `127.0.0.1` หมายถึงเครื่องที่รัน Flask จึงต้องเปิดคำสั่ง `python -m flask --app app run --debug` ค้างไว้ก่อนกดลิงก์ ถ้าปิด Terminal หรือกดจากอีกเครื่องจะขึ้น *site can't be reached* ดูวิธีแก้ที่หัวข้อ **แก้ปัญหาลิงก์เปิดไม่ได้** ด้านล่างครับ

## Lab 04 · CE Amplifier Simulator

เปิด `/simulator` เลือก `DC · .op`, `AC · .ac` หรือ `Transient · .tran` แล้วกด **Run Simulation**
ทุกโหมดใช้วงจรอ้างอิงเดียวกัน (voltage-divider CE) และส่ง netlist จริงให้ ngspice 47

| ช่อง | หน่วยที่กรอก |
|------|---------------|
| VCC, R1, R2, RC, RE, RL | V, Ω |
| Cin, Cout | µF |
| Amplitude peak | mV |
| Frequency (transient) | kHz |
| Frequency start/stop (AC) | Hz |
| Stop time / Time step | ms / µs |

Base case ที่ใช้ตรวจ: `VCC 12 V`, `R1 100 kΩ`, `R2 22 kΩ`, `RC 2.2 kΩ`,
`RE 1 kΩ`, `RL 10 kΩ`, `Cin = Cout = 10 µF`, `10 mV peak`, `1 kHz`;
AC sweep `100 Hz–1 MHz` (5 pts/decade), transient `2 ms` step `1 µs`

### สิ่งที่หน้าเว็บแสดง

- **Engine status**: `READY · ngspice 47` → `RUNNING · ngspice` → `SUCCESS · ngspice 47` หรือ `ERROR · ngspice`
- **Result provenance**: ตาราง `SPICE` แยกจาก `Analytical LAB 03` และมีข้อความระบุว่าค่าอ่านจาก log รอบนี้
- **BJT model ที่ใช้จริง**: `.MODEL QNPN NPN(IS=1E-14 BF=100 VAF=100)`
  → **แบบจำลองที่กำหนดเองในโปรเจกต์ ไม่ใช่ model card จากอาจารย์** ห้ามตีความว่าเป็นค่ามาตรฐานที่ตรวจแล้ว
- `<details>` **Netlist และ ngspice log** ของรันนั้น ๆ เปิดดูได้ในหน้าผลลัพธ์
- กราฟ Bode/wave เป็น SVG ที่สร้างจากตาราง `.PRINT AC` / `.PRINT TRAN` ที่ parse ได้ จึงไม่ใช่ mock plot

### ตัวอย่างค่าที่ใช้ตรวจ (VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V)

| กรณี | อินพุต | ผลที่คาดหวัง |
|------|--------|--------------|
| A1 Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | IC ≈ 1.230 mA, VCE ≈ 8.05 V |
| A2 Fixed | RB=1 MΩ | IC ≈ 1.130 mA, VCE ≈ 9.51 V |
| A3 Emitter | RB=1 MΩ, RE=1 kΩ | IC ≈ 1.026 mA, VCE ≈ 8.71 V |
| A4 Emitter | RB=1 MΩ, RE=2 kΩ | IC ≈ 0.940 mA, VCE ≈ 8.03 V (IC ลดจาก A3) |
| A5 Fixed | RB=0 | แจ้ง `RB ต้องมากกว่า 0` และไม่แสดงผลเก่า |

รายละเอียดการคำนวณมือ ผลจริง วิธีตรวจ A1–A5 (Lab 03) และ B1–B8 (Lab 04) ดูที่
[`docs/validation.md`](docs/validation.md) และภาพใน [`docs/evidence/`](docs/evidence/)

## การรัน tests

```powershell
py -m unittest discover -s tests -v
```

ต้องได้ `OK 44 tests` = Lab 03 เดิม 22 (unit 10 + web 12) + Lab 04 ใหม่ 22
(netlist/parser/error/route/chart) ชุดทดสอบ Lab 03 เดิมยังผ่านเหมือนเดิม

## การตรวจผ่าน Browser / MCP

- `opencode.json` ใส่ Playwright MCP ตามตัวอย่าง OpenCode V2 (`mcp.servers.playwright`)
- ต้องมี Node.js 18+ และ `npx` ก่อน restart OpenCode; ถ้าใช้ OpenCode V1 ให้ย้ายรายการไปใต้ `mcp` ตรง ๆ ตามใบงาน
- เครื่องที่พัฒนานี้ไม่มี `node`/`npx` → Playwright MCP **NOT RUN** สำหรับทั้ง A1–A5 และ B1–B8
  ใช้ **OpenCode Browser** เปิด Flask localhost จริงและบันทึกข้อความ/DOM/screenshot แทน
- **Impeccable: NOT RUN** (ไม่ได้ติดตั้งตามที่ผู้ใช้เลือก) → ปรับ CSS ด้วยมือและใช้ภาพ B8 _before/after เป็นหลักฐาน
  ไม่มีการอ้างว่า tool นี้ตรวจ UI ให้
- รายละเอียดและค่าที่อ่านจริงอยู่ใน [`docs/validation.md`](docs/validation.md)

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

### ข้อจำกัด Lab 04

- ผลต่าง SPICE กับ Analytical ไม่ได้ถูกบังคับให้เท่ากันเพราะคนละ BJT model (ดู disclosure ข้างบน)
- `IC` ของ `.op` คำนวณจากแรงดันตกที่ `RC` ไม่ใช่การพิมพ์กระแส device โดยตรง
- `.ac` sweep ใช้ 5 จุดต่อ decade คงที่; `.tran` ใช้ stop/step ตามฟอร์มและมี timeout 30 วินาที
- ถ้า ngspice ไม่พร้อม/รันไม่สำเร็จ/timeout หน้าจะขึ้น `ERROR · ngspice` และไม่โชว์กราฟหรือ SUCCESS เก่า
- ngspice ถูกเรียกด้วย argument list ใน isolated temp dir ไม่ใช้ shell string

## แก้ปัญหาลิงก์เปิดไม่ได้

ลิงก์ [http://127.0.0.1:5000/](http://127.0.0.1:5000/) ชี้ไปที่ **localhost** จึงเปิดได้เฉพาะบนเครื่องที่รัน Flask อยู่ และต้องรันค้างไว้ตอนกดลิงก์

```powershell
cd <โฟลเดอร์โปรเจกต์>
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m flask --app app run --debug
```

เมื่อเห็น `Running on http://127.0.0.1:5000` แล้วค่อยกดลิงก์ หรือพิมพ์ URL ใน Browser

- ถ้าขึ้น *Python was not found* ให้ใช้ `py -m venv .venv` แล้วรัน `.venv\Scripts\python.exe -m flask --app app run --debug` แทน
- ถ้า Port 5000 ถูกใช้งานอยู่ ให้เติม `--port 5001` แล้วเปิด `http://127.0.0.1:5001/` แทน
- ถ้าต้องการให้เครื่องอื่นหรือคนอื่นเปิดได้ ต้อง deploy แอปหรือใช้ tunnel (เช่น ngrok) แล้วเปลี่ยนลิงก์ใน README เป็น URL สาธารณะ เพราะ `127.0.0.1` ของแต่ละเครื่องคนละที่กัน

## หมายเหตุความปลอดภัย

Flask Debug Server ใช้ในเครื่องเท่านั้น (`127.0.0.1`) ห้ามเปิดสู่เครือข่ายภายนอก
และห้าม commit `.venv/`, `.env`, credential
