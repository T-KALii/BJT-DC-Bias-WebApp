import math

from flask import Flask, render_template, request

import charts
import spice_engine
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

# Lab 4 fixture: course-friendly units shown in the simulator form.
SIM_DEFAULT = {
    "vcc": "12", "r1": "100000", "r2": "22000", "rc": "2200",
    "re": "1000", "rl": "10000", "cin": "10", "cout": "10",
    "amp": "10", "freq": "1", "fstart": "100", "fstop": "1000000",
    "tstop": "2", "tstep": "1",
}
SIM_MODES = ("dc", "ac", "transient")
SIM_MODE_LABELS = {"dc": "DC · .op", "ac": "AC · .ac", "transient": "Transient · .tran"}


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


def _lab3_context(error=None, values=None, result=None, circuit=DEFAULT_CIRCUIT):
    """Context for the Lab 03 section of the combined page."""
    return {
        "circuit": circuit,
        "mode_label": CIRCUIT_LABELS[circuit],
        "fields": CIRCUIT_FIELDS[circuit],
        "field_info": FIELD_INFO,
        "result": result,
        "error": error,
        "values": values or {},
        "display": _display(result) if result is not None else None,
        "show_divider_meta": (
            circuit == "divider" and result is not None and result["vth"] is not None
        ),
    }


@app.get("/")
def index():
    requested = request.args.get("circuit", DEFAULT_CIRCUIT)
    circuit = requested if requested in CIRCUIT_LABELS else DEFAULT_CIRCUIT
    return _render_combined(lab3={"circuit": circuit})


@app.post("/calculate")
def calculate_view():
    requested = request.form.get("circuit", DEFAULT_CIRCUIT)
    if requested not in CIRCUIT_LABELS:
        return _render_combined(lab3={
            "circuit": DEFAULT_CIRCUIT,
            "error": "โหมดวงจรไม่รู้จัก กรุณาเลือก Voltage Divider, Fixed หรือ Emitter Bias",
            "values": {"circuit": requested},
        })

    circuit = requested
    label = CIRCUIT_LABELS[circuit]
    fields = CIRCUIT_FIELDS[circuit]
    values = {"circuit": circuit}
    values.update({name: request.form.get(name, "") for name in fields})

    if any(not values[name].strip() for name in fields):
        names = ", ".join(FIELD_INFO[name][0].split(" (")[0] for name in fields)
        return _render_combined(lab3={
            "circuit": circuit,
            "values": values,
            "error": f"{label}: กรุณากรอกค่าให้ครบทุกช่อง ({names})",
        })

    try:
        parsed = {name: float(values[name]) for name in fields}
    except ValueError:
        return _render_combined(lab3={
            "circuit": circuit,
            "values": values,
            "error": f"{label}: กรุณากรอกเป็นตัวเลขเท่านั้น (เช่น 12 หรือ 100000)",
        })

    if not all(math.isfinite(value) for value in parsed.values()):
        return _render_combined(lab3={
            "circuit": circuit,
            "values": values,
            "error": f"{label}: กรุณากรอกตัวเลขที่อยู่ในช่วงที่คำนวณได้ (เช่น 12 หรือ 100000)",
        })

    try:
        result = _calculate(circuit, parsed)
    except ValueError as exc:
        return _render_combined(lab3={
            "circuit": circuit, "values": values, "error": f"{label}: {exc}",
        })

    return _render_combined(lab3={"circuit": circuit, "values": values, "result": result})


def _analytical_reference(values):
    """Lab 3 divider result, shown only as a labelled DC reference."""
    try:
        parsed = {name: float(values[name]) for name in ("vcc", "r1", "r2", "rc", "re")}
        if not all(math.isfinite(item) for item in parsed.values()):
            return None
        if min(parsed.values()) <= 0:
            return None
        return calculate(
            vcc=parsed["vcc"], r1=parsed["r1"], r2=parsed["r2"],
            rc=parsed["rc"], re=parsed["re"], beta=100.0, vbe=0.70,
        )
    except (ValueError, KeyError, TypeError, ZeroDivisionError):
        return None


def _sim_summary(result, mode):
    """Small derived labels so the template never computes physics."""
    if not result or not result.get("series"):
        return {}
    series = result["series"]
    if mode == "ac":
        gains = [item["gain_db"] for item in series]
        phases = [item["phase_deg"] for item in series]
        closest = min(series, key=lambda item: abs(item["frequency_hz"] - 1000.0))
        return {
            "gain_min": min(gains), "gain_max": max(gains),
            "phase_min": min(phases), "phase_max": max(phases),
            "at_1k": closest,
        }
    if mode == "transient":
        tail = series[int(len(series) * 0.4):] or series
        vins = [item["vin_v"] for item in tail]
        vouts = [item["vout_v"] for item in tail]
        mean_out = sum(vouts) / len(vouts)
        peak_index = max(range(len(vins)), key=lambda i: vins[i])
        inverted = vouts[peak_index] < mean_out
        return {
            "vin_pp": max(vins) - min(vins),
            "vout_pp": max(vouts) - min(vouts),
            "phase_note": ("Vin ที่ +peak ตรงกับ Vout ด้านลบ → สัญญาณกลับเฟส"
                           if inverted else
                           "Vin ที่ +peak ตรงกับ Vout ด้านบวก → ไม่กลับเฟสในช่วงที่วัด"),
            "samples": series[:8],
        }
    return {}


def _sim_context(values=None, mode="dc", error=None, result=None):
    """Context for the Lab 04 section of the combined page."""
    values = {**SIM_DEFAULT, **(values or {})}
    if mode not in SIM_MODES:
        mode = "dc"
    return {
        "defaults": SIM_DEFAULT,
        "values": values,
        "mode": mode,
        "modes": SIM_MODES,
        "mode_labels": SIM_MODE_LABELS,
        "error": error,
        "result": result,
        "engine_version": spice_engine.NGSPICE_VERSION,
        "summary": _sim_summary(result, mode),
        "analytical": _analytical_reference(values) if mode == "dc" else None,
        "bode_svg": charts.bode_svg(result["series"]) if result and mode == "ac" else "",
        "wave_svg": (
            charts.waveform_svg(result["series"])
            if result and mode == "transient" else ""
        ),
    }


def _render_combined(lab3=None, sim=None):
    """Render both workspaces in one page; each submission updates its own half."""
    lab3_context = _lab3_context(**(lab3 or {}))
    sim_context = _sim_context(**(sim or {}))
    context = {f"lab3_{name}": value for name, value in lab3_context.items()}
    context.update({f"sim_{name}": value for name, value in sim_context.items()})
    return render_template("combined.html", **context)


@app.get("/simulator")
def simulator_form():
    # Old bookmark still works; it now shows both workspaces in one page.
    return _render_combined()


@app.post("/simulator/run")
def simulator_run():
    mode = request.form.get("mode", "dc")
    values = {name: request.form.get(name, SIM_DEFAULT[name]) for name in SIM_DEFAULT}
    try:
        result = spice_engine.run_simulation(mode, values)
    except (ValueError, spice_engine.SpiceEngineError) as exc:
        # Never show a previous successful run together with an error.
        return _render_combined(sim={"values": values, "mode": mode, "error": str(exc)})
    return _render_combined(sim={"values": values, "mode": mode, "result": result})


if __name__ == "__main__":
    app.run(debug=True)
