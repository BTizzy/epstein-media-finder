"""
Script 1: Fetch DOJ Data Set 9 File Manifest
Scrapes the DOJ website to get list of all files in Data Set 9
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import csv
from collections import Counter
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
    os.makedirs('data/manifests', exist_ok=True)
    output_path = config['output']['manifest_file']
    if manifest_data:
        fieldnames = list(manifest_data[0].keys())
    else:
        fieldnames = ['file_id', 'filename', 'url', 'extension', 'estimated_size', 'source_page']

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest_data:
            writer.writerow(row)
    
    logger.info(f"✅ Manifest saved: {output_path}")
    logger.info(f"📊 Total media files: {len(manifest_data)}")
    logger.info(f"📝 Breakdown by type:")
    counts = Counter([m['extension'] for m in manifest_data])
    for ext, cnt in counts.most_common():
        print(f"{ext}: {cnt}")

if __name__ == "__main__":
    main()
