import os
from playwright.sync_api import sync_playwright
from datetime import datetime,timezone
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width in [1440,390,320]:
  page=b.new_page(viewport={'width':width,'height':900});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.clock.install();page.goto(os.environ.get('TEST_URL', 'http://127.0.0.1:8000'))
  page.evaluate('document.fonts.load(\'26px "Unknown Signal Alien"\')')
  page.clock.run_for(55000)
  assert page.locator('#access-record').is_hidden()
  page.clock.pause_at(datetime.fromtimestamp(page.evaluate('Date.now()')/1000,timezone.utc))
  page.locator('#access').click()
  page.wait_for_function('document.querySelector("#scene").naturalWidth>0')
  page.clock.run_for(499);assert page.locator('#signal-message').is_hidden()
  page.clock.run_for(6000);assert page.locator('#signal-text').inner_text()=='If you have received our signal, please respond.'
  for _ in range(3):page.locator('#next-image').click()
  page.clock.run_for(1000)
  assert 0<len(page.locator('#record-text').inner_text())<27
  assert page.locator('#access-record').is_hidden()
  while page.locator('#record-text').inner_text()!='Is there really no one left?':page.clock.run_for(1)
  page.clock.run_for(699);assert page.locator('#access-record').is_hidden()
  page.clock.run_for(1);assert page.locator('#access-record').is_visible()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.locator('#access-record').click();assert page.locator('#archive').is_visible()
  assert page.locator('#archive-status').inner_text()=='ARCHIVE : 01 / 03'
  page.locator('#archive-return').click()
  page.locator('#archive-return').click()
  page.locator('#archive-return').click();assert page.locator('.terminal').is_visible()
  assert page.locator('#access-record').is_visible()
  assert not errors,errors
  print('PASS',width,'first message, return trigger, slow typing, 700ms, archive and return')
  page.close()
 for mode in ['failed', 'stalled']:
  page=b.new_page()
  pending=[]
  if mode == 'failed':
   page.route('**/*.woff2', lambda route: route.abort())
  else:
   page.route('**/*.woff2', lambda route: pending.append(route))
  page.clock.install()
  page.goto(os.environ.get('TEST_URL', 'http://127.0.0.1:8000'), wait_until='domcontentloaded')
  page.clock.run_for(55000)
  page.locator('#access').click()
  for _ in range(3): page.locator('#next-image').click()
  page.clock.run_for(6000)
  assert page.locator('#record-message').is_hidden()
  assert page.locator('#record-text').inner_text() == ''
  assert page.locator('#access-record').is_visible()
  assert page.evaluate('recordUnlocked')
  page.locator('#access-record').click()
  assert page.locator('#archive').is_visible()
  page.locator('#archive-return').click()
  page.locator('#archive-return').click()
  page.locator('#archive-return').click()
  assert page.locator('.terminal').is_visible()
  print('PASS font', mode, 'no English exposure, archive remains accessible')
  for route in pending: route.abort()
  page.close()
 b.close()
