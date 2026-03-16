"""
Script Analyzer - Identifies 3-4 key moments in a video script
that are ideal for motion graphics.

Scoring criteria:
  - Statistics / numbers / data points  (highest impact)
  - Key quotes or bold statements
  - Lists or enumerations
  - Transitions / section headers
  - Emotional peaks (superlatives, emphasis words)
"""

import re
from dataclasses import dataclass, field


@dataclass
class ScriptSegment:
    text: str
    score: float
    category: str          # "stat", "quote", "list", "title", "emphasis"
    start_index: int
    keywords: list = field(default_factory=list)


# ── patterns ──────────────────────────────────────────────────────────────────

_STAT_PATTERNS = [
    r'\b\d+[\.,]?\d*\s*(%|percent|million|billion|trillion|thousand|x\b|times)',
    r'\b\d+\s*(out of|\/)\s*\d+',
    r'\b(increased|decreased|grew|dropped|rose|fell)\s+by\s+\d+',
    r'\$\s*\d+[\.,]?\d*\s*(million|billion|trillion|k|m|b)?',
    r'\b\d{2,}\s*(users|customers|people|downloads|subscribers|views|followers)',
]

_EMPHASIS_WORDS = [
    'incredible', 'amazing', 'revolutionary', 'breakthrough', 'game-changing',
    'critical', 'essential', 'powerful', 'massive', 'explosive', 'insane',
    'unbelievable', 'mind-blowing', 'shocking', 'secret', 'ultimate',
    'number one', '#1', 'most important', 'key takeaway', 'bottom line',
    'here\'s the thing', 'listen', 'pay attention', 'remember this',
    'never forget', 'the truth is', 'fact is', 'reality is',
]

_LIST_PATTERNS = [
    r'(?:first|second|third|fourth|1\.|2\.|3\.|4\.)',
    r'(?:step\s+\d|tip\s+\d|point\s+\d|reason\s+\d|rule\s+\d)',
    r'(?:number\s+(?:one|two|three|four|five|\d))',
]

_TITLE_PATTERNS = [
    r'^(?:chapter|part|section|act)\s+\d',
    r'^(?:intro(?:duction)?|conclusion|summary|outro|hook)',
    r'^(?:why|how|what|when|where|the\s+\w+\s+(?:of|to|for))',
]

_QUOTE_PATTERNS = [
    r'["\u201c].{15,}["\u201d]',
    r'(?:as\s+\w+\s+(?:said|once said|put it|wrote))',
    r'(?:quote|saying|proverb)',
]


def _split_into_segments(script: str, max_words: int = 40) -> list[str]:
    """Split script into sentence-level segments."""
    # Split on sentence boundaries
    raw = re.split(r'(?<=[.!?])\s+|\n{2,}', script.strip())
    segments = []
    buf = []
    for chunk in raw:
        chunk = chunk.strip()
        if not chunk:
            continue
        buf.append(chunk)
        word_count = sum(len(s.split()) for s in buf)
        if word_count >= max_words // 2:
            segments.append(' '.join(buf))
            buf = []
    if buf:
        segments.append(' '.join(buf))
    return [s for s in segments if len(s.split()) >= 3]


def _score_segment(text: str) -> tuple[float, str, list[str]]:
    """Return (score, category, keywords) for a segment."""
    lower = text.lower()
    score = 0.0
    category = "emphasis"
    keywords = []

    # Stats / numbers  (highest value for motion graphics)
    for pat in _STAT_PATTERNS:
        matches = re.findall(pat, lower)
        if matches:
            score += 3.0 * len(matches)
            category = "stat"
            keywords.extend(matches)

    # Standalone big numbers
    big_nums = re.findall(r'\b\d{3,}\b', text)
    if big_nums:
        score += 1.5 * len(big_nums)
        if category != "stat":
            category = "stat"
        keywords.extend(big_nums)

    # Quotes
    for pat in _QUOTE_PATTERNS:
        if re.search(pat, lower):
            score += 2.5
            if category not in ("stat",):
                category = "quote"

    # Lists / enumerations
    for pat in _LIST_PATTERNS:
        if re.search(pat, lower):
            score += 2.0
            if category not in ("stat", "quote"):
                category = "list"

    # Title / section header patterns
    for pat in _TITLE_PATTERNS:
        if re.search(pat, lower):
            score += 1.8
            if category not in ("stat", "quote", "list"):
                category = "title"

    # Emphasis words
    for word in _EMPHASIS_WORDS:
        if word in lower:
            score += 1.0
            keywords.append(word)
            if category not in ("stat", "quote", "list", "title"):
                category = "emphasis"

    # Bonus for shorter, punchier segments (better for graphics)
    wc = len(text.split())
    if wc <= 15:
        score *= 1.3
    elif wc <= 25:
        score *= 1.1

    return round(score, 2), category, keywords


def analyze_script(script: str, num_segments: int = 4) -> list[ScriptSegment]:
    """
    Analyze a video script and return the top `num_segments` parts
    most suitable for motion graphics conversion.
    """
    num_segments = max(3, min(num_segments, 4))
    raw_segments = _split_into_segments(script)

    scored: list[ScriptSegment] = []
    offset = 0
    for text in raw_segments:
        score, cat, kw = _score_segment(text)
        idx = script.find(text[:30], offset)
        if idx == -1:
            idx = offset
        scored.append(ScriptSegment(
            text=text,
            score=score,
            category=cat,
            start_index=idx,
            keywords=kw,
        ))
        offset = idx + len(text)

    # Sort by score descending, pick top N ensuring diversity of position
    scored.sort(key=lambda s: s.score, reverse=True)

    # Greedy pick: ensure selected segments are spread apart
    selected: list[ScriptSegment] = []
    used_indices: set[int] = set()
    min_gap = max(1, len(raw_segments) // (num_segments + 1))

    for seg in scored:
        seg_idx = raw_segments.index(seg.text) if seg.text in raw_segments else -1
        if seg_idx == -1:
            continue
        # Check distance from already-selected
        too_close = any(abs(seg_idx - ui) < min_gap for ui in used_indices)
        if too_close and len(selected) > 0:
            continue
        selected.append(seg)
        used_indices.add(seg_idx)
        if len(selected) >= num_segments:
            break

    # If we didn't get enough, relax constraint
    if len(selected) < num_segments:
        for seg in scored:
            if seg not in selected:
                selected.append(seg)
            if len(selected) >= num_segments:
                break

    # Re-order by appearance in script
    selected.sort(key=lambda s: s.start_index)

    # If all scores are 0 (generic text), still return segments evenly spread
    if all(s.score == 0 for s in selected) and len(raw_segments) >= num_segments:
        step = len(raw_segments) // num_segments
        selected = []
        for i in range(num_segments):
            idx = i * step
            text = raw_segments[idx]
            selected.append(ScriptSegment(
                text=text, score=0, category="emphasis",
                start_index=script.find(text[:30]),
                keywords=[],
            ))

    return selected
