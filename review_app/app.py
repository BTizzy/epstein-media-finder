from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import json
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
TOP_JSON = BASE_DIR / 'data' / 'results' / 'top_candidates' / 'top_candidates.json'
REVIEWED = BASE_DIR / 'data' / 'results' / 'reviewed.json'
EXPORT_JSON = BASE_DIR / 'data' / 'results' / 'exported_reviews.json'
EXPORT_CSV = BASE_DIR / 'data' / 'results' / 'exported_reviews.csv'

app = Flask(__name__, static_folder=str(BASE_DIR / 'data' / 'downloaded_media'))


def load_candidates():
    if TOP_JSON.exists():
        with open(TOP_JSON) as f:
            return json.load(f)
    return []


def normalize_thumbnails(candidates):
    # convert absolute thumbnail paths to static-relative paths
    dd = str(BASE_DIR / 'data' / 'downloaded_media')
    for c in candidates:
        thumb = c.get('thumbnail') or ''
        if thumb and thumb.startswith(dd):
            rel = os.path.relpath(thumb, dd)
            c['thumbnail'] = rel.replace('\\', '/')
        elif thumb and thumb.startswith('data/downloaded_media'):
            # already relative-ish
            _, rel = thumb.split('data/downloaded_media', 1)
            c['thumbnail'] = rel.lstrip('/\\')
    return candidates


def load_reviewed():
    if REVIEWED.exists():
        with open(REVIEWED) as f:
            return json.load(f)
    return {}


def save_reviewed(data):
    os.makedirs(REVIEWED.parent, exist_ok=True)
    with open(REVIEWED, 'w') as f:
        json.dump(data, f, indent=2)


@app.route('/')
def index():
    candidates = normalize_thumbnails(load_candidates())
    reviewed = load_reviewed()

    # Filters
    show_faces = request.args.get('faces') == '1'
    show_nsfw = request.args.get('nsfw') == '1'

    # Sorting
    sort = request.args.get('sort', 'interest')
    if sort == 'interest':
        candidates = sorted(candidates, key=lambda x: float(x.get('interest_score') or x.get('_interest_score') or 0), reverse=True)
    elif sort == 'virality':
        candidates = sorted(candidates, key=lambda x: float(x.get('virality_score') or 0))
    elif sort == 'filename':
        candidates = sorted(candidates, key=lambda x: x.get('filename') or '')

    # Apply filters
    if show_faces:
        candidates = [c for c in candidates if int(c.get('face_count') or 0) > 0]
    if show_nsfw:
        candidates = [c for c in candidates if str(c.get('likely_nsfw')).lower() in ('true', '1')]

    # Pagination
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 12))
    except Exception:
        page = 1
        page_size = 12

    total = len(candidates)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = candidates[start:end]

    return render_template('index.html', candidates=page_items, reviewed=reviewed, page=page, total=total, page_size=page_size, sort=sort)


@app.route('/candidate/<path:filename>')
def candidate(filename):
    candidates = normalize_thumbnails(load_candidates())
    item = next((c for c in candidates if c['filename'] == filename), None)
    if not item:
        return 'Not found', 404
    reviewed = load_reviewed()
    return render_template('candidate.html', item=item, reviewed=reviewed.get(item['file_id']))


@app.route('/mark', methods=['POST'])
def mark():
    file_id = request.form.get('file_id')
    action = request.form.get('action')  # reviewed or unreview
    reviewed = load_reviewed()
    if action == 'reviewed':
        reviewed[file_id] = {'status': 'reviewed', 'note': request.form.get('note','')}
    else:
        reviewed.pop(file_id, None)
    save_reviewed(reviewed)
    return redirect(request.referrer or url_for('index'))


@app.route('/export')
def export():
    reviewed = load_reviewed()
    candidates = load_candidates()
    rows = []
    for c in candidates:
        fid = c['file_id']
        if fid in reviewed:
            r = reviewed[fid]
            rows.append({**c, **r})

    # save json and csv
    with open(EXPORT_JSON, 'w') as f:
        json.dump(rows, f, indent=2)

    if rows:
        keys = list(rows[0].keys())
        with open(EXPORT_CSV, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    return send_file(EXPORT_JSON, as_attachment=True)


@app.route('/export_all')
def export_all():
    # Export all candidates JSON
    candidates = load_candidates()
    tmp = EXPORT_JSON.parent / 'all_candidates.json'
    with open(tmp, 'w') as f:
        json.dump(candidates, f, indent=2)
    return send_file(tmp, as_attachment=True)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
