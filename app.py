import math

from flask import Flask, render_template, request

from dc_bias import calculate

app = Flask(__name__)

FIELD_NAMES = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")


def _display(result):
    """Pre-format numbers with units for the template."""
    return {
        "vb": f"{result.vb:.2f}",
        "ve": f"{result.ve:.2f}",
        "vc": f"{result.vc:.2f}",
        "vce": f"{result.vce:.2f}",
        "ic": f"{result.ic * 1e3:.3f}",
        "ib": f"{result.ib * 1e6:.1f}",
        "ie": f"{result.ie * 1e3:.3f}",
        "vth": f"{result.vth:.3f}",
        "rth": f"{result.rth / 1e3:.2f}",
    }


@app.get("/")
def index():
    return render_template("index.html", result=None, error=None, values={}, display=None)


@app.post("/calculate")
def calculate_view():
    values = {name: request.form.get(name, "") for name in FIELD_NAMES}

    if any(not values[name].strip() for name in FIELD_NAMES):
        return (
            render_template(
                "index.html",
                error="กรุณากรอกค่าให้ครบทุกช่อง (VCC, R1, R2, RC, RE, β, VBE)",
                result=None,
                values=values,
                display=None,
            ),
            200,
        )

    try:
        parsed = {name: float(values[name]) for name in FIELD_NAMES}
    except ValueError:
        return (
            render_template(
                "index.html",
                error="กรุณากรอกเป็นตัวเลขเท่านั้น (เช่น 12 หรือ 100000)",
                result=None,
                values=values,
                display=None,
            ),
            200,
        )

    if not all(math.isfinite(value) for value in parsed.values()):
        return (
            render_template(
                "index.html",
                error="กรุณากรอกตัวเลขที่อยู่ในช่วงที่คำนวณได้ (เช่น 12 หรือ 100000)",
                result=None,
                values=values,
                display=None,
            ),
            200,
        )

    try:
        result = calculate(**parsed)
    except ValueError as exc:
        return (
            render_template(
                "index.html", error=str(exc), result=None, values=values, display=None
            ),
            200,
        )

    return render_template(
        "index.html",
        result=result,
        error=None,
        values=values,
        display=_display(result),
    )


if __name__ == "__main__":
    app.run(debug=True)
