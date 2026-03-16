"""
Kinetic Typography Scene
─────────────────────────
Words fly in with staggered timing, scale up, and settle into position.
Background has floating particles and subtle grid.
Used for: emphasis statements, titles, bold claims.
"""

import math
import os
import tempfile

from ..renderer import create_frame, FPS, WIDTH, HEIGHT
from ..easing import ease_out_back, ease_out_cubic, ease_in_out_cubic, remap, clamp
from ..colors import get_palette, hex_to_rgb, hex_to_rgba


def render_kinetic_text(text: str, category: str, output_dir: str,
                         duration: float = 5.0) -> list[str]:
    """
    Render kinetic typography frames.
    Returns list of frame file paths.
    """
    palette = get_palette(category)
    total_frames = int(duration * FPS)
    frames = []

    # Split text into words for staggered animation
    words = text.split()
    # Group into lines of ~4-6 words
    lines = []
    line = []
    for w in words:
        line.append(w)
        if len(line) >= 5:
            lines.append(' '.join(line))
            line = []
    if line:
        lines.append(' '.join(line))

    # If very short, treat as single block
    if len(lines) <= 1:
        lines = [text]

    for fi in range(total_frames):
        t = fi / total_frames          # 0 → 1 over duration
        ts = fi / FPS                  # time in seconds

        fc = create_frame()

        # ── Background ────────────────────────────────────────────────
        fc.fill_gradient_radial(palette["surface"], palette["bg"])
        fc.grid_dots(spacing=50, hex_color=palette["primary"], alpha=0.03)
        fc.particle_field(ts, count=25, hex_color=palette["primary"], alpha=0.1)

        # ── Animated accent orbs ──────────────────────────────────────
        orb_t = ease_in_out_cubic(clamp(t * 1.5))
        fc.glow_circle(
            WIDTH * 0.15 + orb_t * 80, HEIGHT * 0.3,
            150 + math.sin(ts * 2) * 30,
            palette["gradient"][0], alpha=0.08
        )
        fc.glow_circle(
            WIDTH * 0.85 - orb_t * 60, HEIGHT * 0.7,
            120 + math.cos(ts * 1.5) * 25,
            palette["gradient"][-1], alpha=0.06
        )

        # ── Top accent line ───────────────────────────────────────────
        line_w = remap(t, 0.05, 0.3, 0, 300)
        if line_w > 0:
            fc.accent_bar(WIDTH/2, HEIGHT * 0.28, line_w, 3,
                          palette["primary"])

        # ── Staggered word/line reveal ────────────────────────────────
        line_height = 75 if len(lines) <= 3 else 65
        total_text_h = line_height * len(lines)
        base_y = HEIGHT / 2 - total_text_h / 2 + line_height / 2

        for i, ln in enumerate(lines):
            # Stagger: each line starts 0.15s after previous
            delay = 0.15 + i * 0.15
            line_t = clamp((ts - delay) / 0.6)  # 0.6s to animate in
            anim = ease_out_back(line_t)

            if line_t <= 0:
                continue

            # Scale + vertical offset
            scale = 0.3 + 0.7 * anim
            y_offset = (1 - anim) * 60
            alpha_val = clamp(line_t * 2)

            y = base_y + i * line_height + y_offset

            ctx = fc.ctx
            ctx.save()
            ctx.translate(WIDTH / 2, y)
            ctx.scale(scale, scale)
            ctx.translate(-WIDTH / 2, -y)

            # Determine font size – main emphasis lines bigger
            is_main = (i == len(lines) // 2) or len(lines) == 1
            size = 62 if is_main else 48
            color = palette["text"] if not is_main else palette["primary"]

            # Text shadow
            fc.text(ln, WIDTH/2 + 2, y + 2, palette["bg"],
                    size=size, bold=is_main, max_width=WIDTH * 0.75)
            # Main text
            fc.text(ln, WIDTH/2, y, color,
                    size=size, bold=is_main, max_width=WIDTH * 0.75)

            ctx.restore()

        # ── Bottom accent bar ─────────────────────────────────────────
        bot_t = remap(t, 0.6, 0.8, 0, 1)
        if bot_t > 0:
            bar_w = ease_out_cubic(bot_t) * 200
            fc.accent_bar(WIDTH/2, HEIGHT * 0.72, bar_w, 3,
                          palette["accent"])

        # ── Fade out in last 0.5s ─────────────────────────────────────
        fade_out = remap(t, 0.85, 1.0, 0, 1)
        if fade_out > 0:
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["bg"], fade_out))
            fc.ctx.paint()

        # ── Save frame ────────────────────────────────────────────────
        path = os.path.join(output_dir, f'frame_{fi:05d}.png')
        fc.surface.write_to_png(path)
        frames.append(path)

    return frames
