"""Complete both records and verify automatic image reception in Chromium."""
import math
import os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

URL = os.getenv('TEST_URL', 'http://127.0.0.1:8000')
EXPECTED = '\n'.join(['NEW OS UPDATE DETECTED.', 'INITIALIZING UPDATE...',
                       'CHECKING UPDATE FILES...', 'FILES VERIFIED.', 'STARTING UPDATE...'])

def journey(page):
    page.clock.install()
    page.goto(URL)
    page.evaluate('''() => {
      const original = receiveImage;
      receiveImage = () => { window.receptionStartedAt = performance.now(); return original(); };
    }''')
    page.evaluate('document.fonts.load(\'26px "Unknown Signal Alien"\')')
    page.clock.run_for(55000)
    page.clock.pause_at(datetime.fromtimestamp(page.evaluate('Date.now()') / 1000, timezone.utc))
    page.locator('#access').click()
    page.wait_for_function('document.querySelector("#scene").naturalWidth > 0')
    page.clock.run_for(6000)
    assert page.locator('#signal-text').inner_text() == 'If you have received our signal, please respond.'
    for _ in range(3): page.locator('#next-image').click()
    page.clock.run_for(5000)
    assert page.locator('#record-text').inner_text() == 'Is there really no one left?'
    page.locator('#access-record').click()
    for index in range(3):
        page.wait_for_function('document.querySelector("#archive-scene").naturalWidth > 0')
        if index == 1:
            page.clock.run_for(1800)
            assert page.locator('#friend-text').inner_text() == 'NEW FRIEND'
        page.locator('#archive-return').click()
    # Language conversion and existing two-second pause are unchanged.
    page.clock.run_for(15000)
    assert page.evaluate('languageState') == 'complete'
    while page.evaluate('updateState') != 'complete': page.clock.run_for(50)
    assert page.locator('#os-update-text').inner_text() == EXPECTED

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width, height in [(1440, 900), (390, 844), (320, 568)]:
        page = browser.new_page(viewport={'width': width, 'height': height})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        journey(page)
        page.wait_for_function('document.querySelector("#received-image img").naturalWidth > 0')
        before = page.locator('#output').inner_html()
        elapsed = page.evaluate('performance.now() - receptionStartedAt')
        page.clock.run_for(math.ceil(1999 - elapsed))
        assert page.locator('#received-image').is_hidden()
        page.clock.run_for(1)
        assert page.locator('#received-image').is_visible()
        assert page.evaluate('receivedImageState') == 'revealing'
        frame = page.locator('.received-image-frame')
        progress = lambda: frame.evaluate('(el) => parseFloat(el.style.getPropertyValue("--received-progress")) || 0')
        assert progress() == 0
        page.clock.run_for(200)
        partial = progress()
        assert 0 < partial < 100
        page.clock.run_for(50)
        assert progress() == partial, 'the first advancing segment must pause'
        page.clock.run_for(3000)
        assert partial < progress() < 100
        page.screenshot(path=f'/workspace/work/reception-mid-{width}.png')
        page.clock.run_for(3250)
        assert page.evaluate('receivedImageState') == 'complete'
        assert progress() == 100
        image = page.locator('#received-image img')
        assert image.get_attribute('src') == 'images/scene-07.jpg'
        assert image.evaluate('(el) => Math.abs(el.width/el.height - el.naturalWidth/el.naturalHeight) < 0.01')
        assert page.locator('#received-image').bounding_box()['y'] >= page.locator('#os-update').bounding_box()['y'] + page.locator('#os-update').bounding_box()['height']
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.locator('#output').inner_html() == before
        assert page.locator('#os-update-text').inner_text() == EXPECTED
        assert page.locator('#access-record').is_enabled()
        page.clock.resume()
        page.wait_for_timeout(500)
        assert page.locator('.received-image-front').bounding_box()['y'] <= height + 1
        page.screenshot(path=f'/workspace/work/reception-complete-{width}.png')
        page.clock.pause_at(datetime.fromtimestamp(page.evaluate('Date.now()') / 1000, timezone.utc))
        page.locator('#access-record').click()
        for _ in range(3): page.locator('#archive-return').click()
        page.clock.run_for(15000)
        assert page.locator('#received-image').count() == 1
        assert page.evaluate('receivedImageState') == 'complete'
        assert progress() == 100
        assert not errors, errors
        print('PASS', width, 'full journey, 2s wait, stepped 6s reveal, pauses, aspect, scroll, preservation, once')
        page.close()
    for failure in ['missing', 'corrupt', 'stalled']:
        page = browser.new_page()
        pending = []
        if failure == 'missing': page.route('**/scene-07.jpg', lambda route: route.abort())
        elif failure == 'corrupt': page.route('**/scene-07.jpg', lambda route: route.fulfill(content_type='image/jpeg', body='bad image'))
        else: page.route('**/scene-07.jpg', lambda route: pending.append(route))
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        journey(page)
        page.clock.run_for(17000)
        assert page.evaluate('receivedImageState') == 'error'
        assert page.locator('.received-image-error').inner_text() == 'IMAGE UNAVAILABLE'
        assert page.locator('#os-update-text').inner_text() == EXPECTED
        page.locator('#access-record').click()
        assert page.locator('#archive').is_visible()
        assert not errors, errors
        for route in pending: route.abort()
        print('PASS', failure, 'safe image failure, preserved text, archive remains usable')
        page.close()
    browser.close()
