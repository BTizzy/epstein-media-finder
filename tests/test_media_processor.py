import os
from PIL import Image
from utils.media_processor import compute_skin_fraction, detect_faces, is_likely_nsfw


def test_skin_fraction_on_synthetic_image(tmp_path):
    # Create a synthetic image with a large skin-like color rectangle
    img_path = tmp_path / 'skin.png'
    img = Image.new('RGB', (300, 300), (198, 134, 66))
    img.save(img_path)

    sf = compute_skin_fraction(str(img_path))
    # ensure a valid fraction between 0 and 1
    assert 0.0 <= sf <= 1.0


def test_detect_faces_returns_int(tmp_path):
    # Simple check: function returns a dict with face_count
    img_path = tmp_path / 'blank.png'
    Image.new('RGB', (200, 200), (255, 255, 255)).save(img_path)
    res = detect_faces(str(img_path))
    assert 'face_count' in res


def test_is_likely_nsfw_by_keyword(tmp_path):
    img_path = tmp_path / 'blank2.png'
    Image.new('RGB', (200, 200), (255, 255, 255)).save(img_path)
    res = is_likely_nsfw(str(img_path), ocr_text='This contains nude content')
    assert res.get('likely_nsfw') is True


def test_interest_score_increases_with_face():
    # Synthetic item with face_count should score higher than without
    from utils.social_checker import compute_interest_score
    item_no_face = {'keywords_found': '', 'phash': '', 'local_path': ''}
    item_with_face = {'keywords_found': '', 'phash': '', 'local_path': '', 'face_count': 2}
    score_no = compute_interest_score(item_no_face, items=[item_no_face, item_with_face])
    score_yes = compute_interest_score(item_with_face, items=[item_no_face, item_with_face])
    assert score_yes >= score_no
