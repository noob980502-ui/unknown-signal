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
}

access.addEventListener('click', () => {
  output.textContent += '\nSIGNAL ACCESS REQUESTED';
  status.textContent = 'SIGNAL ACCESS REQUESTED';
  access.hidden = true;
});

boot();
