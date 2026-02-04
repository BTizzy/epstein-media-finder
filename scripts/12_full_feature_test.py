"""
Script 12: Full feature test (limited)
Runs hashing/face/skin/nsfw heuristics and (optionally) reverse image checks on a small sample.
"""
import os
import sys
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.media_processor import detect_faces, compute_skin_fraction, is_likely_nsfw, is_valid_image
from utils.social_checker import upload_image_anonymous, reverse_image_search_counts, compute_interest_score
import csv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HASH_CSV = 'data/manifests/media_hashes.csv'
OUT = 'data/results/test_run_results.json'

def main(limit=5, do_reverse=False):
    if not os.path.exists(HASH_CSV):
        logger.error('Hash CSV not found; run scripts/03_hash_media.py first')
        return

    rows = []
    with open(HASH_CSV, newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    sample = rows[:limit]
    results = []
    for r in sample:
        img = r.get('local_path')
        if not img or not os.path.exists(img):
            continue
        faces = detect_faces(img)
        sf = compute_skin_fraction(img)
        nsfw = is_likely_nsfw(img, ocr_text=r.get('page_text_snippet',''))

        rev = {}
        if do_reverse:
            pub = upload_image_anonymous(r.get('thumbnail_path') or img)
            if pub:
                rev = reverse_image_search_counts(pub)

        item = {
            'filename': r.get('filename'),
            'local_path': img,
            'face_count': faces.get('face_count', 0),
            'skin_fraction': sf,
            'likely_nsfw': nsfw.get('likely_nsfw', False),
            'nsfw_reasons': nsfw.get('reasons', []),
            'reverse_search_matches': rev
        }
        # compute interest (best-effort)
        item['interest_score'] = compute_interest_score({**item, **r}, rows)
        results.append(item)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"✅ Test run complete. Results in {OUT}")

if __name__ == '__main__':
    main(limit=5, do_reverse=False)
