"""DC bias calculations for a BJT common-emitter voltage-divider bias circuit.

Physics only: this module must not import Flask or know anything about HTTP/HTML.
"""

from dataclasses import dataclass
import math

VCE_SAT = 0.3  # V — collector-emitter saturation threshold used for warnings


def _require_finite(values: tuple[float, ...], message: str) -> None:
    if not all(math.isfinite(value) for value in values):
        raise ValueError(message)


@dataclass(frozen=True)
class DcBiasResult:
    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...] = ()


def calculate(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> DcBiasResult:
    """Return the DC operating point of a voltage-divider biased NPN BJT."""
    _require_finite(
        (vcc, r1, r2, rc, re, beta, vbe),
        "ค่าที่กรอกต้องเป็นตัวเลขที่อยู่ในช่วงที่คำนวณได้",
    )
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    if r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0:
        raise ValueError("ค่าความต้านทานต้องมากกว่า 0")
    if r1 + r2 <= 0:
        raise ValueError("R1 + R2 ต้องมากกว่า 0")
    if beta <= 0:
        raise ValueError("β ต้องมากกว่า 0")
    if vbe < 0 or vbe >= vcc:
        raise ValueError("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    _require_finite(
        (vth, rth), "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้"
    )

    ib = (vth - vbe) / (rth + (beta + 1) * re)

    if ib <= 0:
        # Cutoff: no base current means no collector/emitter current. Report the
        # physical state instead of the negative numbers the formula would give.
        return DcBiasResult(
            vth=vth,
            rth=rth,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vth,
            ve=0.0,
            vc=vcc,
            vce=vcc,
            region="cutoff",
            warnings=(
                "VTH ≤ VBE: ทรานซิสเตอร์ไม่นำกระแส "
                "แบบจำลอง Forward-Active ใช้ไม่ได้",
            ),
        )

    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    if vce <= VCE_SAT:
        region = "saturation"
        warnings = (
            f"VCE ใกล้/ต่ำกว่า VCE(sat) = {VCE_SAT} V: "
            "ผล DC Bias ไม่แม่นตามแบบจำลอง Forward-Active",
        )
    else:
        region = "active"
        warnings = ()

    _require_finite(
        (ib, ic, ie, vb, ve, vc, vce),
        "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้",
    )

    return DcBiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )
