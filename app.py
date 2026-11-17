import math

from flask import Flask, render_template, request

from dc_bias import calculate, calculate_emitter, calculate_fixed

app = Flask(__name__)

DEFAULT_CIRCUIT = "divider"

CIRCUIT_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

# label, placeholder — the form still uses V and ohm, so there is no conversion.
FIELD_INFO = {
    "vcc": ("VCC (V)", "เช่น 12"),
    "r1": ("R1 (Ω) — ต่อ VCC ถึง Base", "เช่น 100000"),
    "r2": ("R2 (Ω) — ต่อ Base ถึง Ground", "เช่น 22000"),
    "rb": ("RB (Ω) — ต่อ VCC ถึง Base", "เช่น 1000000"),
    "rc": ("RC (Ω) — ต่อ VCC ถึง Collector", "เช่น 2200"),
    "re": ("RE (Ω) — ต่อ Emitter ถึง Ground", "เช่น 1000"),
    "beta": ("β (hFE)", "เช่น 100"),
    "vbe": ("VBE (V)", "เช่น 0.70"),
}

CIRCUIT_FIELDS = {
    "divider": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "rc", "re", "beta", "vbe"),
}


def _calculate(circuit, p):
    """Select the physics function with if/elif; never guess an unknown mode."""
    if circuit == "divider":
        return calculate(
            vcc=p["vcc"], r1=p["r1"], r2=p["r2"], rc=p["rc"],
            re=p["re"], beta=p["beta"], vbe=p["vbe"],
        )
    elif circuit == "fixed":
        return calculate_fixed(
            vcc=p["vcc"], rb=p["rb"], rc=p["rc"],
            beta=p["beta"], vbe=p["vbe"],
        )
    elif circuit == "emitter":
        return calculate_emitter(
            vcc=p["vcc"], rb=p["rb"], rc=p["rc"], re=p["re"],
            beta=p["beta"], vbe=p["vbe"],
        )
    raise ValueError("โหมดวงจรไม่รู้จัก กรุณาเลือก Voltage Divider, Fixed หรือ Emitter Bias")


def _display(result):
    """Pre-format numbers with units for the template."""
    display = {
        "vb": f"{result['vb']:.2f}",
        "ve": f"{result['ve']:.2f}",
        "vc": f"{result['vc']:.2f}",
        "vce": f"{result['vce']:.2f}",
        "ic": f"{result['ic'] * 1e3:.3f}",
        "ib": f"{result['ib'] * 1e6:.1f}",
        "ie": f"{result['ie'] * 1e3:.3f}",
    }
    if result["vth"] is not None:
        display["vth"] = f"{result['vth']:.3f}"
        display["rth"] = f"{result['rth'] / 1e3:.2f}"
    return display


def _render(error=None, values=None, result=None, circuit=DEFAULT_CIRCUIT):
    return render_template(
        "index.html",
        circuit=circuit,
        mode_label=CIRCUIT_LABELS[circuit],
        fields=CIRCUIT_FIELDS[circuit],
        field_info=FIELD_INFO,
        result=result,
        error=error,
        values=values or {},
        display=_display(result) if result is not None else None,
        show_divider_meta=(
            circuit == "divider" and result is not None and result["vth"] is not None
        ),
    )


@app.get("/")
def index():
    requested = request.args.get("circuit", DEFAULT_CIRCUIT)
    circuit = requested if requested in CIRCUIT_LABELS else DEFAULT_CIRCUIT
    return _render(circuit=circuit)


@app.post("/calculate")
def calculate_view():
    requested = request.form.get("circuit", DEFAULT_CIRCUIT)
    if requested not in CIRCUIT_LABELS:
        return _render(
            circuit=DEFAULT_CIRCUIT,
            error="โหมดวงจรไม่รู้จัก กรุณาเลือก Voltage Divider, Fixed หรือ Emitter Bias",
            values={"circuit": requested},
        )

    circuit = requested
    label = CIRCUIT_LABELS[circuit]
    fields = CIRCUIT_FIELDS[circuit]
    values = {"circuit": circuit}
    values.update({name: request.form.get(name, "") for name in fields})

    if any(not values[name].strip() for name in fields):
        names = ", ".join(FIELD_INFO[name][0].split(" (")[0] for name in fields)
        return _render(
            circuit=circuit,
            values=values,
            error=f"{label}: กรุณากรอกค่าให้ครบทุกช่อง ({names})",
        )

    try:
        parsed = {name: float(values[name]) for name in fields}
    except ValueError:
        return _render(
            circuit=circuit,
            values=values,
            error=f"{label}: กรุณากรอกเป็นตัวเลขเท่านั้น (เช่น 12 หรือ 100000)",
        )

    if not all(math.isfinite(value) for value in parsed.values()):
        return _render(
            circuit=circuit,
            values=values,
            error=f"{label}: กรุณากรอกตัวเลขที่อยู่ในช่วงที่คำนวณได้ (เช่น 12 หรือ 100000)",
        )

    try:
        result = _calculate(circuit, parsed)
    except ValueError as exc:
        return _render(circuit=circuit, values=values, error=f"{label}: {exc}")

    return _render(circuit=circuit, values=values, result=result)


if __name__ == "__main__":
    app.run(debug=True)
