"""
Script 8: Run OCR on rendered pages and update media_hashes.csv
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import logging
from tqdm import tqdm
from utils.state_manager import get, set_

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None

HASH_CSV = 'data/manifests/media_hashes.csv'


def ocr_image(image_path: str) -> str:
    if pytesseract is None:
        return ''
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception:
        return ''


def main():
    if not os.path.exists(HASH_CSV):
        logger.error('Hash CSV not found. Run scripts/03_hash_media.py first.')
        return

    # load rows
    with open(HASH_CSV, newline='') as csvfile:
        rows = list(csv.DictReader(csvfile))

    start = get('ocr_index', 0)
    logger.info(f'Starting OCR at index {start}')

    for idx in tqdm(range(start, len(rows))):
        r = rows[idx]
        img = r.get('local_path')
        if not img or not os.path.exists(img):
            r['full_text'] = r.get('page_text_snippet','')
            continue

        text = ocr_image(img)
        if not text:
            text = r.get('page_text_snippet','')

        r['full_text'] = text
        # save progress state
        set_('ocr_index', idx+1)

    # write back CSV (preserve existing fields + full_text)
    fieldnames = list(rows[0].keys()) if rows else []
    if 'full_text' not in fieldnames:
        fieldnames.append('full_text')

    with open(HASH_CSV, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    logger.info('✅ OCR complete and media_hashes.csv updated')


if __name__ == '__main__':
    main()
