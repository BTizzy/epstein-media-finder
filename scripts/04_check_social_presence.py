"""
Script 4: Check Social Media Presence (FREE VERSION)
Uses web scraping to check if files are already viral - NO API COSTS
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from tqdm import tqdm
import logging
import yaml
import json
from datetime import datetime
from utils.social_checker import (
    google_search_count,
    reddit_count_mentions,
    nitter_search,
    calculate_free_virality_score,
    is_underreported,
    rate_limit_delay
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check social media presence for each file"""
    
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Load hash database
    hash_path = 'data/manifests/media_hashes.csv'
    with open(hash_path, newline='') as csvfile:
        df = list(csv.DictReader(csvfile))
    logger.info(f"Checking social presence for {len(df)} files")
    
    # Load partial results if present to avoid re-checking same files
    json_path = config['output']['results_file']
    results = []
    processed_ids = set()
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as jf:
                results = json.load(jf)
                processed_ids = set(r['file_id'] for r in results)
        except Exception:
            results = []
            processed_ids = set()
    
    for idx, row in enumerate(tqdm(df, total=len(df), desc="Checking social media")):
        file_id = row.get('file_id')
        filename = row.get('filename')
        
        logger.info(f"Checking: {filename}")
        if file_id in processed_ids:
            logger.info(f"⏭️  Already checked: {file_id}")
            continue
        
        # Search queries (limit to filename for speed)
        queries = [
            filename,  # Exact filename
        ]
        
        # Aggregate counts
        total_google = 0
        total_reddit = 0
        total_nitter = 0
        
        for query in queries:
            # Google search
            try:
                google_count = google_search_count(query)
                total_google += google_count
                logger.info(f"  Google '{query}': {google_count} results")
                rate_limit_delay(0.5, 1.0)
            except Exception as e:
                logger.error(f"Google search failed: {e}")
            
            # Reddit search (limit to first 3 subreddits for speed)
            try:
                subs = config['social_platforms']['reddit_subreddits'][:3]
                reddit_count = reddit_count_mentions(query, subs)
                total_reddit += reddit_count
                logger.info(f"  Reddit '{query}': {reddit_count} posts")
                rate_limit_delay(0.5, 1.0)
            except Exception as e:
                logger.error(f"Reddit search failed: {e}")
            
            # Nitter search (Twitter mirror)
            try:
                nitter_count = nitter_search(query, config['social_platforms']['nitter_instances'])
                total_nitter += nitter_count
                logger.info(f"  Nitter '{query}': {nitter_count} tweets")
                rate_limit_delay(0.5, 1.0)
            except Exception as e:
                logger.error(f"Nitter search failed: {e}")
        
        # Calculate virality score
        score = calculate_free_virality_score(total_google, total_reddit, total_nitter)
        underreported = is_underreported(score)
        
        logger.info(f"  📊 Virality Score: {score} - {'🔥 UNDERREPORTED' if underreported else '✅ Known'}")
        
        item = {
            'file_id': file_id,
            'filename': filename,
            'local_path': row.get('local_path'),
            'thumbnail_path': row.get('thumbnail_path'),
            'google_mentions': total_google,
            'reddit_mentions': total_reddit,
            'nitter_mentions': total_nitter,
            'virality_score': score,
            'is_underreported': underreported,
            'check_timestamp': datetime.now().isoformat()
        }

        results.append(item)

        # Save partial results after each file to avoid losing progress
        json_path = config['output']['results_file']
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        try:
            with open(json_path, 'w') as jf:
                import json as _json
                _json.dump(results, jf, indent=2)
        except Exception as e:
            logger.error(f"Failed to save partial results: {e}")
        
    # Extra delay between files
    rate_limit_delay(0.5, 1.0)
    
    # Save results
    results_df = results
    
    # JSON output (full data)
    json_path = config['output']['results_file']
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    results_df.to_json(json_path, orient='records', indent=2)
    
    # CSV output (summary)
    csv_path = 'data/results/underreported_media.csv'
    if results:
        fieldnames = list(results[0].keys())
    else:
        fieldnames = ['file_id','filename','local_path','thumbnail_path','google_mentions','reddit_mentions','nitter_mentions','virality_score','is_underreported','check_timestamp']
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    
    # Summary stats
    underreported_count = sum(1 for r in results if r.get('is_underreported') is True or str(r.get('is_underreported')).lower() == 'true')
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Social media check complete!")
    logger.info(f"📊 Total files analyzed: {len(results_df)}")
    logger.info(f"🔥 Underreported items: {underreported_count}")
    logger.info(f"💾 Results saved:")
    logger.info(f"   - {json_path}")
    logger.info(f"   - {csv_path}")
    logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    main()
