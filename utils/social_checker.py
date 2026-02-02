"""
Social Media Presence Checker (FREE - No API Keys Required)
Uses web scraping and public endpoints to check social media presence
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import random
import logging
from fake_useragent import UserAgent
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_random_user_agent() -> str:
    """Generate random User-Agent string"""
    ua = UserAgent()
    return ua.random

def rate_limit_delay(min_seconds: int = 2, max_seconds: int = 4):
    """Add random delay to avoid rate limiting"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def google_search_count(query: str, max_retries: int = 3) -> int:
    """
    Get approximate result count from Google search (FREE)
    
    Args:
        query: Search query
        max_retries: Number of retry attempts
        
    Returns:
        Approximate number of results
    """
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            
            response = requests.get(url, headers=headers, timeout=10)
            try:
                soup = BeautifulSoup(response.text, 'lxml')
            except Exception:
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find result count
            result_stats = soup.find('div', {'id': 'result-stats'})
            if result_stats:
                text = result_stats.get_text()
                # Extract number from "About X results"
                import re
                match = re.search(r'([\d,]+)\s+results?', text)
                if match:
                    count_str = match.group(1).replace(',', '')
                    return int(count_str)
            
            return 0
        except Exception as e:
            logger.error(f"Google search error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                rate_limit_delay(3, 6)
    
    return 0

def reddit_json_search(query: str, subreddits: Optional[List[str]] = None, limit: int = 50) -> List[Dict]:
    """
    Search Reddit using free JSON API (NO AUTH REQUIRED)
    
    Args:
        query: Search term
        subreddits: Optional list of subreddits to search
        limit: Max results per request
        
    Returns:
        List of matching post dicts
    """
    posts = []
    
    try:
        headers = {'User-Agent': get_random_user_agent()}
        
        if subreddits:
            # Search specific subreddits
            for sub in subreddits:
                url = f"https://www.reddit.com/r/{sub}/search.json?q={requests.utils.quote(query)}&limit={limit}&restrict_sr=1"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'children' in data['data']:
                        posts.extend([child['data'] for child in data['data']['children']])
                
                rate_limit_delay(0.2, 0.5)
        else:
            # Search all of Reddit
            url = f"https://www.reddit.com/search.json?q={requests.utils.quote(query)}&limit={limit}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'children' in data['data']:
                    posts = [child['data'] for child in data['data']['children']]
        
        logger.info(f"Found {len(posts)} Reddit posts for '{query}'")
        return posts
        
    except Exception as e:
        logger.error(f"Reddit search error: {e}")
        return []

def reddit_count_mentions(term: str, subreddits: Optional[List[str]] = None) -> int:
    """
    Count total Reddit mentions using free JSON API
    
    Args:
        term: Search term
        subreddits: Optional list of subreddits
        
    Returns:
        Total mention count
    """
    posts = reddit_json_search(term, subreddits)
    return len(posts)

def nitter_search(term: str, instances: List[str] = None) -> int:
    """
    Search Twitter via Nitter (FREE Twitter mirror - NO API)
    
    Args:
        term: Search term
        instances: List of Nitter instances to try
        
    Returns:
        Approximate mention count
    """
    if instances is None:
        instances = ['nitter.net', 'nitter.42l.fr', 'nitter.fdn.fr']
    
    for instance in instances:
        try:
            headers = {'User-Agent': get_random_user_agent()}
            url = f"https://{instance}/search?q={requests.utils.quote(term)}"
            
            response = requests.get(url, headers=headers, timeout=10)
            try:
                soup = BeautifulSoup(response.text, 'lxml')
            except Exception:
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # Count tweet items
            tweets = soup.find_all('div', class_='timeline-item')
            count = len(tweets)
            
            if count > 0:
                logger.info(f"Found {count} tweets on {instance} for '{term}'")
                return count
            
                rate_limit_delay(0.2, 0.5)
            
        except Exception as e:
            logger.debug(f"Nitter instance {instance} failed: {e}")
            continue
    
    return 0

def calculate_free_virality_score(google_count: int, reddit_count: int, nitter_count: int) -> float:
    """
    Calculate virality score from free sources
    
    Args:
        google_count: Google search results
        reddit_count: Reddit post count
        nitter_count: Twitter/Nitter mention count
        
    Returns:
        Weighted virality score
    """
    # Normalize Google count (divide by 100)
    # Weight: Reddit posts = 3x, Nitter = 2x
    score = (google_count / 100) + (reddit_count * 3) + (nitter_count * 2)
    return round(score, 2)


def compute_interest_score(item: Dict, items: Optional[List[Dict]] = None, keyword_weight: int = 3, uniqueness_weight: int = 3) -> float:
    """
    Compute an interest score for an item based on keywords found and image uniqueness.

    Args:
        item: Dict containing 'keywords_found' (comma-separated) and 'phash'
        items: Optional list of all items to compute uniqueness
        keyword_weight: Weight applied per keyword
        uniqueness_weight: Weight for uniqueness measure

    Returns:
        Floating interest score
    """
    score = 0.0

    # Keyword bonus (higher weight for strong keywords)
    kw = item.get('keywords_found', '')
    kws = [k for k in kw.split(',') if k]
    strong = {'video', 'photo', 'flight', 'payment', 'bank', 'phone', 'escort', 'model', 'minor', 'underage', 'nude', 'sex', 'passport', 'log'}
    kw_score = 0
    for k in kws:
        if k in strong:
            kw_score += (keyword_weight * 2)
        else:
            kw_score += keyword_weight
    score += kw_score

    # Uniqueness: count same phash occurrences
    phash = item.get('phash', '')
    dup_count = 0
    if items and phash:
        dup_count = sum(1 for it in items if it.get('phash') == phash)

    uniqueness = 1.0 / (1 + dup_count)
    score += uniqueness * uniqueness_weight

    # Photo likelihood: basic image variance heuristic
    img_path = item.get('local_path')
    try:
        from PIL import Image, ImageStat
        if img_path and os.path.exists(img_path):
            img = Image.open(img_path).convert('L').resize((200,200))
            st = ImageStat.Stat(img)
            # use standard deviation as proxy for 'photo-likeness'
            stddev = st.stddev[0]
            # normalize (~0-100) to 0-3 scale
            photo_score = min(3.0, (stddev / 30.0))
            score += photo_score
    except Exception:
        pass

    return round(score, 2)


def filter_underreported_candidates(items: List[Dict], virality_threshold: float = 5.0, min_interest: float = 3.5) -> List[Dict]:
    """
    Filter items to those that are underreported (low virality) but high interest.

    Args:
        items: List of item dicts (must include virality_score and keywords_found)
        virality_threshold: Maximum virality score to consider underreported
        min_interest: Minimum interest score to be considered worth attention

    Returns:
        Filtered and sorted list (by interest desc)
    """
    scored = []
    for it in items:
        vir = float(it.get('virality_score', 0) or 0)
        interest = compute_interest_score(it, items)
        it['_interest_score'] = interest
        # Require either meaningful keywords or a higher interest score
        # Accept items with sufficient interest even if no explicit keywords
        if vir < virality_threshold and interest >= min_interest:
            scored.append(it)

    scored = sorted(scored, key=lambda x: x['_interest_score'], reverse=True)
    return scored

def is_underreported(score: float, threshold: float = 5.0) -> bool:
    """
    Determine if content is underreported based on score
    
    Args:
        score: Virality score
        threshold: Score threshold
        
    Returns:
        True if underreported (below threshold)
    """
    return score < threshold

def retry_with_backoff(func, max_attempts: int = 3, *args, **kwargs):
    """
    Retry function with exponential backoff
    
    Args:
        func: Function to retry
        max_attempts: Maximum retry attempts
        
    Returns:
        Function result or None if all attempts fail
    """
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
    return None
