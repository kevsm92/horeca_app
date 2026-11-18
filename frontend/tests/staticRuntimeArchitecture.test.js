import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// Architectural regression guard: Node/Vite may build/test the SPA but must not
// become a deployed application server or replace the Python HTTP API.
const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');

test('production build remains a static Vite client bundle', () => {
  assert.equal(packageJson.scripts.build, 'vite build');
  assert.equal(packageJson.type, 'module');
  assert.match(html, /<div\s+id=["']root["']\s*><\/div>/);
  assert.match(html, /<script\s+type=["']module["']\s+src=["']\/src\/main\.jsx["']\s*><\/script>/);
});

test('Node tooling is not configured as a production application server', () => {
  assert.match(packageJson.scripts.test, /^node --test\b/);
  assert.match(packageJson.scripts.dev, /^vite\b/);
  const scripts = Object.entries(packageJson.scripts);
  assert.ok(!scripts.some(([name]) => ['start', 'serve', 'server', 'api'].includes(name)));
  const runtimeDependencies = Object.keys(packageJson.dependencies ?? {});
  assert.deepEqual(runtimeDependencies.sort(), ['react', 'react-dom']);
  const forbidden = ['express', '@nestjs/core', 'next', 'remix', 'fastify', 'koa', 'socket.io'];
  for (const dependency of forbidden) {
    assert.equal(packageJson.dependencies?.[dependency], undefined);
    assert.equal(packageJson.devDependencies?.[dependency], undefined);
  }
});
