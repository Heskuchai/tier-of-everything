import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import ROOT, validate, validate_image


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data/tiers.json').read_text(encoding='utf-8'))

    def test_catalog(self):
        validate(self.data)

    def test_duplicate_item_rejected(self):
        self.data['lists'][0]['items'].append(copy.deepcopy(self.data['lists'][0]['items'][0]))
        with self.assertRaisesRegex(AssertionError, 'duplicate item'):
            validate(self.data)

    def test_invalid_tier_rejected(self):
        self.data['lists'][0]['items'][0]['tier'] = 'Z'
        with self.assertRaisesRegex(AssertionError, 'unknown tier'):
            validate(self.data)

    def test_unsafe_slug_rejected(self):
        self.data['lists'][0]['id'] = '../unsafe'
        with self.assertRaisesRegex(AssertionError, 'Invalid list ID'):
            validate(self.data)

    def test_unknown_category_rejected(self):
        self.data['lists'][0]['category'] = 'missing'
        with self.assertRaisesRegex(AssertionError, 'unknown category'):
            validate(self.data)

    def test_executable_and_insecure_images_rejected(self):
        for value in ('javascript:alert(1)', 'data:image/png;base64,AAAA', 'http://example.com/a.png', 'media/../x.webp'):
            with self.assertRaises(AssertionError):
                validate_image(value)

    def test_missing_upload_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'Missing image'):
            validate_image('media/nonexistent-upload.webp')

    def test_https_image_accepted(self):
        validate_image('https://example.com/image.png')


if __name__ == '__main__':
    unittest.main()
