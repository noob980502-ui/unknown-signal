// Each entry controls one line: text, character delay range, pause after the line.
const bootLines = [
  { text: '>> INITIALIZING INTERFACE...', speed: [15, 48], pause: 240 },
  { text: '>> CHECKING SYSTEM... OK', speed: [8, 28], pause: 160 },
  { text: '>> LOADING MEMORY... OK', speed: [8, 28], pause: 360 },
  { text: '', pause: 100 },
  { text: '[01] MEMORY ACCESS........ OK', speed: [8, 25], pause: 180 },
  { text: '[02] IMAGE BUFFER......... OK', speed: [8, 25], pause: 210 },
  { text: '[03] TEXT DECODER..........', speed: [35, 110], pause: 1100 },
  { text: '', pause: 150 },
  { text: 'UNKNOWN CHARACTER SET', speed: [80, 180], pause: 950 },
  { text: 'RETRYING...', speed: [70, 140], pause: 1100 },
  { text: 'RETRYING...', speed: [100, 200], pause: 1400 },
  { text: 'FAILED', speed: [100, 230], pause: 850 },
  { text: '', pause: 150 },
  { text: '[04] SIGNAL ROUTE......... OK', speed: [8, 28], pause: 450 },
  { text: '', pause: 100 },
  { text: '>> INCOMING SIGNAL DETECTED', speed: [25, 65], pause: 600 },
  { text: '>> AWAITING INPUT', speed: [35, 80], pause: 0 },
];

const output = document.querySelector('#output');
const access = document.querySelector('#access');
const status = document.querySelector('#status');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
const randomBetween = (min, max) => min + Math.random() * (max - min);

async function boot() {
  // The first 1–2 seconds contain only the cursor.
  await wait(randomBetween(1000, 2000));

  for (const [index, line] of bootLines.entries()) {
    if (reducedMotion) {
      // Keep the sequence but avoid character-by-character animation.
      output.textContent += line.text;
    } else {
      for (const [position, character] of [...line.text].entries()) {
        await wait(randomBetween(...line.speed));
        // The decoder stalls briefly in the middle of interpreting the text.
        if (line.text === 'UNKNOWN CHARACTER SET' && position === 8) {
          await wait(800);
        }
        output.textContent += character;
      }
    }
    await wait(line.pause);
    if (index < bootLines.length - 1) output.textContent += '\n';
  }

  status.textContent = output.textContent + '_';
  access.hidden = false;
  document.querySelector('#alien-message').hidden = false;
}

const terminal = document.querySelector('.terminal');
const viewer = document.querySelector('#viewer');
const imageMessage = document.querySelector('#image-message');
const bufferStatus = document.querySelector('#buffer-status');
const imageAdvance = document.querySelector('#image-advance');
const nextImage = document.querySelector('#next-image');
const recordMessage = document.querySelector('#record-message');
const recordText = document.querySelector('#record-text');
const accessRecord = document.querySelector('#access-record');
const archive = document.querySelector('#archive');
const archiveReturn = document.querySelector('#archive-return');
let recordUnlocked = false;
let recordVersion = 0;

async function revealSecondRecord() {
  const version = ++recordVersion;
  const sentence = 'Is there really no one left?';
  let fontLoaded = false;
  try {
    // Do not let a failed or stalled font request block archive access forever.
    const fonts = await Promise.race([
      document.fonts.load('26px "Unknown Signal Alien"', sentence),
      wait(5000).then(() => []),
    ]);
    fontLoaded = fonts.length > 0 && fonts.every((font) => font.status === 'loaded');
  } catch {
    // Keep the untranslated sentence hidden, but allow the archive to open.
  }
  const isCurrent = () => version === recordVersion && !terminal.hidden;
  if (!isCurrent()) return;
  recordMessage.hidden = !fontLoaded;
  recordText.textContent = '';
  if (!fontLoaded) {
    status.textContent = 'Alien font unavailable. Record access is available.';
  } else if (reducedMotion) {
    recordText.textContent = sentence;
  } else {
    for (const character of sentence) {
      await wait(randomBetween(65, 120));
      if (!isCurrent()) return;
      recordText.textContent += character;
    }
  }
  await wait(700);
  if (isCurrent()) {
    recordUnlocked = true;
    accessRecord.hidden = false;
    accessRecord.scrollIntoView({ block: 'nearest' });
  }
}

const scenes = ['images/scene-01.jpg', 'images/scene-02.jpg', 'images/scene-03.jpg'];
let sceneIndex = 0;
let accessRequested = false;
const signalMessage = document.querySelector('#signal-message');
const signalText = document.querySelector('#signal-text');
const signalSentence = 'If you have received our signal, please respond.';
let messageVersion = 0;

async function typeSignalMessage(version) {
  // Wait for both the image's 500ms display period and the actual alien font.
  // Unlike the test sentence, this message must never appear in plain English.
  try {
    const [, fonts] = await Promise.all([
      wait(500),
      document.fonts.load('26px "Unknown Signal Alien"', signalSentence),
    ]);
    if (!fonts.length || !fonts.every((font) => font.status === 'loaded')) return;
  } catch {
    return;
  }
  const isCurrent = () => version === messageVersion && !viewer.hidden && sceneIndex === 0;
  if (!isCurrent()) return;
  signalMessage.hidden = false;
  if (reducedMotion) {
    signalText.textContent = signalSentence;
    return;
  }
  for (const character of signalSentence) {
    await wait(randomBetween(35, 80));
    if (!isCurrent()) return;
    signalText.textContent += character;
  }
}

function showScene() {
  const version = ++messageVersion;
  signalMessage.hidden = true;
  signalText.textContent = '';
  imageMessage.hidden = false;
  imageMessage.textContent = 'LOADING IMAGE...';
  bufferStatus.textContent = `IMAGE BUFFER : ${String(sceneIndex + 1).padStart(2, '0')} / 03`;
  const lastScene = sceneIndex === scenes.length - 1;
  nextImage.textContent = lastScene ? 'RETURN' : 'NEXT';
  imageAdvance.setAttribute('aria-label', lastScene ? 'Return to interface' : 'Next image');

  // Replace the image node so a late response from the previous image cannot
  // overwrite the current image's loading/error state.
  const image = document.createElement('img');
  image.id = 'scene';
  image.alt = `Signal image ${sceneIndex + 1}`;
  image.hidden = true;
  image.onload = () => {
    if (document.querySelector('#scene') !== image) return;
    image.hidden = false;
    imageMessage.hidden = true;
    if (sceneIndex === 0) typeSignalMessage(version);
  };
  image.onerror = () => {
    if (document.querySelector('#scene') !== image) return;
    image.hidden = true;
    imageMessage.textContent = 'IMAGE UNAVAILABLE';
    imageMessage.hidden = false;
  };
  document.querySelector('#scene').replaceWith(image);
  image.src = scenes[sceneIndex];
}

access.addEventListener('click', () => {
  // Cancel a partially typed second-record prompt while replaying record one.
  recordVersion += 1;
  if (accessRecord.hidden) {
    recordMessage.hidden = true;
    recordText.textContent = '';
    recordUnlocked = false;
  }
  if (!accessRequested) {
    output.textContent += '\nSIGNAL ACCESS REQUESTED';
    status.textContent = 'SIGNAL ACCESS REQUESTED';
    accessRequested = true;
  }
  sceneIndex = 0;
  terminal.hidden = true;
  viewer.hidden = false;
  showScene();
  nextImage.focus();
});

function advanceImage() {
  if (sceneIndex < scenes.length - 1) {
    sceneIndex += 1;
    showScene();
  } else {
    viewer.hidden = true;
    terminal.hidden = false;
    access.focus();
    if (!recordUnlocked) revealSecondRecord();
  }
}

imageAdvance.addEventListener('click', advanceImage);
nextImage.addEventListener('click', advanceImage);

boot();

// The second archive uses the same layout and controls as the first record.
const archiveScenes = ['images/scene-04.jpg', 'images/scene-05.jpg', 'images/scene-06.jpg'];
const archiveImageAdvance = document.querySelector('#archive-image-advance');
const archiveImageMessage = document.querySelector('#archive-image-message');
const archiveStatus = document.querySelector('#archive-status');
const friendMessage = document.querySelector('#friend-message');
const friendText = document.querySelector('#friend-text');
let archiveIndex = 0;
let archiveVersion = 0;
let languageState = 'idle';
let archiveFontReady;

async function loadArchiveFont() {
  try {
    const fonts = await Promise.race([
      document.fonts.load('12px "Unknown Signal Alien"'),
      wait(5000).then(() => []),
    ]);
    return fonts.length > 0 && fonts.every((font) => font.status === 'loaded');
  } catch {
    return false;
  }
}

async function typeFriend(version) {
  const [, fontReady] = await Promise.all([wait(500), archiveFontReady]);
  const isCurrent = () => version === archiveVersion && !archive.hidden && archiveIndex === 1;
  if (!fontReady || !isCurrent()) return;
  friendMessage.hidden = false;
  const sentence = 'NEW FRIEND';
  if (reducedMotion) {
    friendText.textContent = sentence;
    return;
  }
  for (const character of sentence) {
    await wait(randomBetween(35, 80));
    if (!isCurrent()) return;
    friendText.textContent += character;
  }
}

function showArchiveScene() {
  const version = ++archiveVersion;
  friendMessage.hidden = true;
  friendText.textContent = '';
  archiveImageMessage.hidden = false;
  archiveImageMessage.textContent = 'LOADING IMAGE...';
  archiveStatus.textContent = `ARCHIVE : ${String(archiveIndex + 1).padStart(2, '0')} / 03`;
  const last = archiveIndex === archiveScenes.length - 1;
  archiveReturn.textContent = last ? 'RETURN' : 'NEXT';
  archiveImageAdvance.setAttribute('aria-label', last ? 'Return to interface' : 'Next archive image');
  const image = document.createElement('img');
  image.id = 'archive-scene';
  image.className = 'scene-image';
  image.alt = ['Abandoned indoor swimming pool', 'Smiling golden retriever',
    'Golden retriever smelling grass in an abandoned playground'][archiveIndex];
  image.hidden = true;
  image.onload = () => {
    if (version !== archiveVersion || archive.hidden) return;
    image.hidden = false;
    archiveImageMessage.hidden = true;
    if (archiveIndex === 1) typeFriend(version);
  };
  image.onerror = () => {
    if (version !== archiveVersion || archive.hidden) return;
    archiveImageMessage.textContent = 'IMAGE UNAVAILABLE';
  };
  document.querySelector('#archive-scene').replaceWith(image);
  image.src = archiveScenes[archiveIndex];
}

accessRecord.addEventListener('click', () => {
  terminal.hidden = true;
  archive.hidden = false;
  archiveIndex = 0;
  archiveFontReady = loadArchiveFont();
  showArchiveScene();
  archiveReturn.focus();
});

function advanceArchive() {
  if (archiveIndex < archiveScenes.length - 1) {
    archiveIndex += 1;
    showArchiveScene();
    return;
  }
  archiveVersion += 1;
  friendMessage.hidden = true;
  friendText.textContent = '';
  archive.hidden = true;
  terminal.hidden = false;
  accessRecord.focus();
  if (languageState === 'idle') {
    terminal.scrollIntoView({ block: 'start' });
    interpretSystemLanguage();
  }
}
archiveImageAdvance.addEventListener('click', advanceArchive);
archiveReturn.addEventListener('click', advanceArchive);

async function interpretSystemLanguage() {
  languageState = 'waiting';
  // Prevent re-entry during the one-second pause and interpretation.
  access.disabled = true;
  accessRecord.disabled = true;
  await wait(1000);
  if (!await archiveFontReady) {
    // No Latin fallback: leave the existing OS intact and allow a later retry.
    languageState = 'idle';
    access.disabled = false;
    accessRecord.disabled = false;
    return;
  }
  languageState = 'interpreting';
  const lines = output.textContent.split('\n');
  const rows = lines.map((line) => {
    const row = document.createElement('span');
    row.className = 'os-line';
    row.textContent = line || '\u00a0';
    return row;
  });
  output.replaceChildren(...rows);
  // Freeze row heights before deleting letters, retaining all original positions.
  rows.forEach((row) => { row.style.minHeight = `${row.getBoundingClientRect().height}px`; });
  const nonempty = lines.filter(Boolean).length;
  const lineDuration = 12000 / nonempty;
  for (const [index, line] of lines.entries()) {
    if (!line) continue;
    const row = rows[index];
    if (!reducedMotion) {
      const characterDelay = lineDuration / (line.length * 2);
      for (let length = line.length - 1; length >= 0; length -= 1) {
        row.textContent = line.slice(0, length) || '\u00a0';
        await wait(characterDelay);
      }
      row.classList.add('alien-text');
      for (let length = 1; length <= line.length; length += 1) {
        row.textContent = line.slice(0, length);
        await wait(characterDelay);
      }
    } else {
      row.classList.add('alien-text');
      await wait(lineDuration);
    }
  }
  languageState = 'complete';
  status.textContent = 'System language interpretation complete.';
  access.disabled = false;
  accessRecord.disabled = false;
  accessRecord.focus({ preventScroll: true });
  showOSUpdate();
}

let updateStarted = false;
let updateState = 'idle';
let updateScreen;
let updateText;
let updateCursor;

function ensureUpdateScreen() {
  // GitHub Pages/browser caches can serve older HTML with the newer script.
  // Resolve the region when it is needed, repairing only missing update nodes.
  updateScreen = document.querySelector('#os-update');
  if (!updateScreen) {
    updateScreen = document.createElement('pre');
    updateScreen.id = 'os-update';
    updateScreen.className = 'screen os-update';
    updateScreen.hidden = true;
    updateScreen.setAttribute('aria-hidden', 'true');
    terminal.append(updateScreen);
  }
  updateText = updateScreen.querySelector('#os-update-text');
  if (!updateText) {
    updateText = document.createElement('span');
    updateText.id = 'os-update-text';
    updateScreen.prepend(updateText);
  }
  updateCursor = updateScreen.querySelector('#os-update-cursor');
  if (!updateCursor) {
    updateCursor = document.createElement('span');
    updateCursor.id = 'os-update-cursor';
    updateCursor.className = 'cursor';
    updateCursor.textContent = '_';
    updateScreen.append(updateCursor);
  }
}
const updateLines = [
  { text: 'NEW OS UPDATE DETECTED.', pause: 450 },
  { text: 'INITIALIZING UPDATE...', pause: 550 },
  { text: 'CHECKING UPDATE FILES...', pause: 1100 },
  { text: 'FILES VERIFIED.', pause: 500 },
  { text: 'STARTING UPDATE...', pause: 0 },
];

let lastUpdateScroll = -Infinity;
function followUpdateCursor(force = false) {
  if (terminal.hidden) return;
  const bounds = updateCursor.getBoundingClientRect();
  if ((bounds.bottom > window.innerHeight || bounds.top < 0)
      && (force || performance.now() - lastUpdateScroll > 200)) {
    updateCursor.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'nearest' });
    lastUpdateScroll = performance.now();
  }
}

async function showOSUpdate() {
  // Claim this sequence before scheduling anything: archive replays cannot
  // create another timer chain or change the already translated diagnostics.
  if (updateStarted) return;
  updateStarted = true;
  updateState = 'waiting';
  await wait(2000);
  ensureUpdateScreen();
  updateState = 'typing';
  updateScreen.hidden = false;
  for (const [index, line] of updateLines.entries()) {
    if (index > 0) updateText.textContent += '\n';
    for (const character of line.text) {
      await wait(randomBetween(35, 80));
      updateText.textContent += character;
      followUpdateCursor();
    }
    await wait(line.pause);
  }
  updateState = 'complete';
  status.textContent = updateText.textContent;
  followUpdateCursor(true);
  receiveImage();
}

let receivedImageState = 'idle';
let receivedImageStarted = false;

function loadReceivedImage(image) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (loaded) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      image.onload = null;
      image.onerror = null;
      resolve(loaded);
    };
    // A missing, damaged or stalled image must not interrupt the terminal.
    const timeout = setTimeout(() => finish(false), 15000);
    image.onload = () => finish(true);
    image.onerror = () => finish(false);
    image.src = 'images/scene-07.jpg';
  });
}

async function receiveImage() {
  if (receivedImageStarted) return;
  receivedImageStarted = true;
  receivedImageState = 'waiting';
  // Build this below the update, including when older HTML was repaired.
  const section = document.createElement('figure');
  section.className = 'received-image';
  section.id = 'received-image';
  section.hidden = true;
  const frame = document.createElement('div');
  frame.className = 'received-image-frame';
  const image = document.createElement('img');
  image.alt = 'Received signal image';
  const front = document.createElement('span');
  front.className = 'received-image-front';
  front.setAttribute('aria-hidden', 'true');
  frame.append(image, front);
  section.append(frame);
  updateScreen.after(section);
  // Fetch while the screen waits, but do not show any image before two seconds.
  const loaded = loadReceivedImage(image);
  await wait(2000);
  receivedImageState = 'loading';
  if (!await loaded) {
    receivedImageState = 'error';
    frame.hidden = true;
    const error = document.createElement('p');
    error.className = 'received-image-error';
    error.textContent = 'IMAGE UNAVAILABLE';
    section.append(error);
    section.hidden = false;
    return;
  }
  section.hidden = false;
  receivedImageState = 'revealing';
  function reveal(percent) {
    frame.style.setProperty('--received-progress', `${percent}%`);
    if (!terminal.hidden) {
      const bounds = front.getBoundingClientRect();
      if (bounds.bottom > innerHeight - 24 || bounds.top < 0) {
        front.scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'nearest' });
      }
    }
  }
  if (reducedMotion) {
    reveal(100);
  } else {
    // Each short segment advances, then holds. Durations total exactly six
    // seconds, with jitter in both advance distance and pause length.
    const segments = 18;
    for (let step = 0; step < segments; step += 1) {
      const advancing = randomBetween(90, 180);
      await wait(advancing);
      reveal(Math.min(98, ((step + randomBetween(0.5, 1)) / segments) * 100));
      await wait(6000 / segments - advancing);
    }
    reveal(100);
  }
  receivedImageState = 'complete';
  status.textContent = 'Image reception complete.';
}
