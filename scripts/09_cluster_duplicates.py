"""
Script 9: Cluster duplicate or very similar images using phash
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import json
from PIL import Image
import imagehash
from collections import defaultdict
from tqdm import tqdm

HASH_CSV = 'data/manifests/media_hashes.csv'
OUT_JSON = 'data/results/duplicate_clusters.json'


def hamming(a: str, b: str) -> int:
    if not a or not b:
        return 999
    ha = int(str(a), 16)
    hb = int(str(b), 16)
    x = ha ^ hb
    return x.bit_count()


def main():
    if not os.path.exists(HASH_CSV):
        print('Run scripts/03_hash_media.py first')
        return

    with open(HASH_CSV, newline='') as csvfile:
        rows = list(csv.DictReader(csvfile))

    phash_map = defaultdict(list)
    for r in rows:
        phash_map[r.get('phash', '')].append(r)

    # naive pairwise clustering by hamming distance
    clusters = []
    used = set()
    threshold = 10

    for i, r in enumerate(rows):
        if r['local_path'] in used:
            continue
        cluster = [r]
        used.add(r['local_path'])
        for j in range(i+1, len(rows)):
            s = rows[j]
            if s['local_path'] in used:
                continue
            d = hamming(r.get('phash',''), s.get('phash',''))
            if d <= threshold:
                cluster.append(s)
                used.add(s['local_path'])

        if len(cluster) > 1:
            clusters.append([c['local_path'] for c in cluster])

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(clusters, f, indent=2)

    print(f'Clusters found: {len(clusters)}')


if __name__ == '__main__':
    main()
