"""
Script 4: Check Social Media Presence (FREE VERSION)
Uses web scraping to check if files are already viral - NO API COSTS
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
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
    df = pd.read_csv(hash_path)
    logger.info(f"Checking social presence for {len(df)} files")
    
    results = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Checking social media"):
        file_id = row['file_id']
        filename = row['filename']
        
        logger.info(f"Checking: {filename}")
        
        # Search queries
        queries = [
            filename,  # Exact filename
            file_id,   # File ID
            f"{file_id} epstein",  # With context
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
                rate_limit_delay()
            except Exception as e:
                logger.error(f"Google search failed: {e}")
            
            # Reddit search
            try:
                reddit_count = reddit_count_mentions(query, config['social_platforms']['reddit_subreddits'])
                total_reddit += reddit_count
                logger.info(f"  Reddit '{query}': {reddit_count} posts")
                rate_limit_delay()
            except Exception as e:
                logger.error(f"Reddit search failed: {e}")
            
            # Nitter search (Twitter mirror)
            try:
                nitter_count = nitter_search(query, config['social_platforms']['nitter_instances'])
                total_nitter += nitter_count
                logger.info(f"  Nitter '{query}': {nitter_count} tweets")
                rate_limit_delay()
            except Exception as e:
                logger.error(f"Nitter search failed: {e}")
        
        # Calculate virality score
        score = calculate_free_virality_score(total_google, total_reddit, total_nitter)
        underreported = is_underreported(score)
        
        logger.info(f"  📊 Virality Score: {score} - {'🔥 UNDERREPORTED' if underreported else '✅ Known'}")
        
        results.append({
            'file_id': file_id,
            'filename': filename,
            'local_path': row['local_path'],
            'thumbnail_path': row['thumbnail_path'],
            'google_mentions': total_google,
            'reddit_mentions': total_reddit,
            'nitter_mentions': total_nitter,
            'virality_score': score,
            'is_underreported': underreported,
            'check_timestamp': datetime.now().isoformat()
        })
        
        # Extra delay between files
        rate_limit_delay(3, 5)
    
    # Save results
    results_df = pd.DataFrame(results)
    
    # JSON output (full data)
    json_path = config['output']['results_file']
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    results_df.to_json(json_path, orient='records', indent=2)
    
    # CSV output (summary)
    csv_path = 'data/results/underreported_media.csv'
    results_df.to_csv(csv_path, index=False)
    
    # Summary stats
    underreported_count = results_df['is_underreported'].sum()
    
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
