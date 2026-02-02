"""
Script 2: Download Sample Media Files
Downloads first N media files from manifest for analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import requests
from tqdm import tqdm
import time
import logging
from dotenv import load_dotenv
from utils.doj_scraper import get_random_headers

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_file(url: str, output_path: str, max_retries: int = 3) -> bool:
    """Download file with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=get_random_headers(), timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            logger.error(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return False

def main():
    """Download sample media files"""
    
    # Load environment
    max_downloads = int(os.getenv('MAX_MEDIA_TO_DOWNLOAD', 50))
    
    # Load manifest
    manifest_path = 'data/manifests/dataset9_media_manifest.csv'
    if not os.path.exists(manifest_path):
        logger.error(f"Manifest not found: {manifest_path}")
        logger.error("Run script 01 first!")
        return

    with open(manifest_path, newline='') as csvfile:
        reader = list(csv.DictReader(csvfile))

    logger.info(f"Loaded manifest with {len(reader)} files")
    
    # Create download directory
    download_dir = 'data/downloaded_media'
    os.makedirs(download_dir, exist_ok=True)
    
    # Select sample to download
    sample = reader[:max_downloads]
    logger.info(f"Downloading {len(sample)} files...")
    
    # Download with progress bar
    results = []
    for idx, row in enumerate(tqdm(sample, total=len(sample), desc="Downloading")):
        filename = row['filename']
        url = row['url']
        local_path = os.path.join(download_dir, filename)
        
        # Skip if already exists
        if os.path.exists(local_path):
            logger.info(f"⏭️  Skipping (exists): {filename}")
            out = dict(row)
            out.update({'downloaded': True, 'local_path': local_path})
            results.append(out)
            continue
        
        # Download
        success = download_file(url, local_path)
        
        if success:
            file_size = os.path.getsize(local_path)
            logger.info(f"✅ Downloaded: {filename} ({file_size} bytes)")
            out = dict(row)
            out.update({
                'downloaded': True,
                'local_path': local_path,
                'actual_size_bytes': file_size
            })
            results.append(out)
        else:
            logger.error(f"❌ Failed: {filename}")
            out = dict(row)
            out.update({'downloaded': False, 'local_path': None})
            results.append(out)
        
        # Rate limiting
        time.sleep(1)
    
    # Save updated manifest
    fieldnames = list(results[0].keys()) if results else ['file_id', 'filename', 'url', 'extension', 'estimated_size', 'source_page', 'downloaded', 'local_path']
    with open(manifest_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    successful = sum(1 for r in results if str(r.get('downloaded', '')).lower() in ('1', 'true', 'yes'))
    logger.info(f"✅ Successfully downloaded: {successful}/{len(sample)} files")
    logger.info(f"📂 Files saved to: {download_dir}")

if __name__ == "__main__":
    main()
