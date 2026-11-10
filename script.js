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
  }
}

imageAdvance.addEventListener('click', advanceImage);
nextImage.addEventListener('click', advanceImage);

boot();
