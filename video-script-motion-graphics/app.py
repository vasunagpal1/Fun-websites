"""
Video Script → Motion Graphics Generator
Flask web app: paste script → analyze → generate premium motion graphics → download MP4.
"""

import os
import sys
import json
import uuid
import threading
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from script_analyzer import analyze_script
from motion_engine.pipeline import generate_motion_graphics

app = Flask(__name__)
app.config['OUTPUT_DIR'] = os.path.join(os.path.dirname(__file__), 'output')

# Track generation jobs
_jobs: dict[str, dict] = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Analyze script and return identified segments (quick, no video gen)."""
    data = request.get_json()
    script = data.get('script', '').strip()
    if not script:
        return jsonify({"error": "No script provided"}), 400

    num = data.get('num_segments', 4)
    num = max(3, min(4, int(num)))

    segments = analyze_script(script, num_segments=num)
    return jsonify({
        "segments": [
            {
                "index": i + 1,
                "text": s.text,
                "category": s.category,
                "score": s.score,
                "keywords": s.keywords[:5],
            }
            for i, s in enumerate(segments)
        ]
    })


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Start motion graphics generation (async)."""
    data = request.get_json()
    script = data.get('script', '').strip()
    if not script:
        return jsonify({"error": "No script provided"}), 400

    num = data.get('num_segments', 4)
    duration = data.get('duration', 5.0)
    duration = max(3.0, min(8.0, float(duration)))

    job_id = uuid.uuid4().hex[:12]
    job_dir = os.path.join(app.config['OUTPUT_DIR'], job_id)
    os.makedirs(job_dir, exist_ok=True)

    _jobs[job_id] = {"status": "running", "progress": "Analyzing script..."}

    def _run():
        try:
            _jobs[job_id]["progress"] = "Rendering motion graphics..."
            result = generate_motion_graphics(
                script, job_dir,
                duration_per_clip=duration,
                num_segments=int(num),
            )
            _jobs[job_id].update({
                "status": "done",
                "progress": "Complete!",
                "result": result,
            })
        except Exception as e:
            _jobs[job_id].update({
                "status": "error",
                "progress": str(e),
            })

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route('/api/status/<job_id>')
def api_status(job_id):
    """Poll job status."""
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route('/output/<job_id>/<filename>')
def serve_video(job_id, filename):
    """Serve generated video files."""
    directory = os.path.join(app.config['OUTPUT_DIR'], job_id)
    return send_from_directory(directory, filename, mimetype='video/mp4')


if __name__ == '__main__':
    os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
