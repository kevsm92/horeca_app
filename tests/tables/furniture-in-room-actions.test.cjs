'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
const js=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
if(!js)throw new Error('missing floor plan script');
new Function(js);
const names=['placeAt','approvePlacement','removeFromLayout','move'];
const code=names.map(name=>{const start=js.indexOf('function '+name+'(');assert.ok(start>=0,name);const end=js.indexOf('\nfunction ',start+10);return js.slice(start,end<0?js.length:end)}).join('\n');
function fixture(){
 const ctx={physical:[{id:'T1'},{id:'T2'}],positions:{T1:{x:20,y:20}},pendingPlacement:null,selected:'T1',revision:2,actions:[],fail:false};
 ctx.clone=x=>JSON.parse(JSON.stringify(x));ctx.render=()=>{};ctx.announce=()=>{};ctx.confirm=()=>true;
 ctx.save=(rev,action)=>{if(ctx.fail||rev!==ctx.revision)return false;ctx.revision++;ctx.actions.push(action);return true};
 const api=new Function('ctx','with(ctx){'+code+';return {placeAt,approvePlacement,removeFromLayout,move}}')(ctx);
 return {ctx,api};
}
test('preview requires green approval before persistence',()=>{const {ctx,api}=fixture();assert.equal(api.placeAt('T2',60,70),true);assert.equal(ctx.revision,2);assert.equal(ctx.positions.T2,undefined);assert.equal(api.move('T2',64,75),true);assert.equal(ctx.revision,2);assert.equal(api.approvePlacement('T2'),true);assert.deepEqual(ctx.positions.T2,{x:64,y:75});assert.deepEqual(ctx.actions,['Placed T2']);});
test('red action removes confirmed layout item',()=>{const {ctx,api}=fixture();assert.equal(api.removeFromLayout('T1',true),true);assert.equal(ctx.positions.T1,undefined);assert.deepEqual(ctx.actions,['Removed T1']);});
test('red action discards pending placement without saving',()=>{const {ctx,api}=fixture();api.placeAt('T2',50,50);assert.equal(api.removeFromLayout('T2',true),true);assert.equal(ctx.pendingPlacement,null);assert.equal(ctx.revision,2);});
test('failed save preserves preview for retry',()=>{const {ctx,api}=fixture();api.placeAt('T2',50,50);ctx.fail=true;assert.equal(api.approvePlacement('T2'),false);assert.equal(ctx.pendingPlacement.id,'T2');assert.equal(ctx.positions.T2,undefined);});
test('duplicate preview and unrelated approval are rejected',()=>{const {ctx,api}=fixture();api.placeAt('T2',50,50);assert.equal(api.placeAt('T2',51,51),false);assert.equal(api.approvePlacement('T1'),false);assert.equal(ctx.pendingPlacement.x,50);});
test('accessible controls are separate from table button and sidebar remains',()=>{assert.match(html,/toolbar\.dataset\.placementToolbar=t\.id/);assert.ok(html.includes("'Remove table '+id+' from the layout"));assert.match(html,/placement-action\.approve/);assert.match(html,/placement-action\.remove/);assert.match(html,/button\.textContent=placed\?'Already placed':'Place on layout'/);});
