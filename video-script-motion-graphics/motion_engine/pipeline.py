"""
Pipeline – orchestrates script analysis → frame rendering → MP4 encoding.
Each identified segment gets its own motion graphic video.
Also produces a combined final cut.
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path

from script_analyzer import analyze_script, ScriptSegment
from motion_engine.renderer import encode_frames_to_mp4, FPS
from motion_engine.scenes import SCENE_RENDERERS


def generate_motion_graphics(script: str, output_dir: str,
                              duration_per_clip: float = 5.0,
                              num_segments: int = 4) -> dict:
    """
    Full pipeline: script → analysis → render → encode.

    Returns:
        {
            "segments": [...],
            "clips": ["clip_1.mp4", ...],
            "combined": "combined.mp4",
        }
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── 1. Analyze script ─────────────────────────────────────────────
    segments = analyze_script(script, num_segments=num_segments)

    results = {
        "segments": [],
        "clips": [],
        "combined": None,
    }

    clip_paths = []

    for i, seg in enumerate(segments):
        seg_info = {
            "index": i + 1,
            "text": seg.text,
            "category": seg.category,
            "score": seg.score,
        }
        results["segments"].append(seg_info)

        # ── 2. Render frames ─────────────────────────────────────────
        renderer = SCENE_RENDERERS.get(seg.category,
                                        SCENE_RENDERERS["emphasis"])
        frame_dir = tempfile.mkdtemp(prefix=f"mg_frames_{i}_")

        try:
            renderer(
                text=seg.text,
                category=seg.category,
                output_dir=frame_dir,
                duration=duration_per_clip,
            )

            # ── 3. Encode to MP4 ─────────────────────────────────────
            clip_name = f"clip_{i+1}_{seg.category}.mp4"
            clip_path = os.path.join(output_dir, clip_name)
            encode_frames_to_mp4(frame_dir, clip_path)

            results["clips"].append(clip_name)
            clip_paths.append(clip_path)

        finally:
            # Clean up frame PNGs
            shutil.rmtree(frame_dir, ignore_errors=True)

    # ── 4. Combine all clips into one video ───────────────────────────
    if len(clip_paths) > 1:
        combined_path = os.path.join(output_dir, "combined.mp4")
        _concat_videos(clip_paths, combined_path)
        results["combined"] = "combined.mp4"
    elif clip_paths:
        # Only one clip, just copy it
        combined_path = os.path.join(output_dir, "combined.mp4")
        shutil.copy2(clip_paths[0], combined_path)
        results["combined"] = "combined.mp4"

    return results


def _concat_videos(clip_paths: list[str], output_path: str):
    """Concatenate multiple MP4 clips using ffmpeg concat demuxer."""
    list_file = output_path + ".txt"
    try:
        with open(list_file, 'w') as f:
            for p in clip_paths:
                abs_p = os.path.abspath(p)
                f.write(f"file '{abs_p}'\n")

        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)
