#!/usr/bin/env python3
"""Create a 250-channel VLC M3U playlist from IPTV-org's public directory.
Run: python create_iptv_250.py
Requires internet when run. Availability and rights vary by region.
"""
import re
from urllib.request import Request, urlopen
from pathlib import Path

SOURCE = 'https://iptv-org.github.io/iptv/index.m3u'
OUTPUT = Path('Sri_Lanka_India_International_250.m3u')
TARGETS = [('Sri Lanka', 30, {'LK'}), ('India', 120, {'IN'}), ('International', 100, None)]

def fetch():
    req = Request(SOURCE, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8-sig', errors='replace')

def parse(data):
    items = []
    lines = data.splitlines()
    for i, line in enumerate(lines[:-1]):
        if not line.startswith('#EXTINF:'):
            continue
        j = i + 1
        extra = []
        while j < len(lines) and lines[j].startswith('#'):
            extra.append(lines[j]); j += 1
        if j >= len(lines) or not lines[j].strip().startswith(('http://', 'https://')):
            continue
        url = lines[j].strip()
        country = re.search(r'group-title="([^"]*)"', line)
        tvgid = re.search(r'tvg-id="([^"]*)"', line)
        title = line.rsplit(',', 1)[-1].strip()
        # IPTV-org uses country codes in tvg-id suffix for many entries.
        cc = (tvgid.group(1).split('.')[-1].upper() if tvgid else '')
        items.append({'info': line, 'extra': extra, 'url': url, 'cc': cc, 'title': title})
    return items

def main():
    items = parse(fetch())
    used = set()
    chosen = []
    for name, quota, countries in TARGETS:
        candidates = [x for x in items if (x['cc'] in countries if countries else x['cc'] not in {'LK', 'IN'})]
        candidates.sort(key=lambda x: (x['title'].casefold(), x['url']))
        count = 0
        for x in candidates:
            if x['url'] in used:
                continue
            chosen.append((name, x)); used.add(x['url']); count += 1
            if count == quota: break
        print(f'{name}: {count}/{quota}')
    out = ['#EXTM3U']
    for category, x in chosen:
        # Keep original channel metadata and HLS stream URL.
        out.extend([x['info'], *x['extra'], x['url']])
    OUTPUT.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'Created {OUTPUT.resolve()} with {len(chosen)} streams.')
    print('Note: entries are not live-tested and may be region-blocked or offline.')

if __name__ == '__main__':
    main()
