import math
import os
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
url=os.getenv('TEST_URL','http://127.0.0.1:8000')
fixture=(Path(__file__).resolve().parents[1] / 'images/scene-01.jpg').read_bytes()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(1440,900),(390,844),(320,568)]:
  if os.getenv('TEST_WIDTH') and width != int(os.environ['TEST_WIDTH']): continue
  page=b.new_page(viewport={'width':width,'height':height});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  if os.getenv('MOCK_IMAGES'):
   page.route('**/images/*.jpg',lambda r:r.fulfill(content_type='image/jpeg',body=fixture))
  page.clock.install();page.goto(url);page.evaluate('''() => { const original = showOSUpdate; showOSUpdate = () => { window.updateScheduledAt = performance.now(); return original(); }; }''');page.evaluate('document.fonts.load(\'26px "Unknown Signal Alien"\')')
  page.clock.run_for(55000)
  page.clock.pause_at(datetime.fromtimestamp(page.evaluate('Date.now()')/1000,timezone.utc))
  page.locator('#access').click();page.wait_for_function('document.querySelector("#scene").naturalWidth>0')
  page.clock.run_for(6000);assert page.locator('#signal-text').inner_text()=='If you have received our signal, please respond.'
  for _ in range(3):page.locator('#next-image').click()
  page.clock.run_for(5000);assert page.locator('#record-text').inner_text()=='Is there really no one left?'
  original=page.locator('#output').text_content();lines=original.split('\n')
  page.locator('#access-record').click()
  for index in range(3):
   page.wait_for_function('document.querySelector("#archive-scene").naturalWidth>0')
   assert page.locator('#archive-scene').evaluate('(e)=>Math.abs(e.width/e.height-e.naturalWidth/e.naturalHeight)<0.01')
   assert page.locator('#archive-status').inner_text()==f'ARCHIVE : 0{index+1} / 03'
   assert page.locator('#archive-scene').get_attribute('src')==f'images/scene-0{index+4}.jpg'
   if index==1:
    page.clock.run_for(499);assert page.locator('#friend-message').is_hidden()
    page.clock.run_for(1600);assert page.locator('#friend-text').inner_text()=='NEW FRIEND'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=f'/workspace/work/archive-{width}.png')
   else:assert page.locator('#friend-message').is_hidden()
   page.locator('#archive-return').click()
  assert page.locator('.terminal').is_visible()
  page.clock.run_for(999);assert page.locator('#output').text_content()==original
  assert page.evaluate('languageState')=='waiting'
  page.clock.run_for(1);assert page.evaluate('languageState')=='interpreting'
  page.clock.run_for(6000);assert 0<page.locator('.os-line.alien-text').count()<len([s for s in lines if s])
  page.clock.run_for(7000);assert page.evaluate('languageState')=='complete'
  rows=page.locator('.os-line').all_text_contents();assert rows==[s or '\u00a0' for s in lines]
  assert page.locator('.os-line.alien-text').count()==len([s for s in lines if s])
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=f'/workspace/work/os-{width}.png')
  # Inspect the exact boundary relative to the language-completion callback.
  elapsed=page.evaluate('performance.now()-window.updateScheduledAt')
  page.clock.run_for(math.ceil(1999-elapsed))
  assert page.locator('#os-update').is_hidden()
  assert page.locator('#os-update-text').text_content()==''
  page.clock.run_for(1)
  assert page.locator('#os-update').is_visible()
  page.clock.run_for(700)
  assert 0<len(page.locator('#os-update-text').text_content())<len('NEW OS UPDATE DETECTED.')
  before=page.locator('#output').inner_html()
  page.clock.run_for(15000)
  expected='NEW OS UPDATE DETECTED.\nINITIALIZING UPDATE...\nCHECKING UPDATE FILES...\nFILES VERIFIED.\nSTARTING UPDATE...'
  assert page.locator('#os-update-text').text_content()==expected
  assert page.evaluate('updateState')=='complete'
  assert page.locator('#output').inner_html()==before
  assert page.locator('#record-text').text_content()=='Is there really no one left?'
  assert page.locator('#access-record').is_enabled()
  assert page.locator('#os-update').evaluate('(e)=>getComputedStyle(e).fontFamily')==page.locator('.screen').first.evaluate('(e)=>getComputedStyle(e).fontFamily')
  assert page.locator('#os-update-cursor').evaluate('(e)=>getComputedStyle(e).animationName')=='blink'
  page.clock.resume()
  page.wait_for_timeout(500)
  page.clock.pause_at(datetime.fromtimestamp(page.evaluate('Date.now()')/1000,timezone.utc))
  # The automatic received image now follows this cursor and may scroll it up.
  assert page.locator('#os-update-cursor').is_visible()
  page.screenshot(path=f'/workspace/work/update-{width}.png')
  assert page.evaluate('languageState')=='complete' 
  assert not errors,errors
  print('PASS',width,'full journey, exact 2s, gradual English update, preserved OS/buttons, cursor, scroll, replay once')
  # Reopening an archive must not restart interpretation or change its result.
  rendered=page.locator('#output').inner_text()
  page.locator('#access-record').click()
  for _ in range(3):page.locator('#archive-return').click()
  page.clock.run_for(14000)
  assert page.evaluate('languageState')=='complete'
  assert page.locator('#output').inner_text()==rendered
  assert page.locator('#os-update-text').text_content()==expected
  assert page.locator('#os-update').count()==1
  page.close()
 for failure in ['image', 'font']:
  page=b.new_page()
  if failure=='image':
   page.route('**/images/*.jpg',lambda r:r.abort())
  else:
   page.route('**/*.woff2',lambda r:r.abort())
  page.clock.install();page.goto(url);page.evaluate('''() => { const original = showOSUpdate; showOSUpdate = () => { window.updateScheduledAt = performance.now(); return original(); }; }''');page.clock.run_for(55000)
  page.locator('#access').click()
  for _ in range(3):page.locator('#next-image').click()
  page.clock.run_for(6000)
  page.locator('#access-record').click()
  page.locator('#archive-return').click()
  if failure=='image':
   page.wait_for_function('document.querySelector("#archive-image-message").textContent==="IMAGE UNAVAILABLE"')
  page.clock.run_for(4000)
  assert page.locator('#friend-message').is_hidden()
  page.locator('#archive-return').click();page.locator('#archive-return').click()
  page.clock.run_for(15000)
  assert page.locator('.terminal').is_visible()
  assert page.locator('#access-record').is_enabled()
  assert page.evaluate('languageState')==('complete' if failure=='image' else 'idle')
  print('PASS',failure,'failure, no false friend message, navigation, safe OS state')
  page.close()
 b.close()
