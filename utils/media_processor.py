"""
Media Processing Utilities
Handles image hashing, metadata extraction, and thumbnail generation
"""

from PIL import Image
import imagehash
from typing import Dict, Tuple, Optional
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_image_hashes(image_path: str) -> Dict[str, str]:
    """
    Compute perceptual hashes for an image
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dict with phash, average_hash, and dhash as hex strings
    """
    try:
        img = Image.open(image_path)
        return {
            'phash': str(imagehash.phash(img)),
            'average_hash': str(imagehash.average_hash(img)),
            'dhash': str(imagehash.dhash(img))
        }
    except Exception as e:
        logger.error(f"Error computing hashes for {image_path}: {e}")
        return {'phash': '', 'average_hash': '', 'dhash': ''}

def extract_image_metadata(image_path: str) -> Dict:
    """
    Extract basic image metadata
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dict with width, height, format, mode
    """
    try:
        img = Image.open(image_path)
        return {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode
        }
    except Exception as e:
        logger.error(f"Error extracting metadata from {image_path}: {e}")
        return {'width': 0, 'height': 0, 'format': '', 'mode': ''}

def create_thumbnail(image_path: str, output_path: str, size: Tuple[int, int] = (200, 200)) -> bool:
    """
    Create and save thumbnail of image
    
    Args:
        image_path: Source image path
        output_path: Output thumbnail path
        size: Thumbnail dimensions
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        img = Image.open(image_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(output_path)
        logger.debug(f"Created thumbnail: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating thumbnail for {image_path}: {e}")
        return False

def is_valid_image(image_path: str) -> bool:
    """
    Check if file is a valid image
    
    Args:
        image_path: Path to image file
        
    Returns:
        True if valid image, False otherwise
    """
    try:
        img = Image.open(image_path)
        img.verify()
        return True
    except Exception:
        return False
