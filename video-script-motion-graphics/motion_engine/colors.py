"""
Premium color palettes and color utilities for motion graphics.
"""


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert '#RRGGBB' to (r, g, b) in 0-1 range."""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    r, g, b = hex_to_rgb(hex_color)
    return (r, g, b, alpha)


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Interpolate between two RGB/RGBA colors."""
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


# ── Premium Palettes ─────────────────────────────────────────────────────────

PALETTES = {
    "midnight": {
        "bg":       "#0A0E17",
        "surface":  "#141B2D",
        "primary":  "#4F8EF7",
        "accent":   "#FF6B6B",
        "text":     "#E8ECF1",
        "muted":    "#6B7B8D",
        "gradient": ["#4F8EF7", "#A855F7"],
    },
    "ember": {
        "bg":       "#0D0907",
        "surface":  "#1A1210",
        "primary":  "#FF6B35",
        "accent":   "#FFD700",
        "text":     "#F5E6D3",
        "muted":    "#8B7355",
        "gradient": ["#FF6B35", "#FF2E63"],
    },
    "arctic": {
        "bg":       "#0B1628",
        "surface":  "#132240",
        "primary":  "#00D4FF",
        "accent":   "#7B68EE",
        "text":     "#E0F0FF",
        "muted":    "#5A7A9A",
        "gradient": ["#00D4FF", "#7B68EE"],
    },
    "forest": {
        "bg":       "#0A1209",
        "surface":  "#152014",
        "primary":  "#4ADE80",
        "accent":   "#FBBF24",
        "text":     "#E5F5E0",
        "muted":    "#6B8F71",
        "gradient": ["#4ADE80", "#06B6D4"],
    },
}

# Scene-type → palette mapping
SCENE_PALETTE_MAP = {
    "stat":      "arctic",
    "quote":     "midnight",
    "list":      "ember",
    "title":     "forest",
    "emphasis":  "midnight",
}


def get_palette(category: str) -> dict:
    name = SCENE_PALETTE_MAP.get(category, "midnight")
    return PALETTES[name]
