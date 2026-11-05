"""Validate the editable catalog and build the dependency-free GitHub Pages site."""
from pathlib import Path
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent
RANKS = {'S', 'A', 'B', 'C', 'D', 'F'}


def validate_image(value):
    from urllib.parse import urlsplit
    if not value:
        return
    assert isinstance(value, str), 'Image URL must be a string'
    if value.startswith('media/'):
        assert re.fullmatch(r'media/[a-zA-Z0-9-]+\.(?:webp|png|jpe?g)', value), 'Invalid image path'
        assert (ROOT / value).is_file(), f'Missing image: {value}'
    else:
        url = urlsplit(value)
        assert url.scheme == 'https' and url.hostname and not url.username and not url.password, 'Images require HTTPS'


def editorial_today():
    try:
        return datetime.now(ZoneInfo('Europe/Kyiv')).date()
    except ZoneInfoNotFoundError:
        # Windows without a tz database: use the author's local system date.
        return date.today()


def validate(data):
    assert isinstance(data, dict), 'Catalog must be an object'
    categories = data.get('categories', [])
    lists = data.get('lists', [])
    assert categories and lists, 'Categories and lists cannot be empty'
    ids = [c['id'] for c in categories]
    assert len(ids) == len(set(ids)), 'Duplicate category IDs'
    seen = set()
    for entry in lists:
        slug = entry.get('id', '')
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug), f'Invalid list ID: {slug}'
        assert slug not in seen, f'Duplicate list: {slug}'
        seen.add(slug)
        assert entry.get('category') in ids, f'{slug}: unknown category'
        assert entry.get('theme') in {'sand', 'rose', 'sage', 'sky', 'peach', 'lavender', 'butter', 'mint'}, f'{slug}: invalid theme'
        for key in ('title', 'description', 'criteria', 'icon'):
            assert isinstance(entry.get(key), str) and entry[key].strip(), f'{slug}: missing {key}'
        validate_image(entry.get('image'))
        assert len(entry['title']) <= 85, f'{slug}: title exceeds 85 characters'
        assert date.fromisoformat(entry['created']) <= date.fromisoformat(entry['updated']) <= editorial_today(), f'{slug}: invalid dates'
        items = entry.get('items', [])
        assert 1 <= len(items) <= 250, f'{slug}: expected 1-250 items'
        item_ids = set()
        for item in items:
            assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', item.get('id', '')), f'{slug}: invalid item ID'
            assert item['id'] not in item_ids, f'{slug}: duplicate item {item["id"]}'
            item_ids.add(item['id'])
            assert item.get('tier') in RANKS, f'{slug}: unknown tier'
            validate_image(item.get('image'))
            for key in ('name', 'emoji', 'note'):
                assert isinstance(item.get(key), str) and item[key].strip(), f'{slug}: item missing {key}'
            assert len(item['name']) <= 70, f'{slug}: item name too long'
        assert entry.get('history'), f'{slug}: add a history entry'
        for event in entry['history']:
            assert entry['created'] <= event['date'] <= entry['updated'], f'{slug}: history date outside range'
            date.fromisoformat(event['date'])
            assert event.get('text'), f'{slug}: empty history entry'
    return data


def build():
    data = validate(json.loads((ROOT / 'data/tiers.json').read_text(encoding='utf-8')))
    target = ROOT / 'docs'
    target.mkdir(exist_ok=True)
    for name in ('app.js', 'core.js', 'style.css', 'favicon.svg'):
        shutil.copy2(ROOT / 'src' / name, target / name)
    if (ROOT / 'media').exists():
        shutil.copytree(ROOT / 'media', target / 'media', dirs_exist_ok=True)
    admin = target / 'admin'
    admin.mkdir(exist_ok=True)
    for name in ('core.js', 'admin.js', 'admin.css'):
        shutil.copy2(ROOT / 'src/admin' / name, admin / name)
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    (target / 'content.js').write_text('window.TIER_DATA=' + payload + ';\n', encoding='utf-8')
    html = (ROOT / 'src/index.html').read_text(encoding='utf-8')
    for name in ('app.js', 'core.js', 'content.js', 'style.css', 'favicon.svg'):
        digest = hashlib.sha256((target / name).read_bytes()).hexdigest()[:12]
        html = html.replace('"' + name + '"', '"' + name + '?v=' + digest + '"')
    (target / 'index.html').write_text(html, encoding='utf-8')
    admin_html = (ROOT / 'src/admin/index.html').read_text(encoding='utf-8')
    for path in ('../content.js', '../style.css', 'core.js', 'admin.js', 'admin.css'):
        digest = hashlib.sha256((admin / path).read_bytes()).hexdigest()[:12]
        admin_html = admin_html.replace('"' + path + '"', '"' + path + '?v=' + digest + '"')
    (admin / 'index.html').write_text(admin_html, encoding='utf-8')
    (target / '.nojekyll').touch()
    print(f'Built {len(data["lists"])} lists, {sum(len(l["items"]) for l in data["lists"])} items -> docs/')


if __name__ == '__main__':
    build()
