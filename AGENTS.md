# AGENTS.md — กติกาการทำงานใน repo นี้

## สถาปัตยกรรม

- `dc_bias.py` = ฟิสิกส์เท่านั้น ห้าม import Flask/Jinja และห้ามรู้จัก HTTP
- `app.py` = HTTP: parse ฟอร์ม, จับ `ValueError`, ส่ง context ให้ template
- `templates/index.html` = การแสดงผล ห้ามฝังสมการทางไฟฟ้า
- `static/style.css` = หน้าตาเท่านั้น
- `tests/` = ทุกพฤติกรรมใหม่ต้องมี test

## กฎการแก้โค้ด

1. เขียน failing test ก่อนทุกฟีเจอร์ (TDD) แล้วรันให้เห็นว่าล้มจริง
2. รัน `python -m unittest discover -s tests -v` ให้เขียวก่อน commit
3. ห้าม hardcode ผลลัพธ์ใน template — ตัวเลขทั้งหมดต้องมาจาก `dc_bias.py`
4. ค่าคงที่ทางฟิสิกส์ (เช่น `VCE_SAT`) ประกาศที่ `dc_bias.py` ที่เดียว
5. รักษาขอบเขต Lab 02: ไม่เพิ่ม AC, Transient, SPICE, Bias ชนิดอื่น

## Git

- Commit ผ่าน **GitHub Desktop** (Changes → ตรวจ diff → Summary → Commit to main)
- ห้าม commit `.venv/`, `__pycache__/`, `.env`, credential
- ข้อความ commit ใช้ภาษาอังกฤษ รูปแบบ imperative เช่น `Add DC bias calculation`

## ภาษา

- ข้อความที่ผู้ใช้เห็น (UI, error, warning) เป็นภาษาไทย อ่านรู้เรื่อง ไม่ใช้ศัพท์ดิบ
- โค้ด ตัวแปร และ docstring ใช้ภาษาอังกฤษ
