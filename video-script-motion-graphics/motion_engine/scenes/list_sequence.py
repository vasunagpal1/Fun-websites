"""
List / Enumeration Sequence Scene
──────────────────────────────────
Items appear one by one with numbered indicators and progress bars.
Great for tips, steps, reasons, rules.
Used for: lists, enumerations, step-by-step content.
"""

import math
import os
import re

from ..renderer import create_frame, FPS, WIDTH, HEIGHT
from ..easing import (ease_out_back, ease_out_cubic, ease_out_expo,
                      ease_in_out_cubic, remap, clamp)
from ..colors import get_palette, hex_to_rgb, hex_to_rgba


def _extract_list_items(text: str) -> list[str]:
    """Try to split text into discrete list items."""
    # Try numbered patterns
    items = re.split(r'(?:\d+[.)]\s*|(?:first|second|third|fourth)[,:]?\s*)',
                     text, flags=re.IGNORECASE)
    items = [i.strip().rstrip('.,;') for i in items if i.strip() and len(i.strip()) > 5]

    if len(items) >= 2:
        return items[:5]

    # Try comma/semicolon split
    items = re.split(r'[;,]\s+', text)
    items = [i.strip().rstrip('.') for i in items if len(i.strip()) > 8]
    if len(items) >= 2:
        return items[:5]

    # Fallback: split into sentence chunks
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5][:5]


def render_list_sequence(text: str, category: str, output_dir: str,
                          duration: float = 5.0) -> list[str]:
    palette = get_palette(category)
    total_frames = int(duration * FPS)
    frames = []

    items = _extract_list_items(text)
    if not items:
        items = [text]

    num_items = len(items)
    item_height = min(90, 500 // max(num_items, 1))

    for fi in range(total_frames):
        t = fi / total_frames
        ts = fi / FPS

        fc = create_frame()

        # ── Background ────────────────────────────────────────────────
        fc.fill_gradient_vertical(palette["bg"], palette["surface"])
        fc.grid_dots(spacing=45, hex_color=palette["primary"], alpha=0.025)
        fc.particle_field(ts, count=18, hex_color=palette["accent"], alpha=0.07)

        # ── Header glow ───────────────────────────────────────────────
        fc.glow_circle(WIDTH/2, HEIGHT * 0.15, 200,
                       palette["primary"], alpha=0.06)

        # ── Progress bar at top ───────────────────────────────────────
        bar_width = WIDTH * 0.6
        bar_x = WIDTH/2 - bar_width/2
        bar_y = HEIGHT * 0.12

        # Background bar
        fc.rounded_rect(bar_x, bar_y, bar_width, 4, 2)
        fc.ctx.set_source_rgba(*hex_to_rgba(palette["muted"], 0.2))
        fc.ctx.fill()

        # Progress fill
        progress = ease_out_expo(clamp(remap(t, 0.05, 0.85, 0, 1)))
        if progress > 0:
            fc.rounded_rect(bar_x, bar_y, bar_width * progress, 4, 2)
            fc.ctx.set_source_rgb(*hex_to_rgb(palette["primary"]))
            fc.ctx.fill()

        # ── List items ────────────────────────────────────────────────
        total_list_h = num_items * item_height
        start_y = HEIGHT / 2 - total_list_h / 2 + 20

        for i, item in enumerate(items):
            # Stagger timing
            item_delay = 0.1 + i * (0.6 / max(num_items, 1))
            item_t = clamp(remap(t, item_delay, item_delay + 0.25, 0, 1))
            anim = ease_out_back(item_t)

            if item_t <= 0:
                continue

            y = start_y + i * item_height
            x_base = WIDTH * 0.18

            # Slide in from left
            x_offset = (1 - anim) * -200
            alpha = clamp(item_t * 2.5)

            # ── Number badge ──────────────────────────────────────────
            badge_x = x_base + x_offset
            badge_y = y
            badge_r = 22

            # Badge background
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["primary"],
                                                0.15 * alpha))
            fc.ctx.arc(badge_x, badge_y, badge_r, 0, 2 * math.pi)
            fc.ctx.fill()

            # Badge border
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["primary"], alpha))
            fc.ctx.arc(badge_x, badge_y, badge_r, 0, 2 * math.pi)
            fc.ctx.set_line_width(2)
            fc.ctx.stroke()

            # Number
            fc.text(str(i + 1), badge_x, badge_y, palette["primary"],
                    size=22, bold=True)

            # ── Item text ─────────────────────────────────────────────
            text_x = badge_x + 55 + x_offset * 0.3
            fc.text(item, text_x + (WIDTH * 0.7 - text_x) / 2, badge_y,
                    palette["text"],
                    size=28, bold=False,
                    max_width=WIDTH * 0.58, align="center")

            # ── Separator line ────────────────────────────────────────
            if i < num_items - 1:
                sep_t = ease_out_cubic(clamp(remap(t,
                    item_delay + 0.15, item_delay + 0.35, 0, 1)))
                if sep_t > 0:
                    sep_w = sep_t * (WIDTH * 0.55)
                    fc.line(x_base - 10, y + item_height/2 - 5,
                            x_base - 10 + sep_w, y + item_height/2 - 5,
                            palette["muted"], width=0.5)

        # ── Decorative corner accents ─────────────────────────────────
        corner_t = ease_out_cubic(clamp(remap(t, 0.3, 0.6, 0, 1)))
        if corner_t > 0:
            cl = 40 * corner_t
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["accent"], 0.3))
            fc.ctx.set_line_width(2)
            # Top-left
            fc.ctx.move_to(60, 60 + cl)
            fc.ctx.line_to(60, 60)
            fc.ctx.line_to(60 + cl, 60)
            fc.ctx.stroke()
            # Bottom-right
            fc.ctx.move_to(WIDTH - 60, HEIGHT - 60 - cl)
            fc.ctx.line_to(WIDTH - 60, HEIGHT - 60)
            fc.ctx.line_to(WIDTH - 60 - cl, HEIGHT - 60)
            fc.ctx.stroke()

        # ── Fade out ──────────────────────────────────────────────────
        fade_out = remap(t, 0.88, 1.0, 0, 1)
        if fade_out > 0:
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["bg"], fade_out))
            fc.ctx.paint()

        path = os.path.join(output_dir, f'frame_{fi:05d}.png')
        fc.surface.write_to_png(path)
        frames.append(path)

    return frames
