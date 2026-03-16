"""
Core frame renderer using PyCairo.
Produces 1920×1080 frames at 60 fps → fed to ffmpeg.
"""

import cairo
import math
import os
import tempfile
import subprocess
from pathlib import Path

from . import easing as ease
from .colors import hex_to_rgb, hex_to_rgba, lerp_color, get_palette

WIDTH, HEIGHT = 1920, 1080
FPS = 60


class FrameContext:
    """Wrapper around a Cairo context with convenience helpers."""

    def __init__(self, surface: cairo.ImageSurface, ctx: cairo.Context,
                 width: int = WIDTH, height: int = HEIGHT):
        self.surface = surface
        self.ctx = ctx
        self.w = width
        self.h = height
        self.cx = width / 2
        self.cy = height / 2

    # ── Background ────────────────────────────────────────────────────────

    def fill_solid(self, hex_color: str):
        r, g, b = hex_to_rgb(hex_color)
        self.ctx.set_source_rgb(r, g, b)
        self.ctx.paint()

    def fill_gradient_vertical(self, hex_top: str, hex_bot: str):
        pat = cairo.LinearGradient(0, 0, 0, self.h)
        pat.add_color_stop_rgb(0, *hex_to_rgb(hex_top))
        pat.add_color_stop_rgb(1, *hex_to_rgb(hex_bot))
        self.ctx.set_source(pat)
        self.ctx.paint()

    def fill_gradient_radial(self, hex_inner: str, hex_outer: str,
                              cx: float = None, cy: float = None, radius: float = None):
        cx = cx or self.cx
        cy = cy or self.cy
        radius = radius or self.w * 0.7
        pat = cairo.RadialGradient(cx, cy, 0, cx, cy, radius)
        pat.add_color_stop_rgb(0, *hex_to_rgb(hex_inner))
        pat.add_color_stop_rgb(1, *hex_to_rgb(hex_outer))
        self.ctx.set_source(pat)
        self.ctx.paint()

    # ── Shapes ────────────────────────────────────────────────────────────

    def rounded_rect(self, x: float, y: float, w: float, h: float,
                     radius: float = 20):
        """Draw a rounded rectangle path (not filled/stroked yet)."""
        ctx = self.ctx
        ctx.new_path()
        ctx.arc(x + w - radius, y + radius, radius, -math.pi/2, 0)
        ctx.arc(x + w - radius, y + h - radius, radius, 0, math.pi/2)
        ctx.arc(x + radius, y + h - radius, radius, math.pi/2, math.pi)
        ctx.arc(x + radius, y + radius, radius, math.pi, 3*math.pi/2)
        ctx.close_path()

    def circle(self, cx: float, cy: float, r: float):
        self.ctx.arc(cx, cy, r, 0, 2 * math.pi)

    def line(self, x1: float, y1: float, x2: float, y2: float,
             hex_color: str, width: float = 3):
        self.ctx.set_source_rgb(*hex_to_rgb(hex_color))
        self.ctx.set_line_width(width)
        self.ctx.move_to(x1, y1)
        self.ctx.line_to(x2, y2)
        self.ctx.stroke()

    # ── Text ──────────────────────────────────────────────────────────────

    def text(self, txt: str, x: float, y: float, hex_color: str,
             size: float = 48, bold: bool = False, align: str = "center",
             max_width: float = None, font: str = "Sans"):
        ctx = self.ctx
        weight = cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, weight)
        ctx.set_font_size(size)

        # Word-wrap if max_width given
        if max_width:
            lines = self._wrap_text(txt, size, max_width, font, bold)
        else:
            lines = [txt]

        line_height = size * 1.35
        total_h = line_height * len(lines)
        start_y = y - total_h / 2 + line_height / 2

        for i, line in enumerate(lines):
            ext = ctx.text_extents(line)
            ly = start_y + i * line_height

            if align == "center":
                lx = x - ext.width / 2
            elif align == "right":
                lx = x - ext.width
            else:
                lx = x

            ctx.move_to(lx, ly + ext.height / 2)
            ctx.set_source_rgb(*hex_to_rgb(hex_color))
            ctx.show_text(line)

    def _wrap_text(self, txt: str, size: float, max_width: float,
                   font: str, bold: bool) -> list[str]:
        ctx = self.ctx
        weight = cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, weight)
        ctx.set_font_size(size)

        words = txt.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            ext = ctx.text_extents(test)
            if ext.width > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    # ── Decorative elements ───────────────────────────────────────────────

    def glow_circle(self, cx: float, cy: float, r: float,
                    hex_color: str, alpha: float = 0.3):
        """Soft glowing circle for ambient effects."""
        pat = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
        rgba = hex_to_rgba(hex_color, alpha)
        pat.add_color_stop_rgba(0, *rgba)
        pat.add_color_stop_rgba(1, rgba[0], rgba[1], rgba[2], 0)
        self.ctx.set_source(pat)
        self.ctx.arc(cx, cy, r, 0, 2 * math.pi)
        self.ctx.fill()

    def accent_bar(self, x: float, y: float, width: float, height: float,
                   hex_color: str, radius: float = 4):
        """Small accent bar / underline."""
        self.rounded_rect(x - width/2, y, width, height, radius)
        self.ctx.set_source_rgb(*hex_to_rgb(hex_color))
        self.ctx.fill()

    def grid_dots(self, spacing: float = 60, hex_color: str = "#FFFFFF",
                  alpha: float = 0.04, radius: float = 1.5):
        """Subtle background dot grid for premium feel."""
        self.ctx.set_source_rgba(*hex_to_rgba(hex_color, alpha))
        for gx in range(0, self.w + 1, int(spacing)):
            for gy in range(0, self.h + 1, int(spacing)):
                self.ctx.arc(gx, gy, radius, 0, 2 * math.pi)
                self.ctx.fill()

    def particle_field(self, t: float, count: int = 30,
                       hex_color: str = "#FFFFFF", alpha: float = 0.15):
        """Floating particles that drift slowly."""
        import random
        rng = random.Random(42)  # deterministic
        for _ in range(count):
            bx = rng.random() * self.w
            by = rng.random() * self.h
            speed = rng.random() * 0.5 + 0.2
            size = rng.random() * 3 + 1
            # Gentle vertical drift
            px = bx + math.sin(t * speed * 2 + bx) * 20
            py = (by - t * speed * 40) % self.h
            a = alpha * (0.5 + 0.5 * math.sin(t * speed * 3 + by))
            self.ctx.set_source_rgba(*hex_to_rgba(hex_color, a))
            self.ctx.arc(px, py, size, 0, 2 * math.pi)
            self.ctx.fill()

    def noise_overlay(self, alpha: float = 0.015):
        """Very subtle noise texture for cinematic feel."""
        import random
        rng = random.Random(0)
        step = 8
        for nx in range(0, self.w, step):
            for ny in range(0, self.h, step):
                v = rng.random()
                self.ctx.set_source_rgba(v, v, v, alpha)
                self.ctx.rectangle(nx, ny, step, step)
                self.ctx.fill()


def create_frame() -> FrameContext:
    """Create a new blank frame."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    return FrameContext(surface, ctx)


def encode_frames_to_mp4(frame_dir: str, output_path: str,
                          fps: int = FPS) -> str:
    """Use ffmpeg to encode a directory of PNG frames to MP4."""
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', os.path.join(frame_dir, 'frame_%05d.png'),
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-vf', f'fps={fps}',
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
