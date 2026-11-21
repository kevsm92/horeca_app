// Run from the repository root: node --test tests/tables/reference-redesign-icons.test.cjs
// Tests the committed standalone HTML with no external services or dependencies.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');

test('mockup font emphasis and venue storefront SVG are present', () => {
  assert.match(html, /Development Progress Dashboard/);
  assert.match(html, /font-weight:83[0-9]/);
  assert.match(html, /<symbol id="i-store"/);
  assert.match(html, /<use href="#i-store"/);
});
test('all linked SVG icon symbols exist, and no third-party scripts or styles are loaded', () => {
  const symbols = new Set([...html.matchAll(/<symbol id="([^"]+)"/g)].map(x=>x[1]));
  const used = [...html.matchAll(/<use href="#([^"]+)"/g)].map(x=>x[1]);
  assert.ok(used.length >= 15);
  for (const name of used) assert.ok(symbols.has(name), 'undefined SVG symbol: '+name);
  assert.doesNotMatch(html, /<script[^>]+src=|<link[^>]+href=|@import|url\(\s*['"]?https?:/i);
});
const begin = html.indexOf('function renderSaveBadge(');
const finish = html.indexOf('\nfunction save(expected)',begin);
function fixture(message,warning) {
  assert.ok(begin >= 0 && finish > begin, 'save badge logic must be present in shipped HTML');
  const snippet = html.slice(begin,finish);
  const badge = {className:'',children:[],replaceChildren(...nodes){this.children=nodes;}};
  const document = {
    createElementNS(_,name) {
      return {name,attributes:{},setAttribute(k,v){this.attributes[k]=v;},append(child){this.child=child;}};
    },
    createTextNode(value){return {textContent:value};}
  };
  const sandbox = vm.createContext({document,$:()=>badge});
  new vm.Script(snippet+'\nrenderSaveBadge('+JSON.stringify(message)+','+Boolean(warning)+');').runInContext(sandbox,{timeout:1000});
  return badge;
}
test('saving keeps the success icon and accessible status text', () => {
  const badge=fixture('Saved in browser',false);
  assert.equal(badge.className,'saved');
  assert.equal(badge.children[0].attributes['aria-hidden'],'true');
  assert.equal(badge.children[0].child.attributes.href,'#i-check');
  assert.equal(badge.children[1].textContent,'Saved in browser');
});
test('storage failure keeps warning icon and message', () => {
  const badge=fixture('Storage unavailable',true);
  assert.equal(badge.className,'saved warn');
  assert.equal(badge.children[0].child.attributes.href,'#i-info');
  assert.equal(badge.children[1].textContent,'Storage unavailable');
});
test('existing keyboard, drag and per-venue storage handlers remain', () => {
  assert.match(html,/function onKey\(e\)/);
  assert.match(html,/function dragMove\(e\)/);
  assert.match(html,/function save\(expected\)/);
  assert.match(html,/horeca-floor-design-v2:/);
  assert.match(html,/physical=Object\.freeze/);
});
