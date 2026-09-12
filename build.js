#!/usr/bin/env node
// Netlify build step. Reads GA_MEASUREMENT_ID from the environment and copies
// landing/ and docs/ to dist/, substituting the G-PLACEHOLDER in any .html
// file with the real ID. Source files are left untouched so a real Measurement
// ID never lands in git.
//
// Set GA_MEASUREMENT_ID in Netlify → Site settings → Environment variables.
// Leave unset to ship with the placeholder (tracking disabled).

const fs = require('fs');
const path = require('path');

const id = process.env.GA_MEASUREMENT_ID || 'G-PLACEHOLDER';

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyDir(s, d);
    } else if (entry.name.endsWith('.html')) {
      const before = fs.readFileSync(s, 'utf8');
      const after = before.replace(/G-PLACEHOLDER/g, id);
      fs.writeFileSync(d, after);
    } else {
      fs.copyFileSync(s, d);
    }
  }
}

const dirs = ['landing', 'docs'];
let copied = 0;
for (const dir of dirs) {
  const src = path.join(__dirname, dir);
  const dst = path.join(__dirname, 'dist', dir);
  if (!fs.existsSync(src)) continue;
  copyDir(src, dst);
  copied++;
  console.log(`[build.js] ${dir} → dist/${dir}`);
}

console.log(
  `[build.js] done — ${copied} dir(s), GA_MEASUREMENT_ID=${
    id === 'G-PLACEHOLDER' ? 'unset (placeholder kept)' : id
  }`
);