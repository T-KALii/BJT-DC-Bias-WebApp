"""DC bias calculations for BJT common-emitter bias circuits.

Physics only: this module must not import Flask or know anything about HTTP/HTML.

Conventions (shared by all three circuits):
    resistances in ohm, voltages in volt, currents in ampere.

The result is a dict.  It also supports attribute access (``result.ic``) so the
Lab 2 tests and templates keep working while every function returns a dict as
required by Lab 03.
"""

import math

# Lab 02 divider keeps its original threshold so existing results do not change.
VCE_SAT = 0.3  # V
# Lab 03 uses the limit stated in the lab sheet for the two new circuits.
VCE_ACTIVE_LIMIT = 0.2  # V

_FINITE_MESSAGE = "ค่าที่กรอกต้องเป็นตัวเลขที่อยู่ในช่วงที่คำนวณได้"


class BiasResult(dict):
    """Dict of results with attribute access for backward compatibility."""

    __slots__ = ()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def _require_finite(values, message=_FINITE_MESSAGE):
    if not all(math.isfinite(value) for value in values):
        raise ValueError(message)


def _check_common(vcc, rc, beta, vbe):
    """Check the inputs used by every bias circuit."""
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    if rc <= 0:
        raise ValueError("RC ต้องมากกว่า 0")
    if beta <= 0:
        raise ValueError("β ต้องมากกว่า 0")
    if vbe < 0 or vbe >= vcc:
        raise ValueError("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")


def _warnings_for(ib, vce, mode):
    """Lab 03: only warn when the forward-active model is outside its range."""
    warnings = []
    if ib <= 0:
        warnings.append(f"IB ≤ 0: แบบจำลอง Forward-Active อาจใช้ไม่ได้ ({mode})")
    if vce <= VCE_ACTIVE_LIMIT:
        warnings.append(
            f"VCE ≤ {VCE_ACTIVE_LIMIT} V: "
            f"แบบจำลอง Forward-Active อาจใช้ไม่ได้ ({mode})"
        )
    return tuple(warnings)


def calculate(vcc, r1, r2, rc, re, beta, vbe):
    """Voltage-divider bias (Lab 02).  Equations and results are unchanged."""
    _require_finite((vcc, r1, r2, rc, re, beta, vbe))
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    if r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0:
        raise ValueError("ค่าความต้านทานต้องมากกว่า 0")
    if r1 + r2 <= 0:
        raise ValueError("R1 + R2 ต้องมากกว่า 0")
    _check_common(vcc, rc, beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    _require_finite((vth, rth), "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้")

    ib = (vth - vbe) / (rth + (beta + 1) * re)

    if ib <= 0:
        # Cutoff: report the physical state instead of negative currents.
        return BiasResult(
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

    return BiasResult(
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


def calculate_fixed(vcc, rb, rc, beta, vbe):
    """Fixed bias: RB from VCC to base, emitter tied directly to ground.

    IB = (VCC - VBE) / RB
    VE = 0 V, VB = VBE
    """
    _require_finite((vcc, rb, rc, beta, vbe))
    _check_common(vcc, rc, beta, vbe)
    if rb <= 0:
        raise ValueError("RB ต้องมากกว่า 0")

    ib = (vcc - vbe) / rb
    _require_finite((ib,), "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้")

    ic = beta * ib
    ie = (beta + 1) * ib
    ve = 0.0
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    warnings = _warnings_for(ib, vce, "Fixed Bias")
    _require_finite(
        (ic, ie, vb, ve, vc, vce),
        "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้",
    )

    return BiasResult(
        vth=None,
        rth=None,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region="warning" if warnings else "active",
        warnings=warnings,
    )


def calculate_emitter(vcc, rb, rc, re, beta, vbe):
    """Emitter bias with one supply: RB to base and RE from emitter to ground.

    IB = (VCC - VBE) / [RB + (beta + 1) * RE]
    """
    _require_finite((vcc, rb, rc, re, beta, vbe))
    _check_common(vcc, rc, beta, vbe)
    if rb <= 0 or re <= 0:
        raise ValueError("RB และ RE ต้องมากกว่า 0")

    denominator = rb + (beta + 1) * re
    _require_finite(
        (denominator,), "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้"
    )
    ib = (vcc - vbe) / denominator
    _require_finite((ib,), "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้")

    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    warnings = _warnings_for(ib, vce, "Emitter Bias")
    _require_finite(
        (ic, ie, vb, ve, vc, vce),
        "ค่าที่กรอกทำให้ผลลัพธ์เกินช่วงที่คำนวณได้",
    )

    return BiasResult(
        vth=None,
        rth=None,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region="warning" if warnings else "active",
        warnings=warnings,
    )
