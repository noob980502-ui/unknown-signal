"""Run a real two-archive journey with current and mismatched cached assets.

Start a local server, then TEST_URL=http://127.0.0.1:8000 python3 tests/os_update_recovery.py
"""
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.getenv('TEST_URL', 'http://127.0.0.1:8000').rstrip('/') + '/'
EXPECTED = '\n'.join([
    'NEW OS UPDATE DETECTED.', 'INITIALIZING UPDATE...',
    'CHECKING UPDATE FILES...', 'FILES VERIFIED.', 'STARTING UPDATE...',
])
HTML = (ROOT / 'index.html').read_text()
OLD_SCRIPT = subprocess.check_output(
    ['git', 'show', '21a3940:script.js'], cwd=ROOT, text=True,
)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width, height in [(1440, 900), (390, 844)]:
        for scenario in ['current', 'old-html', 'missing-children', 'cached-old-script']:
            page = browser.new_page(viewport={'width': width, 'height': height})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
            requests = []
            page.on('request', lambda req: requests.append(req.url))
            if scenario == 'old-html':
                html = re.sub(r'    <pre id="os-update".*?</pre>\n', '', HTML)
                # This older HTML used unversioned assets.
                html = html.replace('?v=received-image-1', '')
                page.route(URL, lambda route: route.fulfill(content_type='text/html', body=html))
            elif scenario == 'missing-children':
                html = re.sub(r'(<pre id="os-update"[^>]*>).*?(</pre>)', r'\1\2', HTML)
                page.route(URL, lambda route: route.fulfill(content_type='text/html', body=html))
            elif scenario == 'cached-old-script':
                # Only the old, unversioned URL is stale. Current HTML must
                # request a different URL rather than run this pre-PR8 code.
                page.route('**/script.js', lambda route: route.fulfill(content_type='text/javascript', body=OLD_SCRIPT))

            # Python's static server has no favicon; it is unrelated to the app.
            page.route('**/favicon.ico', lambda route: route.fulfill(status=204))
            page.clock.install()
            page.goto(URL)
            page.evaluate('document.fonts.load(\'26px "Unknown Signal Alien"\')')
            page.clock.run_for(55000)
            page.clock.pause_at(datetime.fromtimestamp(page.evaluate('Date.now()') / 1000, timezone.utc))
            page.locator('#access').click()
            page.wait_for_function('document.querySelector("#scene").naturalWidth > 0')
            page.clock.run_for(6000)
            assert page.locator('#signal-text').inner_text() == 'If you have received our signal, please respond.'
            for _ in range(3):
                page.locator('#next-image').click()
            page.clock.run_for(5000)
            assert page.locator('#record-text').inner_text() == 'Is there really no one left?'
            page.locator('#access-record').click()
            page.locator('#archive-return').click()
            page.wait_for_function('document.querySelector("#archive-scene").naturalWidth > 0')
            page.clock.run_for(2000)
            assert page.locator('#friend-text').inner_text() == 'NEW FRIEND'
            page.locator('#archive-return').click()
            page.locator('#archive-return').click()
            page.clock.run_for(14000)
            assert page.evaluate('languageState') == 'complete'
            translated = page.locator('#output').inner_html()
            page.clock.run_for(15000)
            assert page.evaluate('updateState') == 'complete'
            assert page.locator('#os-update').is_visible()
            assert page.locator('#os-update-text').inner_text() == EXPECTED
            assert page.locator('#os-update').evaluate('(el) => getComputedStyle(el).display') != 'none'
            assert page.locator('#output').inner_html() == translated
            assert page.locator('#record-text').inner_text() == 'Is there really no one left?'
            assert page.locator('#access-record').is_visible()
            assert page.locator('#access-record').is_enabled()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            if scenario == 'cached-old-script':
                assert any('script.js?v=received-image-1' in url for url in requests)
                assert not any(url.endswith('/script.js') for url in requests)
            # Replay cannot duplicate the region or its message chain.
            page.locator('#access-record').click()
            for _ in range(3):
                page.locator('#archive-return').click()
            page.clock.run_for(20000)
            assert page.locator('#os-update').count() == 1
            assert page.locator('#os-update-text').inner_text() == EXPECTED
            assert not errors, errors
            print('PASS', width, scenario, 'both archives -> conversion -> five visible English lines; no console errors')
            page.close()
    browser.close()
