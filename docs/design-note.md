# Design Note — BJT DC Bias Web App (Lab 02)

วันที่: 2026-11-10 · เอกสารเต็ม: `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## ปัญหา

ต้องมีเว็บที่คำนวณ DC Bias ของ BJT Voltage-Divider Bias ได้จริงภายในคาบเดียว
โดยพิสูจน์ได้ว่าตัวเลขมาจาก Python ไม่ใช่ HTML ที่ฝังค่าไว้

## ทางเลือกที่พิจารณา

| ทาง | ข้อดี | ข้อเสีย | สรุป |
|-----|-------|---------|------|
| A. Server-rendered + `POST /calculate` | โค้ดน้อย, ตรง rubric (Python คำนวณ), test ง่าย | ต้อง refresh หน้า | **เลือก** |
| B. JSON API + `fetch()` | UI ลื่น | เพิ่ม JS, error handling สองฝั่ง, test ยากขึ้น | ไม่เลือก |
| C. คำนวณด้วย JavaScript | ไม่ต้องมี backend | ขัดโจทย์ที่ต้องมี Python Backend | ไม่เลือก |

## การตัดสินใจสำคัญ

1. **แยก `dc_bias.py` ออกจาก `app.py`** — ทดสอบสมการได้โดยไม่ต้องเริ่ม Flask
   และแก้สมการโดยไม่แตะ HTML
2. **รับค่าความต้านทานเป็น Ω ล้วน** ตามสเปกใบงาน (ไม่รับ suffix `k`) เพื่อลด
   parser และชุด test ที่ต้องดูแล
3. **Cutoff รายงานสภาวะทางกายภาพ** (IB=IC=IE=0, VB=VTH, VC=VCC) ไม่ใช่ค่าติดลบ
   จากสูตร เพราะค่าติดลบสื่อความหมายผิดและทำให้ VC สูงกว่า VCC
4. **Saturation รายงานค่าตามสมการตามจริง** (ไม่ clamp) แล้วติด warning
   `VCE_SAT = 0.3 V` เพราะยังเป็น operating point ที่คำนวณได้ แต่ไม่แม่นตามแบบจำลอง
5. **HTTP 200 ทั้งกรณีสำเร็จและ error** — หน้าเว็บไม่ล้ม และผู้ใช้เห็นข้อความไทย

## โครงสร้างข้อมูล

`DcBiasResult` (frozen dataclass): `vth, rth, ib, ic, ie, vb, ve, vc, vce`
เป็น SI (V, A, Ω) — แปลงเป็น mA/µA ตอนแสดงผลเท่านั้น

## สิ่งที่ไม่ทำใน Lab นี้

Bias ชนิดอื่น, SPICE/ngspice, DC Load Line, AC/Bode, Transient, Signal Generator,
Interactive Schematic, ฐานข้อมูล, ระบบ login
