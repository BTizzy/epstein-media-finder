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
try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None
try:
    # optional stronger NSFW model (NudeNet) - not required
    from nudenet import NudeClassifier
    _NSFW_CLASSIFIER = NudeClassifier()
except Exception:
    _NSFW_CLASSIFIER = None

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


def detect_faces(image_path: str) -> Dict:
    """
    Detect faces in an image using OpenCV Haar cascade.

    Returns:
        Dict with keys: face_count, faces (list of bboxes)
    """
    res = {'face_count': 0, 'faces': []}
    if cv2 is None:
        logger.debug("OpenCV not available; skipping face detection")
        return res

    try:
        img = cv2.imread(image_path)
        if img is None:
            return res
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
        faces_list = [{'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)} for (x, y, w, h) in faces]
        res['face_count'] = len(faces_list)
        res['faces'] = faces_list
        return res
    except Exception as e:
        logger.debug(f"Face detection failed for {image_path}: {e}")
        return res


def annotate_faces_on_image(image_path: str, out_path: str, faces: List[Dict]) -> bool:
    """
    Draw bounding boxes for faces and save annotated image.
    """
    if cv2 is None or np is None:
        return False
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False
        for f in faces:
            x, y, w, h = f['x'], f['y'], f['w'], f['h']
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cv2.imwrite(out_path, img)
        return True
    except Exception as e:
        logger.debug(f"Failed to annotate faces on {image_path}: {e}")
        return False


def compute_skin_fraction(image_path: str) -> float:
    """
    Simple skin-tone detection heuristic using YCrCb color space.

    Returns:
        Fraction of pixels considered 'skin' (0.0 - 1.0)
    """
    if np is None or cv2 is None:
        return 0.0
    try:
        img = cv2.imread(image_path)
        if img is None:
            return 0.0
        # resize down for speed
        h, w = img.shape[:2]
        scale = 300.0 / max(h, w)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        (y, cr, cb) = cv2.split(img_ycrcb)
        # skin color range in YCrCb
        skin_mask = cv2.inRange(img_ycrcb, (0, 133, 77), (255, 173, 127))
        skin_fraction = float(cv2.countNonZero(skin_mask)) / float(img.shape[0] * img.shape[1])
        return round(skin_fraction, 4)
    except Exception as e:
        logger.debug(f"Skin detection failed for {image_path}: {e}")
        return 0.0


def is_likely_nsfw(image_path: str, ocr_text: str = '') -> Dict:
    """
    Heuristic NSFW detector combining skin-fraction, face presence, and OCR keywords.

    Returns:
        Dict with keys: skin_fraction, face_count, likely_nsfw (bool), reasons (list)
    """
    reasons = []
    sf = compute_skin_fraction(image_path)
    faces = detect_faces(image_path)
    face_count = faces.get('face_count', 0)

    # simple rules
    likely = False
    if sf > 0.30:
        likely = True
        reasons.append(f'high_skin_fraction:{sf}')
    if face_count == 0 and sf > 0.10:
        # skin but no face might indicate nudity
        likely = True
        reasons.append('skin_no_face')

    # OCR keyword check
    low = (ocr_text or '').lower()
    nsfw_keywords = ['nude', 'porn', 'sex', 'sexual', 'explicit']
    for k in nsfw_keywords:
        if k in low:
            likely = True
            reasons.append(f'keyword:{k}')

    # If a stronger classifier is available, use it and combine results
    model_score = None
    if _NSFW_CLASSIFIER is not None:
        try:
            out = _NSFW_CLASSIFIER.classify(image_path)
            # NudeClassifier.classify returns dict {path: {'unsafe': 0.9, 'safe': 0.1}}
            if isinstance(out, dict) and image_path in out:
                model_score = out[image_path].get('unsafe') or out[image_path].get('probability') or None
            else:
                # sometimes the result key is the filename
                key = list(out.keys())[0]
                model_score = out[key].get('unsafe') or out[key].get('probability') or None
        except Exception as e:
            logger.debug(f"NSFW model failed for {image_path}: {e}")

    # If model indicates high unsafe probability, prefer that
    if model_score is not None:
        try:
            if float(model_score) >= 0.6:
                likely = True
                reasons.append(f'model_unsafe:{model_score}')
            elif float(model_score) >= 0.35:
                # borderline
                reasons.append(f'model_borderline:{model_score}')
        except Exception:
            pass

    return {'skin_fraction': sf, 'face_count': face_count, 'likely_nsfw': bool(likely), 'reasons': reasons, 'model_score': model_score}
