"""Scene types for motion graphics generation."""

from .kinetic_text import render_kinetic_text
from .stat_reveal import render_stat_reveal
from .quote_card import render_quote_card
from .list_sequence import render_list_sequence

SCENE_RENDERERS = {
    "emphasis": render_kinetic_text,
    "stat":     render_stat_reveal,
    "quote":    render_quote_card,
    "list":     render_list_sequence,
    "title":    render_kinetic_text,
}
