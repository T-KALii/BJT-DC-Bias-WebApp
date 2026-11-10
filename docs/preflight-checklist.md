# Pre-flight Checklist — ENG29 2121 Lab 02

> อ้างอิงหัวข้อ **2.4 Checklist ก่อนเริ่มทำงานจริง** ของใบงาน
> ปรับขั้น Commit/Push ให้ใช้ **GitHub Desktop** แทนคำสั่ง Git CLI
> ตรวจเมื่อ: 10 พ.ย. 2026 · เครื่อง: `C:\Users\B6829773` · OpenCode v2.2.6

---

## 1. ผลตรวจเครื่องจริง

| # | รายการตามใบงาน | ผล | หลักฐาน / หมายเหตุ |
|---|---|---|---|
| 1 | Git: `git --version` | ✅ ผ่าน | `git version 2.56.0.windows.4` (อยู่ที่ `%LOCALAPPDATA%\Programs\Git\cmd`, อยู่ใน User PATH แล้ว) |
| 2 | Git identity | ✅ ผ่าน | `user.name=T-KALii`, `user.email=wilaiwan.was@gmail.com` |
| 3 | GitHub: Repo เปิดได้ | ⚠️ ยังไม่ผ่าน | local repo มีที่ `Documents\GitHub\BJT DC Bias WebApp` แต่ **ยังไม่มี remote** (`git remote -v` ว่าง) และ **GitHub Desktop ยังไม่ sign in** |
| 4 | OpenCode Desktop: ส่งข้อความได้ | ✅ ผ่าน | v2.2.6, session นี้ทำงานปกติ |
| 5 | Superpowers: โหลด `brainstorming` ได้ | ✅ ผ่าน | plugin `superpowers` state = **active**, commit `22f0b46` (tag v7.0.2 = HEAD), ลงทะเบียน 16 skills |
| 6 | Python: `python --version` | ⚠️ ผ่านแบบมีเงื่อนไข | **Python 3.14.2** ที่ `C:\Program Files\Python314` (pip 25.3) — แต่ terminal ที่เปิดค้างไว้ก่อนแก้ PATH จะยังโดน WindowsApps stub |
| 7 | GitHub Desktop | ⚠️ ติดตั้งแล้ว ยังไม่พร้อมใช้ | v3.6.10 ติดตั้งแล้ว แต่ยังไม่มีบัญชี (`Preferences` มีแค่ spellcheck, ไม่มี `settings.json`) |
| 8 | Flask | ⬜ ยังไม่มี | ปกติ — จะติดตั้งใน `.venv` ของโปรเจกต์ |
| 9 | โฟลเดอร์โปรเจกต์ที่เปิดใน OpenCode | ⚠️ ผิดโฟลเดอร์ | session ปัจจุบันเปิด `Documents\Default Project` (ว่างเปล่า) ควรเปิด `Documents\GitHub\BJT DC Bias WebApp` |

---

## 2. P0 — ต้องแก้ก่อนเริ่ม Brainstorm

- [ ] **Sign in GitHub Desktop**: `File → Options → Accounts → Sign in to GitHub.com` (บัญชี `T-KALii`)
- [ ] **Add local repository** เข้า GitHub Desktop: `File → Add Local Repository…` → เลือก `Documents\GitHub\BJT DC Bias WebApp`
- [ ] **Commit `.gitignore` ก่อน Publish** (ตอนนี้ยังเป็นไฟล์ untracked — ถ้า publish ก่อน ไฟล์นี้จะไม่ขึ้น GitHub)
- [ ] **Publish repository** ให้มี remote `origin` (ตั้งชื่อ remote ว่า `BJT-DC-Bias-WebApp` ไม่ต้องมีเว้นวรรค)
- [ ] **เปิดโฟลเดอร์โปรเจกต์ให้ถูก** ใน OpenCode Desktop (ไม่ใช่ `Default Project` และไม่ใช่การเปิดไฟล์ HTML เดี่ยว)
- [ ] **สร้าง venv + ติดตั้ง Flask** (ดูข้อ 5)

---

## 3. Checklist 5 ข้อของใบงาน (สรุปในบรรทัดเดียว)

| ป้ายในใบงาน | คำสั่ง/การกระทำ | สถานะ |
|---|---|---|
| Git: `git --version` | `git --version` | ✅ |
| GitHub: Repo เปิดได้ | เปิด repo บน github.com ได้ + มี remote | ⚠️ ต้อง Publish |
| OpenCode Desktop: ส่งข้อความได้ | ทดลองส่งข้อความให้ Agent ตอบ | ✅ |
| Superpowers: โหลด brainstorming ได้ | `Use the skill tool to list skills and load brainstorming.` | ✅ |
| Python: `python --version` | `python --version` | ✅ (terminal ใหม่) |

> เกณฑ์ผ่านคือ **ทั้ง 5 ข้อ** ถ้าข้อใดยังไม่ผ่าน ห้ามเริ่มกิจกรรม Brainstorm ตามที่ใบงานระบุ

---

## 4. หมายเหตุ Python (สำคัญ)

- Python จริง: `C:\Program Files\Python314\python.exe` → **3.14.2**
- `C:\Program Files\Python314` ถูกใส่เป็นรายการ **แรก** ของ User PATH แล้ว
- ปัญหาที่เจอ: shell ที่ OpenCode spawn ไว้ **ก่อน** แก้ PATH ยัง resolve `python` ไปที่
  `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe` (Store stub) แล้วขึ้น
  `Python was not found`
- วิธีแก้:
  1. เปิด terminal ใหม่ (หรือ restart OpenCode service) ก่อนใช้ `python`
  2. ถ้ายังไม่หาย ใช้ `py` แทน → `py --version` (ได้ 3.14.2) หรือ `py -m venv .venv`
  3. หรือระบุเต็ม `"C:\Program Files\Python314\python.exe"`

---

## 5. เตรียม environment ก่อนเขียนโค้ด

```powershell
# จากโฟลเดอร์โปรเจกต์
cd "C:\Users\B6829773\Documents\GitHub\BJT DC Bias WebApp"
py -m venv .venv
.venv\Scripts\Activate.ps1        # ถ้าโดน policy: Set-ExecutionPolicy -Scope Process RemoteSigned
python -m pip install --upgrade pip
python -m pip install flask
python -c "import flask; print(flask.__version__)"
```

⛔ ห้าม commit: `.venv/`, `.env`, API key, credentials
✅ `.gitignore` ของ repo ครอบ `.venv/`, `venv/`, `__pycache__/`, `.env`, `*.key`, `.pem` ไว้แล้ว

---

## 6. GitHub Desktop — ขั้นตอน Commit / Push ที่ใช้แทน CLI

### 6.1 เตรียมครั้งแรก (ทำครั้งเดียว)

1. **Sign in**: `File → Options → Accounts → Sign in to GitHub.com`
2. **เพิ่ม repo**: `File → Add Local Repository…` → `Documents\GitHub\BJT DC Bias WebApp`
   - ถ้าแจ้งว่าไม่ใช่ git repository ให้ตรวจว่ามีโฟลเดอร์ `.git` อยู่จริง
3. **Commit `.gitignore` ก่อน**
   - แท็บ **Changes** → ตรวจรายการไฟล์ (ควรเห็นแค่ `.gitignore`)
   - Summary: `chore: add gitignore for python venv and secrets`
   - กด **Commit to main**
4. **Publish**
   - `Repository → Publish repository…`
   - Name: `BJT-DC-Bias-WebApp`
   - ❗ เอา **Keep this code private** ออก ถ้าอาจารย์ต้องเปิดดู repo
   - กด **Publish repository** → จะได้ remote `origin` + URL สำหรับส่ง Moodle

### 6.2 วงจรทำงานปกติ (ทุก Task)

1. แก้โค้ดใน OpenCode
2. กลับมา GitHub Desktop → แท็บ **Changes**
3. **ตรวจ Diff ก่อนทุกครั้ง** (คลิกไฟล์ → ดูด้านขวา) — ต้องไม่มี `.venv/`, `.env`, ไฟล์ขยะ
4. กรอก **Summary** (บังคับ) และ **Description** (ถ้าจำเป็น)
5. กด **Commit to main**
6. กด **Push origin** (มุมขวาบน) — ถ้าเพิ่งสร้าง branch ใหม่จะเป็น **Publish branch**

> Commit ถี่ ๆ ต่อ Task ดีกว่า commit ครั้งเดียวตอนจบ เพราะใบงานให้คะแนน "ประวัติการทำงาน"

### 6.3 ดึง Commit SHA ไปส่ง Moodle

- แท็บ **History** → คลิกขวาที่ commit ล่าสุด → **Copy SHA**
- หรือคลิก commit แล้วคัดลอกค่า SHA ทางขวา
- ส่ง: **Repository URL + Commit SHA** ผ่าน Moodle

### 6.4 ข้อควรระวัง

- GitHub Desktop ใช้ `.git` ชุดเดียวกับ CLI → สลับไปใช้ `git` CLI ได้ ไม่ conflict
- อย่าลืม Push — commit อย่างเดียวจะอยู่แค่เครื่องตัวเอง
- ถ้าแก้ `.gitignore` ภายหลัง ให้ commit ใหม่ (ไม่ย้อนลบไฟล์ที่ push ไปแล้วโดยไม่ตั้งใจ)
- รูปหน้าจอ/test log จะแปะใน Moodle หรือใส่ `docs/` ก็ได้ แต่ระวังขนาดไฟล์ใหญ่

---

## 7. ข้อความ Commit ที่แนะนำ (ทำทีละ Task)

```text
chore: add gitignore for python venv and secrets
feat: add dc_bias engineering calculations
test: add unit tests for dc bias math
feat: add flask routes for form and calculation
feat: add jinja template for input and results
style: add responsive css for lab 02 ui
test: add flask test client route tests
docs: add readme with setup and run steps
docs: add validation note and reflection
```

---

## 8. Definition of Done (ก่อนปิดคาบ)

- [ ] A1 `GET /` → HTTP 200 เห็นฟอร์ม
- [ ] A2 กด Calculate → ค่ามาจาก Python จริง (ไม่ hardcode)
- [ ] A3 VB/VE/VC/VCE/IC ตรงกับคำนวณอิสระ
- [ ] A4 input ผิด → Error อ่านได้ หน้าไม่ล้ม
- [ ] A5 นอก Active Region → Warning
- [ ] A6 ≥3 engineering tests + ≥1 Flask test client test ผ่านจริง (แนบ log)
- [ ] A7 clone repo ใหม่แล้วทำตาม README ได้
- [ ] Commit + Push ขึ้น GitHub เรียบร้อย
- [ ] ส่ง URL + SHA + ภาพหน้าจอ + Test log ทาง Moodle

---

## 9. ค่าอ้างอิงสำหรับตรวจผล (ชุดข้อมูลใบงาน)

VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V

| ปริมาณ | ค่า |
|---|---|
| VTH | 2.1639 V |
| RTH | 18.0328 kΩ |
| IB | 12.299 µA |
| IC | 1.2299 mA |
| IE | 1.2422 mA |
| VE | 1.2422 V |
| VB | 1.9422 V |
| VC | 9.2943 V |
| VCE | 8.0522 V |

→ อยู่ใน Forward Active (VTH > VBE และ VCE ≫ VCE,sat)
