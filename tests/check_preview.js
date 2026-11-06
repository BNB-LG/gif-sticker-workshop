// Offline interaction smoke test. This is a DOM stub, not a browser render test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const preview = process.argv[2] || path.join(__dirname, '../examples/qa/preview.html');
const html = fs.readFileSync(preview, 'utf8');
const source = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const ids = ['frame', 'seek', 'label', 'play', 'prev', 'next'];
const elements = Object.fromEntries(ids.map(id => [id, {value: 0, textContent: ''}]));
let callback;
let lastDelay;
vm.runInNewContext(source, {
  document: {
    getElementById: id => elements[id],
    querySelectorAll: () => Object.values(elements),
  },
  setTimeout: (fn, delay) => { callback = fn; lastDelay = delay; return 1; },
  clearTimeout: () => { callback = null; },
}, {timeout: 1000});
assert.match(elements.frame.src, /^data:image\/png;base64,/);
assert.match(elements.label.textContent, /1\/12/);
elements.next.onclick();
assert.match(elements.label.textContent, /2\/12/);
elements.prev.onclick();
elements.prev.onclick();
assert.match(elements.label.textContent, /12\/12/);
elements.seek.value = 3;
elements.seek.oninput();
assert.match(elements.label.textContent, /4\/12/);
elements.play.onclick();
assert.equal(lastDelay, 200);
assert.equal(typeof callback, 'function');
callback();
assert.match(elements.label.textContent, /5\/12/);
elements.play.onclick();
assert.equal(callback, null);
console.log('PASS: frame navigation, wrap, scrub, timed play and pause (DOM stub only)');
