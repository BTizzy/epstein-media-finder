"""
Script 10: Resume and finish social presence checks
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
from utils.state_manager import get, set_
from utils.social_checker import (
    google_search_count, reddit_count_mentions, nitter_search, calculate_free_virality_score, is_underreported, rate_limit_delay
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RESULTS_JSON = 'data/results/underreported_media.json'
CONFIG_FILE = 'config/config.yaml'

def main():
    if not os.path.exists(RESULTS_JSON):
        logger.error('No partial results found. Run scripts/04_check_social_presence.py first to start checks.')
        return

    with open(RESULTS_JSON) as f:
        items = json.load(f)

    start = get('social_index', 0)
    logger.info(f'Resuming social checks at index {start}')

    for idx in range(start, len(items)):
        it = items[idx]
        filename = it.get('filename')
        logger.info(f'Checking (resume): {filename} ({idx+1}/{len(items)})')

        try:
            g = google_search_count(filename)
            r = reddit_count_mentions(filename)
            n = nitter_search(filename)
            score = calculate_free_virality_score(g, r, n)
            it.update({'google_mentions': g, 'reddit_mentions': r, 'nitter_mentions': n, 'virality_score': score, 'is_underreported': is_underreported(score)})

            # persist after each
            with open(RESULTS_JSON, 'w') as f:
                json.dump(items, f, indent=2)

            set_('social_index', idx+1)
            rate_limit_delay(0.5, 1.0)
        except Exception as e:
            logger.error(f'Error checking {filename}: {e}')
            rate_limit_delay(1,2)

    logger.info('✅ Social checks finished')

if __name__ == '__main__':
    main()
