// Fails CI if the widget gets too big for customers' pages.
import { statSync } from 'node:fs';

const LIMIT = 25_000; // bytes, minified, uncompressed
const size = statSync('dist/widget.js').size;

console.log(`dist/widget.js: ${size} bytes (limit ${LIMIT})`);
if (size > LIMIT) {
  console.error('widget.js is over its size budget');
  process.exit(1);
}
