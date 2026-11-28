import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const app = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

test('fictional POS external dish images do not send a referrer', () => {
  const images = [...app.matchAll(/<img\b[^>]*>/g)].map(match => match[0]);
  assert.ok(images.length > 0, 'expected a fictional POS dish image');
  for (const image of images) {
    if (/https:\/\/images\.unsplash\.com/.test(image)) {
      assert.match(image, /\breferrerPolicy="no-referrer"/);
      assert.match(image, /\bloading="lazy"/);
      assert.match(image, /\balt=\{d\[0\]\}/);
    }
  }
});

test('the privacy attribute does not imply the external images are locally hosted', () => {
  assert.match(app, /https:\/\/images\.unsplash\.com/);
  assert.match(app, /Synthetic data only/);
});
