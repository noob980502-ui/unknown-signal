"""Browser regression for the complete flower transmission and in-place decoding."""
import math
import os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

URL = os.getenv('TEST_URL', 'http://127.0.0.1:8000')
PARAGRAPHS = [
    ["This small organism converts hydrogen into oxygen.", "It is essential to the composition of this planet's atmosphere."],
    ["And this was called a flower."],
    ["This is a place where beauty and longing coexist.", "Could we have held hands, as you once did?"],
    ["We fear that it may all have ended before the very possibility of coexistence could be tested."],
    ["We miss you.", "We miss you, even though we have never known you."],
    ['.', '.', '.'],
    ["We hope someone has received this message."],
    ["We hope we are not alone in this universe."],
]

INSTRUMENT = '''() => {
  window.trace = {glyphs: [], os: []};
  const original = showFlowerMessage;
  showFlowerMessage = () => { trace.called = performance.now(); return original(); };
  const typeOS = typeFlowerOSLine;
  typeFlowerOSLine = async (el, text) => {
    const entry = {text, start: performance.now()}; trace.os.push(entry);
    await typeOS(el, text); entry.end = performance.now();
  };
  const decode = decodeFlowerMessage;
  decodeFlowerMessage = async (lines) => {
    trace.decodeStart = performance.now(); await decode(lines); trace.decodeEnd = performance.now();
  };
  const seen = new WeakSet();
  new MutationObserver((changes) => {
    for (const change of changes) {
      const node = change.target;
      if (node.matches('.flower-glyph:not(.pending)') && !seen.has(node)) {
        seen.add(node);
        trace.glyphs.push({time: performance.now(), line: [...document.querySelectorAll('.flower-line')].indexOf(node.closest('.flower-line'))});
      }
    }
  }).observe(document, {subtree: true, attributes: true, attributeFilter: ['class']});
}'''

def journey(page):
    page.clock.install()
    page.goto(URL)
    page.evaluate(INSTRUMENT)
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
    for i in range(3):
        page.wait_for_function('document.querySelector("#archive-scene").naturalWidth > 0')
        if i == 1:
            page.clock.run_for(1800)
            assert page.locator('#friend-text').inner_text() == 'NEW FRIEND'
        page.locator('#archive-return').click()
    for _ in range(100):
        page.clock.run_for(500)
        if page.evaluate('receivedImageState') == 'complete': break
        if page.evaluate('receivedImageState') == 'error': return 0
    assert page.evaluate('receivedImageState') == 'complete'
    return page.evaluate('performance.now() - trace.called')

def text_lines(page):
    return page.locator('.flower-line').evaluate_all('els => els.map(el => [...el.querySelectorAll(".flower-glyph")].map(g => g.firstChild.nodeValue).join(""))')

def positions(page):
    return page.locator('.flower-glyph').evaluate_all('els => { const root = document.querySelector("#flower-message").getBoundingClientRect(); return els.map(e => { const r=e.getBoundingClientRect(); return [r.x-root.x,r.y-root.y,r.width,r.height]; }); }')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width, height in [(1440,900),(390,844),(320,568)]:
        page = browser.new_page(viewport={'width':width,'height':height})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        elapsed = journey(page)
        old = page.locator('#output').inner_html()
        update = page.locator('#os-update-text').text_content()
        image = page.locator('#received-image').inner_html()
        page.clock.run_for(math.ceil(4999-elapsed))
        assert page.locator('#flower-sequence').count() == 0
        page.clock.run_for(1)
        assert page.evaluate('flowerState') == 'typing'
        page.clock.run_for(500)
        assert 0 < page.locator('.flower-glyph:not(.pending)').count() < page.locator('.flower-glyph').count()
        assert page.locator('.flower-glyph').first.evaluate('(e)=>getComputedStyle(e).fontFamily').startswith('"Unknown Signal Alien"')
        for _ in range(150):
            page.clock.run_for(500)
            if page.evaluate('flowerState') == 'waiting-integrity': break
        assert page.evaluate('flowerState') == 'waiting-integrity'
        assert text_lines(page) == [line for paragraph in PARAGRAPHS for line in paragraph]
        assert page.locator('.flower-paragraph').count() == len(PARAGRAPHS)
        assert page.locator('.flower-glyph.decoded').count() == 0
        trace = page.evaluate('trace')
        by_line = {}
        for glyph in trace['glyphs']: by_line.setdefault(glyph['line'], []).append(glyph['time'])
        offset = 0
        for paragraph in PARAGRAPHS:
            for i, line in enumerate(paragraph):
                if i:
                    gap = by_line[offset][0] - by_line[offset-1][-1]
                    if line == '.': assert 1499 <= gap <= 1501, gap
                    else: assert 499 <= gap <= 1081, gap
                elif offset:
                    gap = by_line[offset][0] - by_line[offset-1][-1]
                    assert 1499 <= gap <= 3081, gap
                offset += 1
        last_typed = trace['glyphs'][-1]['time']
        remaining = 2999 - page.evaluate('performance.now()') + last_typed
        page.clock.run_for(math.ceil(remaining))
        assert page.locator('#flower-sync').count() == 0
        page.clock.run_for(1)
        for _ in range(20):
            page.clock.run_for(500)
            if page.evaluate('flowerState') == 'waiting-decode': break
        assert page.evaluate('flowerState') == 'waiting-decode'
        assert page.locator('#flower-sync').inner_text() == 'SYNCHRONIZATION AND INTEGRITY CHECK...'
        assert page.locator('#flower-complete').inner_text() == 'COMPLETE.'
        trace = page.evaluate('trace')
        assert 2999 <= trace['os'][1]['start'] - trace['os'][0]['end'] <= 3001
        before = positions(page)
        now = page.evaluate('performance.now()')
        page.clock.run_for(math.ceil(trace['os'][1]['end']+999-now))
        assert page.locator('.flower-glyph.decoded').count() == 0
        page.clock.run_for(1)
        page.clock.run_for(8000)
        assert 0 < page.locator('.flower-glyph.decoded').count() < page.locator('.flower-glyph').count()
        assert text_lines(page) == [line for paragraph in PARAGRAPHS for line in paragraph]
        page.screenshot(path=f'/workspace/work/flower-partial-{width}.png')
        page.clock.run_for(10000)
        assert page.evaluate('flowerState') == 'complete'
        assert page.locator('.flower-glyph.decoded').count() == page.locator('.flower-glyph').count()
        after = positions(page)
        assert max(abs(a-b) for row1,row2 in zip(before,after) for a,b in zip(row1,row2)) < 0.2
        trace = page.evaluate('trace')
        assert 17999 <= trace['decodeEnd'] - trace['decodeStart'] <= 18001
        assert page.locator('#output').inner_html() == old
        assert page.locator('#os-update-text').text_content() == update
        assert page.locator('#received-image').inner_html() == image
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.locator('.flower-cursor').count() == 1
        assert page.locator('.flower-cursor').evaluate('(e)=>getComputedStyle(e).animationName') == 'blink'
        page.clock.resume(); page.wait_for_timeout(500)
        page.screenshot(path=f'/workspace/work/flower-complete-{width}.png')
        page.clock.pause_at(datetime.fromtimestamp(page.evaluate('Date.now()')/1000,timezone.utc))
        page.locator('#access-record').click()
        for _ in range(3): page.locator('#archive-return').click()
        page.clock.run_for(10000)
        assert page.locator('#flower-sequence').count() == 1
        assert page.evaluate('flowerState') == 'complete'
        assert not errors, errors
        print('PASS', width, 'full journey, 5s, exact paragraphs/dots, 3s/3s/1s, 18s in-place decoding, stable layout, preservation, once')
        page.close()
    for fault in ['font-failed', 'font-stalled', 'image-failed', 'reduced-motion']:
        page = browser.new_page(viewport={'width': 320, 'height': 568},
                                reduced_motion='reduce' if fault == 'reduced-motion' else 'no-preference')
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        if fault.startswith('font-'):
            page.add_init_script('''(() => {
              const original = FontFaceSet.prototype.load;
              FontFaceSet.prototype.load = function(font, text) {
                if (text && text.startsWith('This small organism')) {
                  return FAULT === 'font-failed' ? Promise.reject(new Error('test font failure')) : new Promise(() => {});
                }
                return original.call(this, font, text);
              };
            })();'''.replace('FAULT', repr(fault)))
        if fault == 'image-failed': page.route('**/scene-07.jpg', lambda route: route.abort())
        journey(page)
        page.clock.run_for(6000)
        if fault.startswith('font-'):
            assert page.evaluate('flowerState') == 'font-error'
            assert page.locator('#flower-sequence').count() == 0
        elif fault == 'image-failed':
            assert page.evaluate('flowerState') == 'idle'
            assert page.locator('#flower-sequence').count() == 0
        else:
            page.clock.run_for(90000)
            assert page.evaluate('flowerState') == 'complete'
            assert text_lines(page) == [line for paragraph in PARAGRAPHS for line in paragraph]
            assert page.locator('.flower-cursor').evaluate('(e)=>getComputedStyle(e).animationName') == 'none'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.locator('#access-record').is_enabled()
        assert not errors, errors
        print('PASS', fault, 'safe final sequence and existing controls')
        page.close()
    browser.close()
