"""
Script 3: Hash Media Files
Compute perceptual hashes and extract metadata from downloaded images
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from tqdm import tqdm
import logging
from utils.media_processor import (
    compute_image_hashes,
    extract_image_metadata,
    create_thumbnail,
    is_valid_image,
    detect_faces,
    annotate_faces_on_image,
    compute_skin_fraction,
    is_likely_nsfw,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Hash all downloaded media files"""
    
    # Instead of relying on the manifest's downloaded column (which may be incomplete),
    # process all files present in the download directory that haven't been hashed yet.
    download_dir = 'data/downloaded_media'
    all_files = [f for f in os.listdir(download_dir) if f.lower().endswith('.pdf')]

    # Load existing hashes to avoid reprocessing
    hash_path = 'data/manifests/media_hashes.csv'
    processed = set()
    if os.path.exists(hash_path):
        with open(hash_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for r in reader:
                processed.add(r.get('local_path') or '')

    downloaded = []
    for f in all_files:
        local_path = os.path.join(download_dir, f)
        if local_path in processed:
            continue
        downloaded.append({'file_id': os.path.splitext(f)[0], 'filename': f, 'local_path': local_path, 'extension': 'pdf'})

    logger.info(f"Processing {len(downloaded)} downloaded files")
    
    # Create thumbnail directory
    thumb_dir = 'data/downloaded_media/thumbnails'
    os.makedirs(thumb_dir, exist_ok=True)
    
    # Process each file
    results = []
    for idx, row in enumerate(tqdm(downloaded, total=len(downloaded), desc="Hashing")):
        local_path = row.get('local_path')
        
        # Handle PDFs: render all pages (skip TOC pages) and process each page image
        if row.get('extension') == 'pdf':
            pdf_path = local_path
            images_out_dir = os.path.join('data', 'downloaded_media', 'rendered_pages')
            os.makedirs(images_out_dir, exist_ok=True)
            from utils.media_processor import render_pdf_pages

            pages = render_pdf_pages(pdf_path, images_out_dir, dpi=200)
            logger.info(f"Rendered {len(pages)} pages from PDF: {row.get('filename')}")

            # Simple keyword list for 'interesting' content
            keywords = ['video', 'photo', 'flight', 'payment', 'bank', 'phone', 'escort', 'model', 'minor', 'underage', 'nude', 'sex', 'abuse', 'passport']

            for p in pages:
                if p.get('is_toc'):
                    logger.debug(f"Skipping TOC page: {row.get('filename')} p{p.get('page_number')}")
                    continue

                img_path = p.get('image_path')
                text = p.get('text', '') or ''

                if not is_valid_image(img_path):
                    logger.error(f"❌ Invalid rendered image: {img_path}")
                    continue

                hashes = compute_image_hashes(img_path)
                metadata = extract_image_metadata(img_path)
                thumb_path = os.path.join(thumb_dir, f"thumb_{row.get('file_id')}_p{p.get('page_number')}.png")
                create_thumbnail(img_path, thumb_path, size=(400,400))
                # Face detection and NSFW heuristics
                faces = detect_faces(img_path)
                skin_frac = compute_skin_fraction(img_path)
                nsfw = is_likely_nsfw(img_path, ocr_text=text)

                # Create an annotated version of the thumbnail showing faces (if any)
                annotated_thumb = os.path.join(thumb_dir, f"annotated_{row.get('file_id')}_p{p.get('page_number')}.png")
                annotate_faces_on_image(img_path, annotated_thumb, faces.get('faces', []))

                # keyword matches
                found_keywords = [k for k in keywords if k in text.lower()]

                results.append({
                    'file_id': f"{row.get('file_id')}|p{p.get('page_number')}",
                    'filename': os.path.basename(img_path),
                    'local_path': img_path,
                    'phash': hashes['phash'],
                    'average_hash': hashes['average_hash'],
                    'dhash': hashes['dhash'],
                    'width': metadata['width'],
                    'height': metadata['height'],
                    'format': metadata['format'],
                    'thumbnail_path': thumb_path,
                    'annotated_thumbnail': annotated_thumb,
                    'face_count': faces.get('face_count', 0),
                    'skin_fraction': skin_frac,
                    'likely_nsfw': nsfw.get('likely_nsfw', False),
                    'nsfw_reasons': ','.join(nsfw.get('reasons', [])),
                    'page_text_snippet': text[:500],
                    'keywords_found': ','.join(found_keywords)
                })

            # done with this PDF
            continue
            continue
        
        # Validate image
        if not is_valid_image(local_path):
            logger.error(f"❌ Invalid image: {row.get('filename')}")
            continue
        
        # Compute hashes
        hashes = compute_image_hashes(local_path)
        
        # Extract metadata
        metadata = extract_image_metadata(local_path)
        
        # Create thumbnail
        thumb_path = os.path.join(thumb_dir, f"thumb_{row['filename']}")
        create_thumbnail(local_path, thumb_path)
        
        results.append({
            'file_id': row.get('file_id'),
            'filename': row.get('filename'),
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
    hash_path = 'data/manifests/media_hashes.csv'
    if results:
        fieldnames = list(results[0].keys())
    else:
        fieldnames = ['file_id','filename','local_path','phash','average_hash','dhash','width','height','format','thumbnail_path']
    with open(hash_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    
    logger.info(f"✅ Processed {len(results)} images")
    logger.info(f"💾 Hash database saved: {hash_path}")
    logger.info(f"🖼️  Thumbnails saved: {thumb_dir}")

if __name__ == "__main__":
    main()
