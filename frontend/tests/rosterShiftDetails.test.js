import test from 'node:test';
import assert from 'node:assert/strict';
import {rosterShiftKey, rosterShiftDescription} from '../src/rosterShiftDetails.js';
test('shift identity remains stable for keyboard details',()=>{assert.equal(rosterShiftKey('sofia','2026-11-23'),'sofia:2026-11-23');assert.throws(()=>rosterShiftKey('bad id','2026-11-23'),TypeError);});
test('shift details explicitly distinguish scheduled from attendance',()=>{const text=rosterShiftDescription({name:'Sofia',role:'Floor lead'},{day:'Mon',date:'23 Nov'},{time:'11:00–19:00'});assert.match(text,/Scheduled only; actual attendance unknown/);assert.match(text,/Fictional data/);});
test('unknown shift never fabricates details',()=>{assert.throws(()=>rosterShiftDescription({name:'Sofia'},{day:'Mon'},null),TypeError);});
