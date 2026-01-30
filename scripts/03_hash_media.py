"""
Script 3: Hash Media Files
Compute perceptual hashes and extract metadata from downloaded images
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tqdm import tqdm
import logging
from utils.media_processor import compute_image_hashes, extract_image_metadata, create_thumbnail, is_valid_image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Hash all downloaded media files"""
    
    # Load manifest
    manifest_path = 'data/manifests/dataset9_media_manifest.csv'
    df = pd.read_csv(manifest_path)
    
    # Filter to downloaded files
    downloaded = df[df['downloaded'] == True].copy()
    logger.info(f"Processing {len(downloaded)} downloaded files")
    
    # Create thumbnail directory
    thumb_dir = 'data/downloaded_media/thumbnails'
    os.makedirs(thumb_dir, exist_ok=True)
    
    # Process each file
    results = []
    for idx, row in tqdm(downloaded.iterrows(), total=len(downloaded), desc="Hashing"):
        local_path = row['local_path']
        
        # Skip non-image files for now (videos need frame extraction)
        if row['extension'] in ['mp4', 'mov', 'avi']:
            logger.info(f"⏭️  Skipping video (not implemented): {row['filename']}")
            continue
        
        # Validate image
        if not is_valid_image(local_path):
            logger.error(f"❌ Invalid image: {row['filename']}")
            continue
        
        # Compute hashes
        hashes = compute_image_hashes(local_path)
        
        # Extract metadata
        metadata = extract_image_metadata(local_path)
        
        # Create thumbnail
        thumb_path = os.path.join(thumb_dir, f"thumb_{row['filename']}")
        create_thumbnail(local_path, thumb_path)
        
        results.append({
            'file_id': row['file_id'],
            'filename': row['filename'],
            'local_path': local_path,
            'phash': hashes['phash'],
            'average_hash': hashes['average_hash'],
            'dhash': hashes['dhash'],
            'width': metadata['width'],
            'height': metadata['height'],
            'format': metadata['format'],
            'thumbnail_path': thumb_path
        })
    
    # Save hash database
    hash_df = pd.DataFrame(results)
    hash_path = 'data/manifests/media_hashes.csv'
    hash_df.to_csv(hash_path, index=False)
    
    logger.info(f"✅ Processed {len(hash_df)} images")
    logger.info(f"💾 Hash database saved: {hash_path}")
    logger.info(f"🖼️  Thumbnails saved: {thumb_dir}")

if __name__ == "__main__":
    main()
