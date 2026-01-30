"""
Script 1: Fetch DOJ Data Set 9 File Manifest
Scrapes the DOJ website to get list of all files in Data Set 9
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
from tqdm import tqdm
import logging
from utils.doj_scraper import fetch_dataset9_page, extract_file_links, filter_media_files, estimate_file_size

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Fetch and save Data Set 9 file manifest"""
    
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info("Starting Data Set 9 manifest fetch...")
    logger.info(f"Target URL: {config['doj']['dataset9_url']}")
    
    # Fetch page
    soup = fetch_dataset9_page(config['doj']['dataset9_url'])
    if not soup:
        logger.error("Failed to fetch DOJ page")
        return
    
    # Extract file links
    all_files = extract_file_links(soup, config['doj']['base_url'])
    logger.info(f"Total files found: {len(all_files)}")
    
    # Filter to media only
    media_files = filter_media_files(all_files, config['media_filters']['types'])
    logger.info(f"Media files found: {len(media_files)}")
    
    # Build manifest with progress bar
    manifest_data = []
    for file_info in tqdm(media_files, desc="Building manifest"):
        file_id = file_info['filename'].replace('.pdf', '').replace('.jpg', '').replace('.png', '')
        
        manifest_data.append({
            'file_id': file_id,
            'filename': file_info['filename'],
            'url': file_info['url'],
            'extension': file_info['extension'],
            'estimated_size': estimate_file_size(file_info['url']),
            'source_page': config['doj']['dataset9_url']
        })
    
    # Save to CSV
    df = pd.DataFrame(manifest_data)
    os.makedirs('data/manifests', exist_ok=True)
    output_path = config['output']['manifest_file']
    df.to_csv(output_path, index=False)
    
    logger.info(f"✅ Manifest saved: {output_path}")
    logger.info(f"📊 Total media files: {len(df)}")
    logger.info(f"📝 Breakdown by type:")
    print(df['extension'].value_counts())

if __name__ == "__main__":
    main()
