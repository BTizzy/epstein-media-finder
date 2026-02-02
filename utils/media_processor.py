"""
Media Processing Utilities
Handles image hashing, metadata extraction, and thumbnail generation
"""

from PIL import Image
import imagehash
from typing import Dict, Tuple, Optional
import re
import logging
import os
from typing import List
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

def render_pdf_pages(pdf_path: str, output_dir: str, dpi: int = 150, skip_toc: bool = True) -> list:
    """
    Render each page of a PDF to an image and extract page text.

    Args:
        pdf_path: Path to PDF
        output_dir: Directory to save rendered pages
        dpi: Rendering DPI (affects resolution)
        skip_toc: Whether to mark pages that look like a table-of-contents

    Returns:
        List of dicts: {page_number, image_path, text, is_toc}
    """
    pages = []
    if fitz is None:
        logger.error("PyMuPDF (fitz) not installed; cannot render PDF pages")
        return pages

    os.makedirs(output_dir, exist_ok=True)
    try:
        doc = fitz.open(pdf_path)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        scale = dpi / 72  # default 72 dpi baseline
        matrix = fitz.Matrix(scale, scale)

        for i, page in enumerate(doc, start=1):
            text = page.get_text('text')

            # Heuristic to detect table of contents
            is_toc = False
            if skip_toc:
                lower = text.lower()
                if 'table of contents' in lower or '\ncontents\n' in lower or re.search(r'\bcontents\b', lower):
                    is_toc = True
                # many short lines with page numbers indicates TOC
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                if len(lines) > 5:
                    count_nums = sum(1 for ln in lines if re.search(r'\b\d{1,3}\b$', ln))
                    if count_nums / max(1, len(lines)) > 0.4:
                        is_toc = True

            pix = page.get_pixmap(matrix=matrix)
            out_path = os.path.join(output_dir, f"{base}_p{i}.png")
            pix.save(out_path)

            pages.append({'page_number': i, 'image_path': out_path, 'text': text, 'is_toc': is_toc})

        doc.close()
    except Exception as e:
        logger.error(f"Error rendering pages from {pdf_path}: {e}")

    return pages

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


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> List[str]:
    """
    Extract embedded images from a PDF using PyMuPDF

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images

    Returns:
        List of saved image file paths
    """
    saved = []
    if fitz is None:
        logger.error("PyMuPDF (fitz) not installed; cannot extract images from PDF")
        return saved

    os.makedirs(output_dir, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
        base = os.path.splitext(os.path.basename(pdf_path))[0]

        for page_index in range(len(doc)):
            page = doc[page_index]
            images = page.get_images(full=True)
            for img_index, img in enumerate(images, start=1):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n < 5:
                    ext = "png"
                    out_path = os.path.join(output_dir, f"{base}_p{page_index+1}_img{img_index}.{ext}")
                    pix.save(out_path)
                    saved.append(out_path)
                else:
                    # CMYK: convert to RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    ext = "png"
                    out_path = os.path.join(output_dir, f"{base}_p{page_index+1}_img{img_index}.{ext}")
                    pix.save(out_path)
                    saved.append(out_path)
                pix = None

        # If no embedded images were found, render pages as images
        if not saved:
            logger.info(f"No embedded images found in {pdf_path}; rendering pages to images")
            for page_index in range(len(doc)):
                try:
                    page = doc[page_index]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    out_path = os.path.join(output_dir, f"{base}_p{page_index+1}.png")
                    pix.save(out_path)
                    saved.append(out_path)
                except Exception as e:
                    logger.debug(f"Failed to render page {page_index+1}: {e}")

        doc.close()
    except Exception as e:
        logger.error(f"Error extracting images from PDF {pdf_path}: {e}")

    return saved
