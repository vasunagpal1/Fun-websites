"""
Statistics Reveal Scene
───────────────────────
Numbers count up with a circular progress indicator.
Supporting text fades in below. Data-driven, analytical feel.
Used for: statistics, percentages, big numbers, data points.
"""

import math
import os
import re

from ..renderer import create_frame, FPS, WIDTH, HEIGHT
from ..easing import ease_out_expo, ease_out_cubic, ease_in_out_cubic, remap, clamp
from ..colors import get_palette, hex_to_rgb, hex_to_rgba


def _extract_numbers(text: str) -> list[dict]:
    """Pull out numbers and their context from text."""
    results = []
    # Match numbers with optional prefix/suffix
    patterns = [
        r'(\$)\s*(\d[\d,]*\.?\d*)\s*(million|billion|trillion|k|m|b|%)?',
        r'(\d[\d,]*\.?\d*)\s*(%|percent|million|billion|trillion|x\b|times)',
        r'(\d[\d,]*\.?\d*)\s+(?:out of|\/)\s+(\d+)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            results.append({
                'match': m.group(0),
                'raw': m.group(0),
            })

    # Fallback: just find big numbers
    if not results:
        for m in re.finditer(r'\b(\d[\d,]*\.?\d*)\b', text):
            val = m.group(1).replace(',', '')
            try:
                if float(val) >= 2:
                    results.append({'match': m.group(0), 'raw': m.group(0)})
            except ValueError:
                pass

    return results[:3]  # max 3 numbers


def _get_numeric_value(raw: str) -> float:
    """Extract a numeric value for counting animation."""
    clean = re.sub(r'[^\d.]', '', raw.replace(',', ''))
    try:
        return float(clean)
    except ValueError:
        return 100


def render_stat_reveal(text: str, category: str, output_dir: str,
                        duration: float = 5.0) -> list[str]:
    palette = get_palette(category)
    total_frames = int(duration * FPS)
    frames = []

    numbers = _extract_numbers(text)
    main_stat = numbers[0]['raw'] if numbers else "100%"
    main_value = _get_numeric_value(main_stat)

    # Context text = original text minus the number
    context_text = text
    for n in numbers:
        context_text = context_text.replace(n['match'], '___')
    context_text = re.sub(r'\s+', ' ', context_text).strip()

    for fi in range(total_frames):
        t = fi / total_frames
        ts = fi / FPS

        fc = create_frame()

        # ── Background ────────────────────────────────────────────────
        fc.fill_gradient_radial(palette["surface"], palette["bg"],
                                 radius=WIDTH * 0.8)
        fc.grid_dots(spacing=40, hex_color=palette["primary"], alpha=0.025)
        fc.particle_field(ts, count=20, hex_color=palette["primary"], alpha=0.08)

        # ── Circular progress ring ────────────────────────────────────
        ring_t = ease_out_expo(clamp(remap(t, 0.1, 0.7, 0, 1)))
        cx, cy = WIDTH / 2, HEIGHT * 0.42
        ring_r = 160

        # Background ring
        fc.ctx.set_line_width(6)
        fc.ctx.set_source_rgba(*hex_to_rgba(palette["muted"], 0.2))
        fc.ctx.arc(cx, cy, ring_r, 0, 2 * math.pi)
        fc.ctx.stroke()

        # Animated ring
        if ring_t > 0:
            angle = ring_t * 2 * math.pi
            # Glow effect
            fc.ctx.set_line_width(12)
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["primary"], 0.2))
            fc.ctx.arc(cx, cy, ring_r, -math.pi/2, -math.pi/2 + angle)
            fc.ctx.stroke()
            # Main ring
            fc.ctx.set_line_width(6)
            fc.ctx.set_source_rgb(*hex_to_rgb(palette["primary"]))
            fc.ctx.arc(cx, cy, ring_r, -math.pi/2, -math.pi/2 + angle)
            fc.ctx.stroke()

            # Dot at end of ring
            dot_x = cx + ring_r * math.cos(-math.pi/2 + angle)
            dot_y = cy + ring_r * math.sin(-math.pi/2 + angle)
            fc.glow_circle(dot_x, dot_y, 20, palette["primary"], alpha=0.4)
            fc.ctx.set_source_rgb(*hex_to_rgb(palette["primary"]))
            fc.ctx.arc(dot_x, dot_y, 5, 0, 2 * math.pi)
            fc.ctx.fill()

        # ── Counting number ───────────────────────────────────────────
        count_t = ease_out_expo(clamp(remap(t, 0.15, 0.65, 0, 1)))
        current_val = main_value * count_t

        # Format the number to match original style
        if '%' in main_stat:
            display = f"{current_val:.0f}%"
        elif '$' in main_stat:
            if 'million' in main_stat.lower():
                display = f"${current_val:.1f}M"
            elif 'billion' in main_stat.lower():
                display = f"${current_val:.1f}B"
            else:
                display = f"${current_val:,.0f}"
        elif main_value == int(main_value):
            display = f"{int(current_val):,}"
        else:
            display = f"{current_val:.1f}"

        # Number text
        num_alpha = clamp(remap(t, 0.1, 0.25, 0, 1))
        if num_alpha > 0:
            scale = 0.8 + 0.2 * ease_out_cubic(clamp(remap(t, 0.1, 0.4, 0, 1)))
            fc.ctx.save()
            fc.ctx.translate(cx, cy)
            fc.ctx.scale(scale, scale)
            fc.ctx.translate(-cx, -cy)
            fc.text(display, cx, cy, palette["primary"],
                    size=80, bold=True)
            fc.ctx.restore()

        # ── Context text below ────────────────────────────────────────
        ctx_t = ease_out_cubic(clamp(remap(t, 0.45, 0.7, 0, 1)))
        if ctx_t > 0:
            ctx_y = HEIGHT * 0.72 + (1 - ctx_t) * 30
            # Replace ___ placeholder back with styled version
            display_text = context_text.replace('___', '•')
            fc.text(display_text, WIDTH/2, ctx_y, palette["text"],
                    size=32, bold=False, max_width=WIDTH * 0.7)

        # ── Accent lines ──────────────────────────────────────────────
        line_t = ease_out_cubic(clamp(remap(t, 0.3, 0.55, 0, 1)))
        if line_t > 0:
            lw = line_t * 120
            fc.accent_bar(WIDTH/2, HEIGHT * 0.62, lw, 2, palette["accent"])

        # ── Fade out ──────────────────────────────────────────────────
        fade_out = remap(t, 0.88, 1.0, 0, 1)
        if fade_out > 0:
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["bg"], fade_out))
            fc.ctx.paint()

        path = os.path.join(output_dir, f'frame_{fi:05d}.png')
        fc.surface.write_to_png(path)
        frames.append(path)

    return frames
