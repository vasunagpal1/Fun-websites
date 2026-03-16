"""
Quote / Key Point Card Scene
─────────────────────────────
Elegant card slides in, quote marks animate, text reveals word by word.
Feels like a premium keynote presentation.
Used for: quotes, key statements, bold claims.
"""

import math
import os

from ..renderer import create_frame, FPS, WIDTH, HEIGHT
from ..easing import ease_out_cubic, ease_out_back, ease_in_out_cubic, remap, clamp
from ..colors import get_palette, hex_to_rgb, hex_to_rgba


def render_quote_card(text: str, category: str, output_dir: str,
                       duration: float = 5.0) -> list[str]:
    palette = get_palette(category)
    total_frames = int(duration * FPS)
    frames = []

    for fi in range(total_frames):
        t = fi / total_frames
        ts = fi / FPS

        fc = create_frame()

        # ── Background ────────────────────────────────────────────────
        fc.fill_solid(palette["bg"])
        fc.grid_dots(spacing=55, hex_color=palette["text"], alpha=0.02)
        fc.particle_field(ts, count=15, hex_color=palette["primary"], alpha=0.06)

        # ── Ambient glow ──────────────────────────────────────────────
        fc.glow_circle(WIDTH * 0.2, HEIGHT * 0.5,
                       250 + math.sin(ts) * 40,
                       palette["gradient"][0], alpha=0.05)
        fc.glow_circle(WIDTH * 0.8, HEIGHT * 0.5,
                       200 + math.cos(ts * 0.7) * 30,
                       palette["gradient"][-1], alpha=0.04)

        # ── Card background ───────────────────────────────────────────
        card_t = ease_out_cubic(clamp(remap(t, 0.05, 0.35, 0, 1)))
        card_w, card_h = 1200, 450
        card_x = WIDTH/2 - card_w/2
        card_y = HEIGHT/2 - card_h/2 + (1 - card_t) * 80

        if card_t > 0:
            alpha = card_t * 0.9

            # Card shadow
            fc.ctx.set_source_rgba(0, 0, 0, 0.3 * card_t)
            fc.rounded_rect(card_x + 8, card_y + 8, card_w, card_h, 24)
            fc.ctx.fill()

            # Card body
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["surface"], alpha))
            fc.rounded_rect(card_x, card_y, card_w, card_h, 24)
            fc.ctx.fill()

            # Card border (subtle)
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["primary"], 0.15 * card_t))
            fc.rounded_rect(card_x, card_y, card_w, card_h, 24)
            fc.ctx.set_line_width(1.5)
            fc.ctx.stroke()

            # Left accent bar on card
            bar_h = ease_out_cubic(clamp(remap(t, 0.2, 0.5, 0, 1))) * (card_h - 60)
            if bar_h > 0:
                fc.rounded_rect(card_x + 30, card_y + 30, 4, bar_h, 2)
                fc.ctx.set_source_rgb(*hex_to_rgb(palette["primary"]))
                fc.ctx.fill()

        # ── Quote marks ───────────────────────────────────────────────
        quote_t = ease_out_back(clamp(remap(t, 0.15, 0.4, 0, 1)))
        if quote_t > 0:
            qsize = 120 * quote_t
            fc.ctx.save()
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["primary"], 0.2 * quote_t))
            fc.ctx.select_font_face("Sans", 0, 1)
            fc.ctx.set_font_size(qsize)

            # Opening quote
            fc.ctx.move_to(card_x + 50, card_y + 40 + qsize * 0.7)
            fc.ctx.show_text("\u201C")

            # Closing quote
            ext = fc.ctx.text_extents("\u201D")
            fc.ctx.move_to(card_x + card_w - 50 - ext.width,
                           card_y + card_h - 30)
            fc.ctx.show_text("\u201D")
            fc.ctx.restore()

        # ── Text reveal (word by word) ────────────────────────────────
        words = text.split()
        text_start = 0.25
        text_end = 0.75
        words_per_sec = len(words) / ((text_end - text_start) * duration)

        revealed_count = int(
            clamp(remap(t, text_start, text_end, 0, 1)) * len(words)
        )
        revealed_text = ' '.join(words[:revealed_count])

        if revealed_text:
            fc.text(revealed_text, WIDTH/2, HEIGHT/2, palette["text"],
                    size=36, bold=False, max_width=card_w - 120)

        # ── Source / attribution line ─────────────────────────────────
        attr_t = ease_out_cubic(clamp(remap(t, 0.65, 0.8, 0, 1)))
        if attr_t > 0:
            dash_w = attr_t * 40
            fc.accent_bar(WIDTH/2, card_y + card_h + 30, dash_w, 2,
                          palette["muted"])

        # ── Fade out ──────────────────────────────────────────────────
        fade_out = remap(t, 0.88, 1.0, 0, 1)
        if fade_out > 0:
            fc.ctx.set_source_rgba(*hex_to_rgba(palette["bg"], fade_out))
            fc.ctx.paint()

        path = os.path.join(output_dir, f'frame_{fi:05d}.png')
        fc.surface.write_to_png(path)
        frames.append(path)

    return frames
