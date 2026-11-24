"""Small dependency-free SVG plotters for real ngspice result arrays.

This module only draws values that were parsed from a completed simulation.
It never invents, interpolates beyond the data or hard-codes an engineering
result.  Templates embed the returned SVG without doing any physics.
"""
from __future__ import annotations

import math


def _span(values: list[float], pad: float = 0.08) -> tuple[float, float]:
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        lo -= 1.0
        hi += 1.0
    delta = (hi - lo) * pad
    return lo - delta, hi + delta


def _xy(points, x_lo, x_hi, y_lo, y_hi, left, top, width, height) -> str:
    def sx(x):
        return left + (x - x_lo) / (x_hi - x_lo) * width

    def sy(y):
        return top + height - (y - y_lo) / (y_hi - y_lo) * height

    return " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in points)


def bode_svg(series: list[dict], width: int = 760, height: int = 300) -> str:
    """Gain (dB) and phase (deg) versus log frequency (Hz)."""
    if not series:
        return ""
    freqs = [math.log10(item["frequency_hz"]) for item in series]
    gains = [item["gain_db"] for item in series]
    phases = [item["phase_deg"] for item in series]
    x_lo, x_hi = min(freqs), max(freqs)
    if math.isclose(x_lo, x_hi):
        x_lo -= 0.5
        x_hi += 0.5
    g_lo, g_hi = _span(gains)
    p_lo, p_hi = _span(phases)

    left, top, plot_w, plot_h = 64, 26, width - 118, height - 74
    gain_pts = list(zip(freqs, gains))
    phase_pts = list(zip(freqs, phases))
    gain_line = _xy(gain_pts, x_lo, x_hi, g_lo, g_hi, left, top, plot_w, plot_h)
    phase_line = _xy(phase_pts, x_lo, x_hi, p_lo, p_hi, left, top, plot_w, plot_h)

    ticks = []
    decade_start = math.floor(x_lo)
    decade_end = math.ceil(x_hi)
    for decade in range(decade_start, decade_end + 1):
        x = left + (decade - x_lo) / (x_hi - x_lo) * plot_w
        if 0 <= x <= width:
            ticks.append(
                f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+plot_h}" '
                f'stroke="#dce7ee"/>'
                f'<text x="{x:.1f}" y="{top+plot_h+18}" font-size="11" '
                f'text-anchor="middle" fill="#486275">1e{decade}</text>'
            )
    first = series[0]
    last = series[-1]
    return f'''<svg class="plot" viewBox="0 0 {width} {height}" role="img"
  aria-label="Bode plot: gain {gains[0]:.2f} to {gains[-1]:.2f} dB, phase {phases[0]:.1f} to {phases[-1]:.1f} degrees">
  <rect width="{width}" height="{height}" fill="#f9fcfd"/>
  {''.join(ticks)}
  <line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#7f9bad"/>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#7f9bad"/>
  <polyline points="{gain_line}" fill="none" stroke="#167e93" stroke-width="2.6"/>
  <polyline points="{phase_line}" fill="none" stroke="#c77a35" stroke-width="2.2" stroke-dasharray="5 3"/>
  <text x="{left}" y="16" font-size="12" fill="#135c57">Gain (dB) · {g_lo:.1f} … {g_hi:.1f}</text>
  <text x="{left+plot_w}" y="16" font-size="12" text-anchor="end" fill="#814521">Phase (°) · {p_lo:.0f} … {p_hi:.0f}</text>
  <text x="{left+plot_w/2:.1f}" y="{height-8}" font-size="12" text-anchor="middle" fill="#486275">Frequency (Hz, log scale)</text>
  <text x="{left+plot_w+8}" y="{top+14}" font-size="11" fill="#486275">{len(series)} pts</text>
  <text x="{left+plot_w+8}" y="{top+30}" font-size="11" fill="#486275">{first['frequency_hz']:.0f}–{last['frequency_hz']:.0f} Hz</text>
</svg>'''


def waveform_svg(series: list[dict], width: int = 760, height: int = 300) -> str:
    """Vin and Vout versus time from a real .tran run."""
    if not series:
        return ""
    times = [item["time_s"] for item in series]
    vins = [item["vin_v"] for item in series]
    vouts = [item["vout_v"] for item in series]
    x_lo, x_hi = min(times), max(times)
    if x_hi == x_lo:
        x_hi = x_lo + 1e-9
    y_lo, y_hi = _span(vins + vouts)

    left, top, plot_w, plot_h = 64, 26, width - 118, height - 74
    vin_line = _xy(list(zip(times, vins)), x_lo, x_hi, y_lo, y_hi, left, top, plot_w, plot_h)
    vout_line = _xy(list(zip(times, vouts)), x_lo, x_hi, y_lo, y_hi, left, top, plot_w, plot_h)
    zero_y = top + plot_h - (0 - y_lo) / (y_hi - y_lo) * plot_h
    span_ms = (x_hi - x_lo) * 1e3
    return f'''<svg class="plot" viewBox="0 0 {width} {height}" role="img"
  aria-label="Transient plot: Vin {min(vins):.4f} to {max(vins):.4f} volts, Vout {min(vouts):.4f} to {max(vouts):.4f} volts over {span_ms:.2f} milliseconds">
  <rect width="{width}" height="{height}" fill="#f9fcfd"/>
  <line x1="{left}" y1="{zero_y:.1f}" x2="{left+plot_w}" y2="{zero_y:.1f}" stroke="#b7c9d5"/>
  <line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#7f9bad"/>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#7f9bad"/>
  <polyline points="{vin_line}" fill="none" stroke="#0c8e83" stroke-width="2.2"/>
  <polyline points="{vout_line}" fill="none" stroke="#c77a35" stroke-width="2.2"/>
  <text x="{left}" y="16" font-size="12" fill="#0c6f68">Vin (V) teal</text>
  <text x="{left+150}" y="16" font-size="12" fill="#814521">Vout (V) orange</text>
  <text x="{left+plot_w/2:.1f}" y="{height-8}" font-size="12" text-anchor="middle" fill="#486275">Time (ms) · {span_ms:.2f} ms shown</text>
  <text x="{left+plot_w+8}" y="{top+14}" font-size="11" fill="#486275">{y_hi:.3f} V</text>
  <text x="{left+plot_w+8}" y="{top+plot_h}" font-size="11" fill="#486275">{y_lo:.3f} V</text>
</svg>'''
