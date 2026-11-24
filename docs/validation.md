# Validation — Lab 03 · BJT DC Bias Web App (3 circuits)

ตรวจผลจาก **หน้าเว็บจริง** ที่ `http://127.0.0.1:5000/` ด้วยตาราง A1–A5 ของใบงาน
และเทียบกับค่าอ้างอิงที่คำนวณอิสระจากสมการวิศวกรรม (ไม่ได้นำค่าจากโปรแกรมมาเป็นคำตอบ)

## วิธีตรวจและเครื่องมือ

- **วิธีที่ใช้จริง: OpenCode Browser** (เปิดเว็บ เปลี่ยนโหมด กรอกฟอร์ม คลิกคำนวณ อ่าน snapshot/ข้อความบนหน้าเว็บ)
- **Playwright MCP: NOT RUN** — เครื่องนี้ไม่มี `node` / `npx` ใน PATH จึงยังเริ่ม MCP server ไม่ได้
  ไฟล์ `opencode.json` ถูกเพิ่มตามตัวอย่าง OpenCode V2 ของใบงานแล้ว เมื่อติดตั้ง Node.js 18+
  และ restart OpenCode จะเรียกใช้ `@playwright/mcp` ได้ตามคำสั่งในใบงาน
- หน่วยบนฟอร์มคือ **V และ Ω** (ไม่ต้องแปลงที่ Flask: 1 MΩ กรอกเป็น `1000000`, 1 kΩ คือ `1000`)
- เกณฑ์เปรียบเทียบ: display แสดงอย่างน้อย 2 ตำแหน่งทศนิยม → |ΔIC| ≤ 0.01 mA และ |ΔVCE| ≤ 0.02 V
  เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ
- หลักฐานภาพหน้าจอ: [`docs/evidence/A2-fixed.png`](evidence/A2-fixed.png)

## ค่าอ้างอิงอิสระ (คำนวณมือก่อนรัน)

ใช้ร่วมกันทุกกรณี: `VCC = 12 V`, `RC = 2.2 kΩ = 2200 Ω`, `β = 100`, `VBE = 0.70 V`

### A2 · Fixed Bias, RB = 1 MΩ

```
IB = (VCC − VBE)/RB = (12 − 0.70)/1,000,000 = 11.3 µA
IC = β·IB = 100 × 11.3 µA = 1.130 mA
IE = (β+1)·IB = 1.1413 mA
VE = 0 V (emitter ต่อกราวด์ตรง ๆ)
VB = VE + VBE = 0.700 V
VC = VCC − IC·RC = 12 − (1.130m)(2200) = 9.514 V
VCE = VC − VE = 9.514 V
```

### A3 · Emitter Bias, RB = 1 MΩ, RE = 1 kΩ

```
IB = (12 − 0.70)/(1,000,000 + 101×1000) = 10.26339691 µA
IC = 100·IB = 1.026339691 mA
IE = 101·IB = 1.036603088 mA
VE = IE·RE = 1.036603088 V ; VB = 1.736603088 V
VC = 12 − (1.026339691m)(2200) = 9.742052679 V
VCE = 9.742052679 − 1.036603088 = 8.705449591 V
```

### A4 · Emitter Bias, RE เปลี่ยนเป็น 2 kΩ (ตัวอื่นเท่า A3)

```
IB = 11.3/(1,000,000 + 101×2000) = 9.400998336 µA
IC = 0.940099834 mA ; IE = 0.949490166 mA
VE = 1.899001664 V ; VB = 2.599001664 V
VC = 12 − (0.940099834m)(2200) = 9.931780366 V
VCE = 9.931780366 − 1.899001664 = 8.032778702 V
```

**ทำนายก่อนรัน A4:** RE เพิ่ม → ตัวหาร `[RB + (β+1)RE]` เพิ่ม → IB ลด → IC **ลด** จาก A3
(จากประมาณ 1.026 mA เป็นประมาณ 0.940 mA)

## ค่าก่อนแก้โปรแกรม (A1 baseline, บันทึกจาก Browser ก่อนเขียน Lab 03)

`Divider · VCC=12, R1=100000, R2=22000, RC=2200, RE=1000, β=100, VBE=0.70`

| VB | VE | VC | VCE | IC | IB | IE | Region |
|----|----|----|-----|----|----|----|--------|
| 1.94 V | 1.24 V | 9.29 V | 8.05 V | 1.230 mA | 12.3 µA | 1.242 mA | Active |

VTH = 2.164 V, RTH = 18.03 kΩ — ตรงกับ README/validation ของ Lab 02 ทุกประการ

## ผลตรวจ A1–A5 (จากหน้าเว็บหลังแก้)

| กรณี | อินพุตที่ส่งจริง | คาดหมาย (อิสระ) | เห็นจริง | วิธีตรวจ | สถานะ | หลักฐาน |
|------|------------------|------------------|----------|----------|--------|---------|
| A1 · โหมดเดิม | Divider · `12, 100000, 22000, 2200, 1000, 100, 0.70` | IC 1.229858 mA, VCE 8.052155 V, Active | `IC 1.230 mA`, `VCE 8.05 V`, `VB 1.94 V`, `Active Region` | OpenCode Browser | **PASS** | ข้อความผลในหน้า `DC Bias Results — Voltage Divider Bias` |
| A2 · Fixed | Fixed · `12, RB=1000000, 2200, 100, 0.70` (ไม่มีช่อง RE) | IC 1.130 mA, VCE 9.514 V | `IC 1.130 mA`, `VCE 9.51 V`, `VE 0.00 V`, `VB 0.70 V` | OpenCode Browser | **PASS** | [`A2-fixed.png`](evidence/A2-fixed.png) + ข้อความผล |
| A3 · Emitter | Emitter · `12, RB=1000000, 2200, RE=1000, 100, 0.70` | IC 1.026340 mA, VCE 8.705450 V | `IC 1.026 mA`, `VCE 8.71 V`, `VE 1.04 V` | OpenCode Browser | **PASS** | ข้อความผลในหน้า `DC Bias Results — Emitter Bias` |
| A4 · เปลี่ยนค่าเดียว | Emitter · เหมือน A3 แต่ `RE=2000` | IC ลด → 0.940100 mA, VCE 8.032779 V | `IC 0.940 mA`, `VCE 8.03 V`, `VE 1.90 V` — ลดจริงตามทำนาย | OpenCode Browser | **PASS** | ข้อความผลหลังกดคำนวณรอบที่ 2 |
| A5 · อินพุตผิด | Fixed · `RB=0` | มีข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่โชว์ผลเดิม | `Fixed Bias: RB ต้องมากกว่า 0` / ไม่มีส่วน `DC Bias Results` | OpenCode Browser | **PASS** | ข้อความ `role="alert"` จากหน้าเว็บ |

ผลต่างสูงสุด: A3 |ΔVCE| = |8.71 − 8.705450| = 0.00455 V (< 0.02 V) และ |ΔIC| < 0.001 mA (< 0.01 mA) ทุกกรณี

## บทบาท MCP (สรุปตามใบงานข้อ 05)

- OpenCode เป็น **MCP client** (host) ที่เรียกเครื่องมือผ่าน MCP
- Playwright MCP เป็น **MCP server** ที่เปิดเครื่องมือควบคุมเบราว์เซอร์ (เช่น `browser_navigate`, `browser_snapshot`)
- เบราว์เซอร์คุยกับ Flask ด้วย **HTTP** (โหลดหน้า / POST ฟอร์ม) ต่างจาก MCP ที่ใช้สื่อสารระหว่าง OpenCode กับเครื่องมือ
- ในรอบนี้ใช้ OpenCode Browser แทน เพราะ Node.js ไม่พร้อม ผลการให้คะแนนเท่ากันตามใบงาน แต่ระบุวิธีจริงไว้ในตารางแล้ว

## สิ่งที่ AI เขียน / สิ่งที่ต้องตรวจ

- AI เขียน `calculate_fixed()` และ `calculate_emitter()` ใน `dc_bias.py`, dispatch ด้วย `if/elif` ใน `app.py._calculate()`,
  และปรับฟอร์ม/ผลใน `templates/index.html`
- จุดที่ควรตรวจด้วยความรู้ Engineering Electronics: สูตร `IB` ของทั้งสามแบบ, `VE = 0` เฉพาะ Fixed,
  หน่วย Ω/A/V ก่อนส่งเข้าฟังก์ชัน, และการแปลงเป็น mA/µA เฉพาะตอนแสดงผล (`app.py._display()`)
- การแปลงหน่วย: ฟอร์มใช้ Ω/V อยู่แล้ว → **ไม่ต้องคูณ 1000 ซ้ำ** ที่จุดรับข้อมูล (ใบงานข้อ 03 อนุญาตให้ใช้หน่วยเดิม)
- รันชุดทดสอบLab 02 เดิม: `python -m unittest discover -s tests -v` → **OK 22 tests** (ไม่ได้เพิ่ม unittest ใหม่ตามใบงาน)

---

# Validation — Lab 04 · BJT CE Amplifier Simulator v1

ตรวจหน้า `/simulator` จริงที่ `http://127.0.0.1:5000/simulator` ตามตาราง **B1–B8** ของใบงาน
และแยกผล **SPICE จริง**ออกจากค่าอ้างอิง **Analytical Lab 03** อย่างชัดเจน

## สภาพแวดล้อมและแหล่งที่มาของผล

- เว็บเสิร์ฟ: Flask บน `127.0.0.1:5000` (`py -m flask --app app run --port 5000`)
- เครื่องมือที่ใช้จริง: **OpenCode Browser** (navigate → snapshot → fill/select → click → อ่านข้อความ/DOM → screenshot)
- **Playwright MCP: NOT RUN** — ไม่มี `node` / `npx` ใน PATH ของเครื่องนี้ จึงไม่ได้เรียก tool ชื่อ `browser_*` ของ Playwright MCP และจะไม่อ้างผลว่าใช้ MCP
- **Impeccable: NOT RUN** — ไม่ได้ติดตามที่ผู้ใช้เลือกไม่ติดตั้ง tool นี้ จึงปรับ CSS ด้วยมือและใช้ screenshot ของ Browser เป็นหลักฐาน UI
- ngspice: **47** ติดตั้งที่ `%USERPROFILE%\Tools\ngspice-47\Spice64\bin\ngspice.exe`
  (เวอร์ชันอ่านจากโฟลเดอร์ที่ติดตั้ง; `ngspice --version` / `-v` ไม่คืนค่าที่เชื่อถือได้บนเครื่องนี้)
- BJT model ที่ใช้จริง: `.MODEL QNPN NPN(IS=1E-14 BF=100 VAF=100)`
  **แบบจำลองนี้กำหนดขึ้นเองในโปรเจกต์ ไม่ใช่ไฟล์ `.cir`/`.mod` ที่อาจารย์ให้มา** จึงต้อง disclosure ทุกครั้งที่เทียบผล
- ENGINE status ที่หน้าเว็บ: `READY · ngspice 47` → `RUNNING · ngspice` ขณะ POST → `SUCCESS · ngspice 47` หรือ `ERROR · ngspice`
- ทุกตัวเลข SPICE มาจาก netlist ที่ส่งให้ ngspice แล้วอ่านกลับจาก log รอบนั้น
  (`spice_engine.run_simulation()` → `parse_op()` / `parse_ac()` / `parse_tran()` → `charts.py`)
  ไม่มี trace หรือค่าสำเร็จที่ hard-code ใน template
- netlist แต่ละรันถูกเขียนใน temp directory แยกกัน เรียก ngspice ด้วย argument list `['-b','-o',log,cir]`
  มี timeout 30 วินาที และตรวจ `returncode`, ข้อความ `Error:`, สรุปเวลารันก่อนยอมรับผล

## ตารางผล B1–B8

| Case | Method | Input | Expected / Reference | Observed | Evidence | Status |
|------|--------|-------|----------------------|----------|----------|--------|
| B1 · Regression | OpenCode Browser เปลี่ยน `?circuit=divider/fixed/emitter` แล้ว POST `/calculate` | Divider `12, 100000, 22000, 2200, 1000, 100, 0.70`; Fixed `12, RB=1000000, 2200, 100, 0.70`; Emitter `12, RB=1000000, 2200, RE=1000, 100, 0.70` | ค่าอ้างอิงอิสระ A1–A3 ในหัวข้อก่อนหน้า: Divider IC 1.230 mA / VCE 8.05 V; Fixed IC 1.130 mA / VCE 9.51 V; Emitter IC 1.026 mA / VCE 8.71 V | Divider `VB 1.94, VE 1.24, VC 9.29, VCE 8.05 V, IC 1.230 mA, Active`; Fixed `VB 0.70, VE 0.00, VC/VCE 9.51 V, IC 1.130 mA`; Emitter `VB 1.74, VE 1.04, VC 9.74, VCE 8.71 V, IC 1.026 mA`; เปลี่ยนโหมดได้ทุกครั้ง | [`B1-divider.jpg`](evidence/B1-divider.jpg), [`B1-fixed.jpg`](evidence/B1-fixed.jpg), [`B1-emitter.jpg`](evidence/B1-emitter.jpg), ข้อความ `DC Bias Results — …` | **PASS** |
| B2 · DC SPICE | OpenCode Browser POST `/simulator/run` โหมด `dc` | Base case `VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, Cin/Cout 10 µF`; `.OP` | ต้องมี `SUCCESS · ngspice 47`, model card, VB/VE/VC/VCE/IC จาก node voltage ของ ngspice และแยกตาราง Analytical ออกต่างหาก | `READY · ngspice 47` ก่อนรัน → `SUCCESS · ngspice 47`; SPICE `VB 1.949, VE 1.289, VC 9.189, VCE 7.900 V, IC 1.278 mA (จาก RC drop)`; Analytical `1.942, 1.242, 9.294, 8.052 V, 1.230 mA`; แสดง model card และ `<details>` netlist/log | [`B2-dc.jpg`](evidence/B2-dc.jpg) + netlist ในหน้า: `VIN vin 0 DC 0`, `Q1 … QNPN`, `.OP` | **PASS** |
| B3 · Change RE | เปลี่ยนเฉพาะ `RE` จาก `1000` → `1500` Ω แล้ว POST ซ้ำโหมด `dc` | เหมือน B2 แต่ `RE=1500 Ω` | Operating point ต้องเปลี่ยน ไม่ใช่ค่าค้าง และ netlist ต้องสะท้อน RE ใหม่ | ก่อน `VB 1.949, VE 1.289, VC 9.189, VCE 7.900 V, IC 1.278 mA`; หลัง `VB 2.014, VE 1.363, VC 10.019, VCE 8.656 V, IC 0.900 mA`; netlist ยืนยัน `RE emitter 0 1500`; Analytical หลังเปลี่ยน `2.008, 1.308, 10.100, 8.792 V, 0.864 mA` | [`B3-re1500.jpg`](evidence/B3-re1500.jpg) + บรรทัด netlist ที่อ่านจาก DOM | **PASS** |
| B4 · AC | เปลี่ยนโหมดเป็น `ac` แล้ว POST; อ่าน SVG `<polyline>` และข้อความแกน | `10 mV peak`, sweep `100 Hz–1 MHz`, `.AC DEC 5` | แกน Frequency (Hz, log), Gain (dB), Phase (°) ต้องมีหน่วย และค่าต้องมาจาก `.PRINT AC` จริง | `SUCCESS · ngspice 47`; Bode 21 pts, `100–1000000 Hz`; Gain `4.86…4.86 dB`, Phase `-3.1…-3.1°`, ที่ ~1 kHz `4.86 dB / -3.1°`; DOM พบ 2 polyline (gain/phase) และ label `Bode plot: gain 4.86 to 4.86 dB, phase -3.1 to -3.1 degrees`; netlist มี `.PRINT AC VDB(VIN) VP(VIN)` และ `.PRINT AC VDB(VOUT) VP(VOUT)` | [`B4-ac.jpg`](evidence/B4-ac.jpg) + netlist/aria-label จากหน้าเว็บ | **PASS** |
| B5 · Transient | เปลี่ยนโหมดเป็น `transient` แล้ว POST ที่สัญญาณฐาน | `10 mV peak`, `1 kHz`, `Stop 2 ms`, `Step 1 µs`, `.TRAN` | เห็น Vin/Vout ตามเวลา มีป้าย Time (ms)/แรงดัน (V) และสัญญาณกลับเฟสตาม CE | `SUCCESS · ngspice 47`; chart `Vin -0.0100…0.0100 V`, `Vout -0.0175…0.0175 V`, `2.00 ms shown`, 2 polyline ~2008 points; ข้อความ `Vin 20.00 mVpp · Vout 35.00 mVpp · Vin ที่ +peak ตรงกับ Vout ด้านลบ → สัญญาณกลับเฟส`; netlist `SIN(0 0.01 1000)` และ `.TRAN 1e-06 0.002 0 1e-06` | [`B5-tran.jpg`](evidence/B5-tran.jpg) + aria-label/netlist จาก DOM | **PASS** |
| B6 · Change Source | เปลี่ยน Amplitude `10 → 20 mV` และ Frequency `1 → 2 kHz` แล้ว POST ซ้ำ | `20 mV peak`, `2 kHz`; stop/step เท่าเดิม | waveform ต้องเปลี่ยนตามค่าที่ตั้ง ไม่ใช่กราฟคงที่ | `SUCCESS · ngspice 47`; netlist เปลี่ยนเป็น `SIN(0 0.02 2000)`; `Vin 40.00 mVpp · Vout 69.99 mVpp`; chart label เปลี่ยนเป็น `Vin -0.0200…0.0200 V`, `Vout -0.0350…0.0350 V` (ก่อนหน้า ±0.0100/±0.0175 V) | [`B5-tran.jpg`](evidence/B5-tran.jpg) เทียบ [`B6-source-changed.jpg`](evidence/B6-source-changed.jpg) | **PASS** |
| B7 · Invalid / Fail | ใส่ `RE=0` แล้ว POST โหมด `transient` | `RE=0 Ω` | ต้องแจ้ง error, ไม่ค้าง, ไม่แสดง SUCCESS ปลอมหรือกราฟเก่า | status เปลี่ยนเป็น `ERROR · ngspice`; alert `การจำลองไม่สำเร็จ / RE: ต้องมากกว่า 0 / ไม่มีผลเก่าหรือกราฟเก่าที่แสดงเป็น Success ในรอบนี้`; ตรวจ DOM แล้ว `body.innerText.includes('SUCCESS') === false` และ `svg.plot.length === 0` | [`B7-invalid.jpg`](evidence/B7-invalid.jpg) + ค่า DOM ข้างต้น | **PASS** |
| B8 · UI (รันใหม่หลังรวมหน้า C1) | เปิด `/simulator` → เปลี่ยนโหมดเป็น `ac` → รันจริง → ตรวจ desktop `1296×886` และ iframe กว้าง `390 px` ของ **หน้ารวมเดียวกัน** | Desktop `1296×886`; phone frame `390 px` | กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่มีเนื้อหาสำคัญถูกตัด และยังเห็นทั้งสอง workspace | Desktop: `scrollWidth 1281 ≤ innerWidth 1296` (ไม่ overflow), plot width `892 px`, aria-label `Bode plot: gain 4.86 to 4.86 dB, phase -3.1 to -3.1 degrees`, พบ `Frequency (Hz, log scale)`, `Gain (dB)`, `Phase (°)`, status `SUCCESS · ngspice 47`; phone: `scrollWidth 375 ≤ 390` (ไม่ overflow), plot width `303 px`, หน่วย/ปุ่ม/ผล AC อ่านได้, เห็น `id="lab3"`, `id="lab4"` และ nav 3 ลิงก์, status เดิม | [`B8-desktop.jpg`](evidence/B8-desktop.jpg) (1296×886), [`B8-mobile-390.jpg`](evidence/B8-mobile-390.jpg) (375×3697, ภาพทั้งหน้ารวมใน iframe 390 px) | **PASS** |

## หลักฐานว่ากราฟมาจาก ngspice จริง ไม่ใช่ Mock

- B4: `.PRINT AC VDB(VIN) VP(VIN)` และ `.PRINT AC VDB(VOUT) VP(VOUT)` ถูกเขียนลง netlist;
  `parse_ac()` จับคู่ frequency ทีละจุดแล้วคำนวณ `gain = VDB(VOUT) − VDB(VIN)` และ `phase = VP(VOUT) − VP(VIN)`
  จากตารางที่ ngspice พิมพ์ ผลที่ DOM อ่านได้คือ 21 จุดตรงกับ `.AC DEC 5 100 1e+06`
- B5/B6: `.PRINT TRAN V(VIN) V(VOUT)` ถูกเขียนลง netlist; `parse_tran()` อ่านคอลัมน์ `time`, `v(vin)`, `v(vout)`
  แล้วส่งเข้า `waveform_svg()` ตรง ๆ การเปลี่ยน `SIN(0 0.01 1000)` เป็น `SIN(0 0.02 2000)` ทำให้ netlist,
  ช่วงแกน และข้อความ mVpp เปลี่ยนตาม
- Template ไม่มีตัวเลขผลลัพธ์ฝังไว้; มีเพียง `{{ result.* }}`, `{{ summary.* }}` และ SVG ที่สร้างจาก series จริง

## ปัญหาที่พบระหว่าง acceptance และการแก้

- พบ bug จริงตอน B5 ครั้งแรก: ngspice แบบ batch พิมพ์หัวตาราง `.PRINT TRAN` ซ้ำทุกประมาณ 58 แถว
  parser เดิมเก็บเฉพาะ page แรก ทำให้กราฟตัดเหลือ `0.05 ms` และ `Vin 1.97 mVpp / Vout 3.44 mVpp`
  ทั้งที่รันครบ `2 ms`
- เขียน failing test `test_parse_tran_merges_paginated_headers` ก่อน → ได้ `2 != 3` จริง → แก้ `_parse_tables()`
  ให้รวม chunk ที่มี header ชุดเดียวกัน → รันชุดทดสอบเขียว → restart Flask → **recapture B5/B6 ใหม่**
  ค่าที่บันทึกในตารางด้านบนเป็นผลหลังแก้แล้ว ไม่ใช่ screenshot เก่าที่ตัด
- ไม่ได้เปลี่ยนค่าทางฟิสิกส์เพื่อบังคับให้ตรงกับ Analytical; SPICE กับ Lab 03 ใช้คนละ model และตั้งใจรายงานความต่าง

## ความคลาดเคลื่อนและข้อจำกัด

- ผลต่าง SPICE–Analytical ที่ base case: IC `1.278 − 1.230 = 0.048 mA`, VCE `7.900 − 8.052 = −0.152 V`
  เกิดจาก BJT model แบบ exponential/VAF เทียบกับ β/VBE คงที่ จึงไม่ถือว่า FAIL
- `IC` ของ DC SPICE คำนวณจาก `(VCC − VC)/RC` ไม่ใช่คำสั่ง PRINT device current โดยตรง
- `.ac` ใช้ 5 จุดต่อ decade คงที่ และ amplitude มีผลต่อ operating point แต่ gain วัดเป็น dB difference
- `.tran` plot แสดงช่วง time ที่เลือกทั้งหมด; ค่า mVpp ในข้อความสรุปวัดจาก 60% หลังของข้อมูลเพื่อหลีกเลี่ยง startup transient
- ถ้า ngspice หาย/รันไม่สำเร็จ/timeout หรือ log ไม่มี analysis summary ระบบจะขึ้น `ERROR · ngspice` และไม่แสดงผลเก่า
- ผล B1–B8 เป็นของเครื่องนี้กับ ngspice 47; การเปลี่ยน model card หรือเวอร์ชัน solver ต้องรัน acceptance ใหม่

## ภาพหน้าจอที่ใช้เป็นหลักฐาน

`B1-divider.jpg`, `B1-fixed.jpg`, `B1-emitter.jpg`, `B2-dc.jpg`, `B3-re1500.jpg`,
`B4-ac.jpg`, `B5-tran.jpg`, `B6-source-changed.jpg`, `B7-invalid.jpg`,
`B8-desktop.jpg`, `B8-mobile-390.jpg`, `C1-combined-desktop.jpg` อยู่ใน [`docs/evidence/`](evidence/)

B8 ถูก **ถ่ายใหม่หลังรวมหน้า C1** (เดิมเป็นของหน้า `/simulator` แยก) เพื่อให้หลักฐานตรงกับโค้ดปัจจุบัน
- desktop เป็น viewport จริง 1296×886 และ mobile เป็น iframe กว้าง 390 px ของหน้ารวมเดียวกัน

## สิ่งที่ AI เขียน/แก้ และสิ่งที่ตรวจเอง

- AI เขียน `spice_engine.py` (netlist/subprocess/parser/error), `charts.py` (SVG จาก array จริง),
  route `/simulator` และ `/simulator/run` ใน `app.py`, `templates/simulator.html`, `static/app.js`,
  CSS status/plot และเพิ่ม tests ก่อน implement ตาม TDD
- AI แก้ parser paginated `.tran` หลังพบ bug จาก browser จริง พร้อมเพิ่ม failing test ก่อนแก้
- นักศึกษาตรวจเอง: ค่า Lab 03 เทียบสูตรในหัวข้อ A1–A4, netlist ที่ส่งจริง, model card ที่ไม่ใช่ของอาจารย์,
  ความกลับเฟสใน waveform, การเปลี่ยนแปลงเมื่อเปลี่ยน RE/amplitude/frequency,
  และว่า error path ไม่โชว์ SUCCESS ปลอม
---

## C1 · ตรวจการรวมหน้า Lab 03 + Lab 04 (หลัง B1–B8)

ตามที่ผู้ใช้ขอให้ **"อยู่รวมกัน"** ทางหน้าเว็บ: ทั้งสอง workspace อยู่ในหน้าเดียวที่ `/`
และ `/simulator` ยังเปิดเหมือนเดิม (ตอนนี้ render หน้ารวมเดียวกัน)

| รายการ | วิธีตรวจ (OpenCode Browser) | ผลที่เห็นจริง | สถานะ |
|--------|----------------------------|---------------|--------|
| หน้ารวมมี 2 ส่วน | เปิด `http://127.0.0.1:5000/` แล้ว snapshot/DOM | พบ `id="lab3"` และ `id="lab4"` พร้อมกัน; nav ข้ามส่วน 3 ลิงก์; console error `0` | **PASS** |
| POST Lab 03 แล้วไม่เสีย Lab 04 | กรอก Divider `12, 100000, 22000, 2200, 1000, 100, 0.7` → กด **Calculate DC Bias** | URL `/calculate`; `DC Bias Results — Voltage Divider Bias`, `VCE 8.05 V`;  ยังพบ `id="lab4"`, `form[action='/simulator/run']`, status `READY · ngspice 47` | **PASS** |
| POST Lab 04 แล้วไม่เสีย Lab 03 | ในหน้าเดียวกันส่งฟอร์ม DC `.op` (base case) | URL `/simulator/run`; `SUCCESS · ngspice 47`; ตาราง `DC Operating Point / SPICE` คู่กับ `Analytical Reference / LAB 03`, `VCE 7.900 V`; ยังพบ `id="lab3"` และ `form[action='/calculate']` | **PASS** |
| Status ไม่หลุดไป Lab 03 | อ่าน `static/app.js` และ DOM หลัง POST | script ฟังเฉพาะ `form[action='/simulator/run']`; กด Calculate DC Bias ไม่เปลี่ยน status เป็น `RUNNING` | **PASS** |

หลักฐานภาพ: [`C1-combined-desktop.jpg`](evidence/C1-combined-desktop.jpg) (full-page หลังรัน DC จริง)
วิธีตรวจเหมือน B1–B8 คือ OpenCode Browser **ไม่ใช่ Playwright MCP** (ยัง **NOT RUN** เพราะไม่มี `node`/`npx`)
และ **Impeccable: NOT RUN** ตามที่ผู้ใช้เลือก

### สิ่งที่ AI แก้สำหรับ C1 (TDD)

- เขียน failing test 4 ตัวใน `tests/test_simulator_routes.py` ก่อน: หน้า `/` ต้องมีสอง workspace,
  `/simulator` ต้องมีสอง workspace, POST `/calculate` ต้องยังมีปุ่ม Run, POST `/simulator/run` ต้องยังมีปุ่ม Calculate
  → รันแล้วล้มจริง (`id="lab3"` ไม่พบ) ก่อนแก้
- เพิ่ม test ที่ 5 ให้ JS ฟังเฉพาะฟอร์ม `/simulator/run` → ล้มจริงก่อนแก้ `static/app.js`
- แยก template เป็น `combined.html` + `_lab3.html` + `_lab4.html`; `index.html` และ `simulator.html` เป็นแค่ include
- `app.py` ใช้ `_lab3_context()` / `_sim_context()` แล้วรวม context ด้วย prefix `lab3_` / `sim_`
  แล้ว `_render_combined()` ส่งให้ template — ไม่ย้ายสมการหรือ hardcode ตัวเลขเพิ่ม
- ผลทดสอบสุดท้าย: `py -m unittest discover -s tests` → **OK 49 tests** (Lab 03 เดิม 22 + Lab 04 เดิม 22 + C1 อีก 5)
