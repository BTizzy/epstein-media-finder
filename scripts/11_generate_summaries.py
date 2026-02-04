"""
Script 11: Generate manual summaries and social-ready snippets for filtered candidates
"""
import sys
import os
import json
import csv
import logging
import textwrap
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FILTERED_JSON = 'data/results/filtered_candidates.json'
HASH_CSV = 'data/manifests/media_hashes.csv'
OUT_DIR = 'data/results/top_candidates'
KEYWORDS = ['video','photo','flight','payment','bank','phone','escort','model','minor','underage','nude','sex','passport','log']


def sentence_split(text: str):
    # very simple sentence split
    import re
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if s.strip()]


def choose_summary(full_text: str) -> str:
    sents = sentence_split(full_text)
    if not sents:
        return ''

    # prefer sentences containing keywords
    for s in sents:
        low = s.lower()
        if any(k in low for k in KEYWORDS):
            # return up to 2 sentences starting at this sentence
            idx = sents.index(s)
            return ' '.join(sents[idx:idx+2])

    # fallback: first two sentences
    return ' '.join(sents[:2])


def shorten(text: str, max_chars: int = 240) -> str:
    if len(text) <= max_chars:
        return text
    return textwrap.shorten(text, width=max_chars, placeholder='...')


def main():
    if not os.path.exists(FILTERED_JSON):
        logger.error(f"Filtered candidates not found: {FILTERED_JSON}. Run scripts/07_filter_candidates.py first.")
        return

    # load filtered
    with open(FILTERED_JSON) as f:
        candidates = json.load(f)

    # load full text mapping from hash CSV
    text_map = {}
    thumb_map = {}
    if os.path.exists(HASH_CSV):
        with open(HASH_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for r in reader:
                text_map[r.get('filename')] = r.get('full_text', '')
                thumb_map[r.get('filename')] = r.get('thumbnail_path', '')

    os.makedirs(OUT_DIR, exist_ok=True)
    results = []
    for c in candidates:
        fname = c.get('filename')
        full_text = text_map.get(fname, c.get('page_text_snippet','') or '')
        summary = choose_summary(full_text)
        short = shorten(summary, 240)

        doj_url = f"https://www.justice.gov/epstein/files/DataSet%209/{c.get('filename')}"
        suggested_post = f"Underreported DOJ file: {c.get('filename')} — {short} Source: {doj_url} #EpsteinData"

        out = {
            'file_id': c.get('file_id'),
            'filename': fname,
            'thumbnail': thumb_map.get(fname, ''),
            'virality_score': c.get('virality_score'),
            'interest_score': c.get('_interest_score'),
            'summary': summary,
            'suggested_post': suggested_post,
            'doj_url': doj_url
        }

        results.append(out)

        # Save per-item preview file
        base = Path(OUT_DIR) / (fname + '.md')
        with open(base, 'w') as md:
            md.write(f"# {fname}\n\n")
            md.write(f"**File ID:** {c.get('file_id')}\n\n")
            md.write(f"**Virality Score:** {c.get('virality_score')}\n\n")
            md.write(f"**Interest Score:** {c.get('_interest_score')}\n\n")
            md.write(f"**DOJ URL:** {doj_url}\n\n")
            md.write(f"## Summary\n{summary}\n\n")
            md.write(f"## Suggested post\n{suggested_post}\n")

    # Save aggregated JSON and CSV
    with open(os.path.join(OUT_DIR, 'top_candidates.json'), 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"✅ Generated {len(results)} summaries in {OUT_DIR}")


if __name__ == '__main__':
    main()
