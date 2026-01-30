"""
DOJ Website Scraping Utilities
Handles fetching and parsing DOJ Epstein file listings
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging
from fake_useragent import UserAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_random_headers() -> Dict[str, str]:
    """Generate random browser headers to avoid blocking"""
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

def fetch_dataset9_page(url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
    """
    Fetch DOJ Data Set 9 page and return parsed HTML
    
    Args:
        url: DOJ page URL
        max_retries: Number of retry attempts
        
    Returns:
        BeautifulSoup object or None if failed
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=get_random_headers(), timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.error(f"Error fetching page: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    return None

def extract_file_links(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    """
    Extract all file links from parsed DOJ page
    
    Args:
        soup: BeautifulSoup parsed HTML
        base_url: Base URL to resolve relative links
        
    Returns:
        List of dicts with file metadata
    """
    files = []
    
    # Look for links containing EFTA or epstein/files
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'EFTA' in href or 'epstein/files' in href:
            # Handle relative URLs
            if not href.startswith('http'):
                href = base_url + href
            
            filename = href.split('/')[-1]
            extension = filename.split('.')[-1].lower() if '.' in filename else ''
            
            files.append({
                'filename': filename,
                'url': href,
                'extension': extension,
                'link_text': link.get_text(strip=True)
            })
    
    logger.info(f"Extracted {len(files)} file links")
    return files

def filter_media_files(file_list: List[Dict], allowed_extensions: List[str]) -> List[Dict]:
    """
    Filter file list to only media types
    
    Args:
        file_list: List of file dicts
        allowed_extensions: List of allowed extensions
        
    Returns:
        Filtered list containing only media files
    """
    media_files = [f for f in file_list if f['extension'] in allowed_extensions]
    logger.info(f"Filtered to {len(media_files)} media files from {len(file_list)} total")
    return media_files

def estimate_file_size(url: str) -> Optional[int]:
    """
    Estimate file size using HEAD request
    
    Args:
        url: File URL
        
    Returns:
        Size in bytes or None if unavailable
    """
    try:
        response = requests.head(url, headers=get_random_headers(), timeout=5)
        size = response.headers.get('Content-Length')
        return int(size) if size else None
    except Exception as e:
        logger.debug(f"Could not get size for {url}: {e}")
        return None
