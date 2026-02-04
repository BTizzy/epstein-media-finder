"""
Script 7: Filter Underreported but Interesting Candidates
Uses interest scoring to find items worth manual review
"""
import sys
import os
import json
import csv
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.social_checker import filter_underreported_candidates, compute_interest_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RESULTS_JSON = 'data/results/underreported_media.json'
HASH_CSV = 'data/manifests/media_hashes.csv'
OUTPUT_JSON = 'data/results/filtered_candidates.json'
OUTPUT_CSV = 'data/results/filtered_candidates.csv'


def main(prefer_faces: bool = False):
    if not os.path.exists(RESULTS_JSON):
        logger.error(f"Results not found: {RESULTS_JSON}. Run scripts/04_check_social_presence.py first.")
        return

    with open(RESULTS_JSON) as f:
        results = json.load(f)

    # Enrich with keywords from hash db
    keywords_map = {}
    if os.path.exists(HASH_CSV):
        with open(HASH_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for r in reader:
                # key by filename
                keywords_map[r.get('filename')] = r.get('keywords_found', '')

    for r in results:
        fname = r.get('filename')
        if fname in keywords_map:
            r['keywords_found'] = keywords_map[fname]
        else:
            r['keywords_found'] = ''

    candidates = filter_underreported_candidates(results, virality_threshold=5.0, min_interest=3.0)

    # prefer items with faces if requested
    if prefer_faces:
        candidates = sorted(candidates, key=lambda x: (int(x.get('face_count') or 0) > 0, float(x.get('_interest_score') or x.get('interest_score') or 0)), reverse=True)

    # Save
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(candidates, f, indent=2)

    if candidates:
        fieldnames = list(candidates[0].keys())
        with open(OUTPUT_CSV, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for c in candidates:
                writer.writerow(c)

    logger.info(f"✅ Filtered candidates saved: {OUTPUT_JSON} ({len(candidates)} items)")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefer-faces', action='store_true', help='Prefer candidates with detected faces')
    args = parser.parse_args()
    main(prefer_faces=args.prefer_faces)
