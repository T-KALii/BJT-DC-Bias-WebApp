"""ngspice adapter for the Lab 4 CE voltage-divider simulator.

This module owns netlist generation, the external ``subprocess`` call and
parsing of the real solver output.  It never returns fabricated plot data:
every number in ``series`` comes from a completed ngspice run.

Physics of the Lab 3 analytical path stays in ``dc_bias.py``; Flask only
dispatches to this adapter and renders the returned values.
"""
from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

MODEL_NAME = "QNPN"
MODEL_CARD = ".MODEL QNPN NPN(IS=1E-14 BF=100 VAF=100)"
NGSPICE_VERSION = "47"

NUMBER_RE = re.compile(r"^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$")

# Portable fallback for this course setup; NGSPICE_EXECUTABLE and PATH win.
_LOCAL_NGSPICE = (
    Path.home() / "Tools" / "ngspice-47" / "Spice64" / "bin" / "ngspice.exe"
)


class SpiceEngineError(RuntimeError):
    """Raised when ngspice is missing, fails, times out or yields no data."""


def find_ngspice() -> str | None:
    """Resolve the external solver without ever using a shell command string."""
    configured = os.environ.get("NGSPICE_EXECUTABLE")
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which("ngspice")
    if found:
        return found
    if _LOCAL_NGSPICE.is_file():
        return str(_LOCAL_NGSPICE)
    return None


def _number(raw, label: str, *, positive: bool = True) -> float:
    text = str(raw).strip()
    if not NUMBER_RE.match(text):
        raise ValueError(f"{label}: กรุณากรอกเป็นตัวเลขเท่านั้น")
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"{label}: ตัวเลขต้องอยู่ในช่วงที่คำนวณได้")
    if positive and value <= 0:
        raise ValueError(f"{label}: ต้องมากกว่า 0")
    return value


def validate_params(mode: str, raw: dict) -> dict:
    """Validate form text and convert course-friendly units into SI.

    Form units: V, Ω, µF, mV, kHz, ms, µs.  Nothing from the form reaches
    the netlist until it has passed this function.
    """
    if mode not in {"dc", "ac", "transient"}:
        raise ValueError("โหมดไม่รู้จัก กรุณาเลือก DC, AC หรือ Transient")

    p = {
        "vcc": _number(raw.get("vcc"), "VCC"),
        "r1": _number(raw.get("r1"), "R1"),
        "r2": _number(raw.get("r2"), "R2"),
        "rc": _number(raw.get("rc"), "RC"),
        "re": _number(raw.get("re"), "RE"),
        "rl": _number(raw.get("rl"), "RL"),
        "cin_uf": _number(raw.get("cin"), "Cin"),
        "cout_uf": _number(raw.get("cout"), "Cout"),
    }
    p["cin"] = p.pop("cin_uf") * 1e-6
    p["cout"] = p.pop("cout_uf") * 1e-6

    if mode in {"ac", "transient"}:
        p["amp"] = _number(raw.get("amp"), "Amplitude") * 1e-3
    if mode == "ac":
        p["fstart"] = _number(raw.get("fstart"), "Frequency start")
        p["fstop"] = _number(raw.get("fstop"), "Frequency stop")
        p["freq"] = p["fstart"]
        if p["fstop"] <= p["fstart"]:
            raise ValueError("Frequency stop ต้องมากกว่า Frequency start")
        if p["fstop"] > 1e9:
            raise ValueError("Frequency stop ต้องไม่เกิน 1 GHz")
    if mode == "transient":
        p["freq"] = _number(raw.get("freq"), "Frequency") * 1e3
        p["tstop"] = _number(raw.get("tstop"), "Stop time") * 1e-3
        p["tstep"] = _number(raw.get("tstep"), "Time step") * 1e-6
        if p["tstep"] >= p["tstop"]:
            raise ValueError("Time step ต้องน้อยกว่า Stop time")
    return p


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def build_netlist(mode: str, p: dict) -> str:
    """Build one netlist containing exactly one analysis directive."""
    lines = [
        "* CE voltage-divider amplifier reference - Lab 4",
        f"VCC vcc 0 DC {_fmt(p['vcc'])}",
    ]
    if mode == "dc":
        lines.append("VIN vin 0 DC 0")
    elif mode == "ac":
        lines.append(f"VIN vin 0 DC 0 AC {_fmt(p['amp'])}")
    elif mode == "transient":
        lines.append(
            f"VIN vin 0 DC 0 SIN(0 {_fmt(p['amp'])} {_fmt(p['freq'])})"
        )
    else:
        raise SpiceEngineError("โหมดไม่รู้จัก")

    lines.extend([
        f"R1 vcc base {_fmt(p['r1'])}",
        f"R2 base 0 {_fmt(p['r2'])}",
        f"RC vcc collector {_fmt(p['rc'])}",
        f"RE emitter 0 {_fmt(p['re'])}",
        f"RL vout 0 {_fmt(p['rl'])}",
        f"CIN vin base {_fmt(p['cin'])}",
        f"COUT collector vout {_fmt(p['cout'])}",
        f"Q1 collector base emitter 0 {MODEL_NAME}",
        MODEL_CARD,
    ])

    if mode == "dc":
        lines.append(".OP")
    elif mode == "ac":
        lines.append(f".AC DEC 5 {_fmt(p['fstart'])} {_fmt(p['fstop'])}")
        lines.append(".PRINT AC VDB(VIN) VP(VIN)")
        lines.append(".PRINT AC VDB(VOUT) VP(VOUT)")
    elif mode == "transient":
        lines.append(
            f".TRAN {_fmt(p['tstep'])} {_fmt(p['tstop'])} 0 {_fmt(p['tstep'])}"
        )
        lines.append(".PRINT TRAN V(VIN) V(VOUT)")
    lines.append(".END")
    return "\n".join(lines) + "\n"


def _write_netlist(path: Path, text: str) -> None:
    path.write_text(text, encoding="ascii")


def _parse_tables(log: str) -> list[dict]:
    tables: list[dict] = []
    lines = log.splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().lower().startswith("index"):
            continue
        # 'Index' is a real numeric column in ngspice tables, so keep it;
        # dropping it shifts every following value by one column.
        headers = line.split()
        if not headers:
            continue
        table = {name: [] for name in headers}
        started = False
        for row in lines[index + 1:]:
            cells = row.split()
            numeric = len(cells) >= len(headers) and all(
                NUMBER_RE.match(cell) for cell in cells[:len(headers)]
            )
            if not numeric:
                # ngspice puts a dashed separator between header and rows.
                separator = all(all(ch in "-= " for ch in cell) for cell in cells)
                if started or not separator:
                    break
                continue
            for name, cell in zip(headers, cells):
                table[name].append(float(cell))
            started = True
        if not table[headers[0]]:
            continue
        # Batch ngspice repeats the header every page; those chunks belong
        # to one continuous sweep and must not be dropped.
        existing = next((t for t in tables if list(t) == headers), None)
        if existing is None:
            tables.append(table)
        else:
            for name, values in table.items():
                existing[name].extend(values)
    return tables


def parse_op(log: str, p: dict) -> dict:
    """Read the operating point printed by ngspice after .OP."""
    start = log.find("Node")
    end = log.find("Source", start)
    section = log[start:end] if start >= 0 and end > start else log
    nodes: dict[str, float] = {}
    for line in section.splitlines():
        cells = line.split()
        if len(cells) == 2 and NUMBER_RE.match(cells[1]):
            nodes[cells[0].lower()] = float(cells[1])
    required = {"vcc", "base", "emitter", "collector"}
    if not required.issubset(nodes):
        raise SpiceEngineError("ไม่พบผล DC operating point ใน ngspice log")

    vcc = nodes["vcc"]
    vb = nodes["base"]
    ve = nodes["emitter"]
    vc = nodes["collector"]
    ic_a = (vcc - vc) / p["rc"]
    return {
        "vcc": vcc, "vb": vb, "ve": ve, "vc": vc, "vce": vc - ve,
        "ic_ma": ic_a * 1e3,
        "source": "ngspice .op node voltages; IC derived from RC drop",
    }


def parse_ac(log: str) -> dict:
    """Merge the two .PRINT AC tables; gain/phase use VIN as reference."""
    tables = _parse_tables(log)
    vin = next((t for t in tables if "vdb(vin)" in t), None)
    vout = next((t for t in tables if "vdb(vout)" in t), None)
    if vin is None or vout is None:
        raise SpiceEngineError("ไม่พบตาราง .PRINT AC ใน ngspice log")
    if not vin["frequency"] or not vout["frequency"]:
        raise SpiceEngineError("ตาราง .PRINT AC ไม่มีข้อมูล")

    series = []
    count = min(len(vin["frequency"]), len(vout["frequency"]))
    for i in range(count):
        series.append({
            "frequency_hz": vin["frequency"][i],
            "gain_db": vout["vdb(vout)"][i] - vin["vdb(vin)"][i],
            "phase_deg": vout["vp(vout)"][i] - vin["vp(vin)"][i],
            "vin_db": vin["vdb(vin)"][i],
            "vout_db": vout["vdb(vout)"][i],
        })
    return {
        "series": series,
        "vin_reference": "VDB(VIN) / VP(VIN)",
        "source": "ngspice .ac + .PRINT AC; gain = VDB(VOUT) - VDB(VIN)",
    }


def parse_tran(log: str) -> dict:
    """Read the time/VIN/VOUT table printed by .PRINT TRAN."""
    table = next((t for t in _parse_tables(log) if "v(vin)" in t), None)
    if table is None or not table["time"]:
        raise SpiceEngineError("ไม่พบตาราง .PRINT TRAN ใน ngspice log")
    series = [
        {
            "time_s": t,
            "vin_v": v,
            "vout_v": o,
        }
        for t, v, o in zip(table["time"], table["v(vin)"], table["v(vout)"])
    ]
    return {
        "series": series,
        "source": "ngspice .tran + .PRINT TRAN V(VIN) V(VOUT)",
    }


def run_simulation(mode: str, raw: dict, *, executable: str | None = None,
                   timeout: int = 30) -> dict:
    """Run a real ngspice process in an isolated working directory."""
    params = validate_params(mode, raw)
    exe = executable or find_ngspice()
    if not exe:
        raise SpiceEngineError(
            "ไม่พบ ngspice — กรุณาติดตั้งแล้วตั้ง NGSPICE_EXECUTABLE หรือเพิ่มลง PATH"
        )
    if Path(exe).is_file() and not os.access(exe, os.X_OK):
        raise SpiceEngineError("ngspice ไม่มีสิทธิ์รัน")

    netlist = build_netlist(mode, params)
    with tempfile.TemporaryDirectory(prefix="lab04-ngspice-") as tmp:
        workdir = Path(tmp)
        cir = workdir / "ce.cir"
        log_path = workdir / "run.log"
        _write_netlist(cir, netlist)
        env = dict(os.environ)
        bin_dir = str(Path(exe).parent)
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        try:
            completed = subprocess.run(
                [exe, "-b", "-o", str(log_path), str(cir)],
                cwd=bin_dir,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SpiceEngineError(f"ngspice รันเกิน {timeout} วินาที") from exc
        except OSError as exc:
            raise SpiceEngineError(f"เรียก ngspice ไม่ได้: {exc}") from exc

        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        if completed.returncode != 0 or not log:
            detail = (completed.stderr or "").strip()[:300]
            raise SpiceEngineError(
                f"ngspice รันไม่สำเร็จ (exit {completed.returncode}) {detail}".strip()
            )
        if "Error:" in log or "run simulation(s) aborted" in log.lower():
            raise SpiceEngineError("ngspice รายงาน Error ไม่แสดงผลจำลองเป็น Success")
        if "Total analysis time" not in log and "Total elapsed time" not in log:
            raise SpiceEngineError("ngspice ไม่ได้รัน analysis จริง (ไม่มีสรุปเวลา)")

        if mode == "dc":
            result = parse_op(log, params)
        elif mode == "ac":
            result = parse_ac(log)
        else:
            result = parse_tran(log)

    result.update({
        "status": "success",
        "engine": "ngspice",
        "version": NGSPICE_VERSION,
        "model": MODEL_CARD,
        "mode": mode,
        "netlist": netlist,
        "log_excerpt": log[-1200:],
        "parameters": params,
    })
    return result
